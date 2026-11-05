"""Offline citation-neighbor selection, provenance, identity and stop regressions."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import atlas
import neighbors
import supplement


TITLE = 'Predicting odor intensity of aroma molecules'


def paper(doi, title=TITLE, **more):
    return {'DOI': doi, 'title': [title], 'type': 'journal-article',
            'published': {'date-parts': [[2020, 1, 2]]},
            'abstract': 'Aroma molecules were assessed for odor intensity.', **more}


class Response:
    def __init__(self, doi='', status=200, message=None, payload=None, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self.url = neighbors.ENDPOINT + doi
        self.payload = payload if payload is not None else {'status': 'ok', 'message': message or paper(doi)}
        self.text = json.dumps(self.payload)

    def json(self):
        return self.payload


class FixtureClient:
    def __init__(self, responses, maximum=80):
        self.responses = list(responses)
        self.maximum = maximum
        self.count = 0
        self.asked = []

    def available(self):
        return self.count < self.maximum

    def get(self, doi):
        self.count += 1
        self.asked.append(doi)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class NeighborIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = atlas.DB
        atlas.DB = pathlib.Path(self.tmp.name)/'atlas.sqlite'
        neighbors.init()
        supplement.ingest([paper('10.1234/source'), paper('10.1234/second')], 'core-test')

    def tearDown(self):
        atlas.DB = self.old_db
        self.tmp.cleanup()

    def ref(self, doi, title=TITLE, source='doi:10.1234/source', provider='Crossref', target_id=None):
        c = atlas.connect()
        c.execute('INSERT INTO raw_refs VALUES(?,?,?,?,?)',
                  (source, provider, target_id or doi, doi, title))
        c.commit()
        c.close()

    def select(self):
        c = atlas.connect()
        candidates = neighbors.select_candidates(c)
        c.close()
        return candidates

    def execute(self, responses, **kwargs):
        client = FixtureClient(responses, kwargs.pop('maximum', 80))
        with patch.object(neighbors.time, 'sleep'), patch.object(supplement, 'log'):
            result = neighbors.run(client, **kwargs)
        return client, result

    def test_selects_only_unresolved_actual_core_references_and_prioritizes_title(self):
        self.ref('10.1234/title')
        self.ref('10.1234/repeated', 'Statistical methods')
        self.ref('10.1234/repeated', '', source='doi:10.1234/second')
        self.ref('10.1234/one', 'General methods')
        self.ref('not-a-doi')
        self.ref('10.1234/source')
        self.ref('10.1234/known-rejected')
        supplement.ingest([paper('10.1234/known-rejected', 'Aromatic polymer drug scaffolds',
                                 abstract='Unrelated polymer synthesis.')], 'negative')
        c = atlas.connect()
        c.execute("UPDATE papers SET tracks='[\"pharmacology\"]' WHERE doi='10.1234/second'")
        c.commit()
        c.close()
        self.assertEqual([x['doi'] for x in self.select()], ['10.1234/title'])
        c = atlas.connect()
        c.execute("UPDATE papers SET tracks='[\"aroma\"]' WHERE doi='10.1234/second'")
        c.commit()
        c.close()
        self.assertEqual([x['doi'] for x in self.select()], ['10.1234/title', '10.1234/repeated'])

    def test_repeated_providers_do_not_count_as_distinct_citing_papers(self):
        self.ref('10.1234/duplicate', 'Statistics')
        self.ref('10.1234/duplicate', 'Statistics', provider='MED', target_id='999')
        self.assertEqual(self.select(), [])

    def test_rejected_source_cannot_nominate_references(self):
        self.ref('10.1234/target')
        c = atlas.connect()
        c.execute("UPDATE papers SET accepted=0 WHERE doi='10.1234/source'")
        c.commit()
        c.close()
        self.assertEqual(self.select(), [])

    def test_request_race_reuses_exact_existing_enriched_identity(self):
        self.ref('10.1234/target')
        client = FixtureClient([Response('10.1234/target')])
        original_get = client.get

        def get(doi):
            atlas.ingest([{'id': '1234', 'source': 'MED', 'pmid': '1234', 'doi': doi,
                           'title': TITLE, 'abstractText': 'Enriched aroma molecule intensity abstract',
                           'pubYear': '2020'}], 'identity-race-test')
            return original_get(doi)

        client.get = get
        with patch.object(supplement, 'log'):
            report = neighbors.run(client)
        self.assertEqual(report['totals']['accepted_new'], 0)
        self.assertEqual(report['totals']['reused'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT id,source,abstract FROM papers WHERE doi='10.1234/target'").fetchall(),
                         [('pmid:1234', 'MED', 'Enriched aroma molecule intensity abstract')])
        self.assertEqual(c.execute("SELECT paper FROM citation_neighbor_checkpoint WHERE doi='10.1234/target'").fetchone(), ('pmid:1234',))
        c.close()

    def test_exact_metadata_raw_response_origins_and_real_edges_retained(self):
        self.ref('10.1234/target', provider='MED', target_id='pmid-target')
        self.ref('10.1234/target', source='doi:10.1234/second')
        message = paper('https://doi.org/10.1234/TARGET', reference=[{'DOI': '10.1234/deposited'}])
        client, result = self.execute([Response('10.1234/target', message=message)])
        self.assertEqual(client.asked, ['10.1234/target'])
        self.assertEqual(result['totals']['accepted_new'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT doi FROM papers WHERE id='doi:10.1234/target'").fetchone(), ('10.1234/target',))
        origins = c.execute('SELECT citing_paper,citing_doi,target_source,citing_queries FROM citation_neighbor_origins ORDER BY citing_paper').fetchall()
        self.assertEqual(len(origins), 2)
        self.assertTrue(all('crossref:core-test' in json.loads(row[3]) for row in origins))
        audit = c.execute('SELECT request_url,response_body,screening,ingestion FROM citation_neighbor_attempts').fetchone()
        self.assertIn('10.1234%2Ftarget', audit[0])
        self.assertEqual(json.loads(audit[1])['message']['DOI'], message['DOI'])
        self.assertTrue(json.loads(audit[2])['accepted'])
        self.assertEqual(json.loads(audit[3])['accepted_new'], 1)
        self.assertEqual(c.execute("SELECT doi FROM raw_refs WHERE paper='doi:10.1234/target'").fetchall(), [('10.1234/deposited',)])
        edges = c.execute("SELECT source,target,provider FROM edges WHERE target='doi:10.1234/target' ORDER BY source").fetchall()
        self.assertEqual(edges, [('doi:10.1234/second', 'doi:10.1234/target', 'Crossref deposited reference list'),
                                 ('doi:10.1234/source', 'doi:10.1234/target', 'Europe PMC reference list')])
        self.assertEqual(c.execute("SELECT count(*) FROM edges WHERE target='doi:10.1234/deposited'").fetchone()[0], 0)
        c.close()

    def test_mismatched_invalid_notfound_and_rejected_metadata_do_not_add_accepted(self):
        for doi in ['bad', 'missing', 'rejected', 'wrong']:
            self.ref('10.1234/'+doi)
        _, report = self.execute([
            Response('10.1234/bad', payload={'status': 'ok', 'message': {'DOI': '10.1234/bad', 'title': 42}}),
            Response('10.1234/missing', status=404),
            Response('10.1234/rejected', message=paper('10.1234/rejected', published={'date-parts': [[2027, 1, 1]]})),
            Response('10.1234/wrong', message=paper('10.1234/some-other-doi')),
        ])
        self.assertEqual(report['totals']['accepted_new'], 0)
        self.assertEqual(report['totals']['invalid'], 2)
        self.assertEqual(report['totals']['not_found'], 1)
        self.assertEqual(report['totals']['rejected_metadata'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT count(*) FROM papers WHERE accepted=1').fetchone()[0], 2)
        self.assertEqual(c.execute('SELECT count(*) FROM edges').fetchone()[0], 0)
        self.assertEqual(c.execute('SELECT count(*) FROM citation_neighbor_attempts WHERE response_body!=""').fetchone()[0], 4)
        c.close()

    def test_checkpoint_resume_skips_finished_and_retries_interrupted(self):
        self.ref('10.1234/a')
        self.ref('10.1234/b')
        _, first = self.execute([Response('10.1234/a')], maximum=1)
        self.assertEqual(first['totals']['accepted_new'], 1)
        c = atlas.connect()
        c.execute("INSERT OR REPLACE INTO citation_neighbor_checkpoint(doi,status,attempts,updated) VALUES('10.1234/b','in_progress',1,?)", (atlas.now(),))
        c.commit()
        c.close()
        client, second = self.execute([Response('10.1234/b')])
        self.assertEqual(client.asked, ['10.1234/b'])
        self.assertEqual(second['totals']['accepted_new'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT status,attempts FROM citation_neighbor_checkpoint WHERE doi='10.1234/b'").fetchone(), ('accepted', 2))
        c.close()
        client, _ = self.execute([])
        self.assertEqual(client.count, 0)

    def test_persistent_throttling_stops_all_candidates_and_persists_global_cooldown(self):
        self.ref('10.1234/a')
        self.ref('10.1234/b')
        client, report = self.execute([Response(status=429), Response(status=429)])
        self.assertEqual(client.asked, ['10.1234/a', '10.1234/a'])
        self.assertIn('persistent', report['stopped'])
        self.assertTrue(report['cooldown_until'])
        resumed, report = self.execute([])
        self.assertEqual(resumed.count, 0)
        self.assertIn('stored', report['stopped'])

    def test_long_retry_after_is_not_shortened_or_retried_early(self):
        self.ref('10.1234/target')
        client = FixtureClient([Response(status=429, headers={'Retry-After': '120'})])
        with patch.object(neighbors.time, 'sleep') as sleep, patch.object(supplement, 'log'):
            report = neighbors.run(client)
        self.assertEqual(client.count, 1)
        sleep.assert_not_called()
        self.assertIn('cooldown', report['stopped'])

    def test_checkpoint_attempt_ceiling_and_future_retry_are_preserved(self):
        self.ref('10.1234/exhausted')
        self.ref('10.1234/waiting')
        c = atlas.connect()
        c.execute("INSERT INTO citation_neighbor_checkpoint(doi,status,attempts,updated) VALUES('10.1234/exhausted','retryable',3,?)", (atlas.now(),))
        c.execute("INSERT INTO citation_neighbor_checkpoint(doi,status,attempts,updated,retry_after) VALUES('10.1234/waiting','retryable',1,?,?)", (atlas.now(), neighbors.after(3600)))
        c.commit()
        c.close()
        self.assertEqual(self.select(), [])

    def test_hard_budget_bounds_and_client_single_exact_doi_endpoint(self):
        with self.assertRaises(ValueError):
            neighbors.Client(201)
        with self.assertRaises(ValueError):
            neighbors.Client(interval=.1)
        with self.assertRaises(ValueError):
            neighbors.run(max_candidates=501)
        client = neighbors.Client(1)
        with patch.object(client.session, 'get', return_value=Response('10.1234/test')) as request, patch.object(neighbors.time, 'sleep'):
            client.get('10.1234/test')
            with self.assertRaises(neighbors.StopHarvest):
                client.get('10.1234/second')
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.args[0], neighbors.ENDPOINT+'10.1234%2Ftest')
        self.assertFalse(request.call_args.kwargs['allow_redirects'])

    def test_newly_retrieved_references_are_not_recursively_harvested_in_same_run(self):
        self.ref('10.1234/target')
        message = paper('10.1234/target', reference=[{'DOI': '10.1234/next', 'article-title': TITLE}])
        client, _ = self.execute([Response('10.1234/target', message=message)])
        self.assertEqual(client.asked, ['10.1234/target'])
        self.assertEqual([x['doi'] for x in self.select()], ['10.1234/next'])

    def test_redirect_chain_reuses_canonical_identity_and_retains_full_proof(self):
        self.ref('10.1234/old')
        supplement.ingest([paper('10.1234/canonical')], 'existing-canonical')
        first = Response('10.1234/old', status=301, headers={'Location': '/works/10.1234/canonical'})
        client, report = self.execute([first, Response('10.1234/canonical')])
        self.assertEqual(client.asked, ['10.1234/old', '10.1234/canonical'])
        self.assertEqual(report['totals']['accepted_new'], 0)
        self.assertEqual(report['totals']['reused'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT * FROM source_alias WHERE source='DOI'").fetchall(),
                         [('DOI', '10.1234/old', 'doi:10.1234/canonical')])
        self.assertEqual(c.execute("SELECT count(*) FROM papers WHERE doi='10.1234/old'").fetchone()[0], 0)
        proof = c.execute('SELECT id,doi,request_url,http_status,response_body,screening FROM citation_neighbor_attempts ORDER BY id').fetchall()
        self.assertEqual([x[3] for x in proof], [301, 200])
        self.assertEqual(proof[0][4], first.text)
        self.assertEqual(json.loads(proof[1][5])['redirect_proof_attempts'], [proof[0][0]])
        self.assertEqual(json.loads(proof[1][5])['canonical_doi'], '10.1234/canonical')
        self.assertEqual(c.execute("SELECT paper FROM citation_neighbor_checkpoint WHERE doi='10.1234/old'").fetchone(), ('doi:10.1234/canonical',))
        c.close()
        self.assertEqual(self.select(), [])

    def test_redirect_metadata_must_match_final_proven_target(self):
        self.ref('10.1234/old')
        _, report = self.execute([
            Response('10.1234/old', status=301, headers={'Location': '/works/10.1234/canonical'}),
            Response('10.1234/canonical', message=paper('10.1234/unproved'))])
        self.assertEqual(report['totals']['accepted_new'], 0)
        self.assertEqual(report['totals']['invalid'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT count(*) FROM source_alias WHERE source='DOI'").fetchone()[0], 0)
        self.assertEqual(c.execute('SELECT count(*) FROM papers').fetchone()[0], 2)
        self.assertEqual(c.execute('SELECT http_status FROM citation_neighbor_attempts ORDER BY id').fetchall(), [(301,), (200,)])
        c.close()

    def test_redirect_budget_stop_resumes_proved_target_without_rewriting_response(self):
        self.ref('10.1234/old')
        client, first = self.execute([
            Response('10.1234/old', status=301, headers={'Location': '/works/10.1234/canonical'})], maximum=1)
        self.assertEqual(client.count, 1)
        self.assertIn('budget', first['stopped'])
        c = atlas.connect()
        original = c.execute('SELECT * FROM citation_neighbor_attempts').fetchone()
        c.close()
        client, second = self.execute([Response('10.1234/canonical')])
        self.assertEqual(client.asked, ['10.1234/canonical'])
        self.assertEqual(second['totals']['accepted_new'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT * FROM citation_neighbor_attempts ORDER BY id LIMIT 1').fetchone(), original)
        c.close()

    def test_three_redirect_hops_allowed_fourth_rejected_without_provider_cooldown(self):
        self.ref('10.1234/a')
        response = [Response('10.1234/'+a, status=301, headers={'Location': '/works/10.1234/'+b})
                    for a, b in [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')]]
        client, report = self.execute(response)
        self.assertEqual(client.count, 4)
        self.assertEqual(report['totals']['redirect_responses'], 3)
        self.assertEqual(report['totals']['invalid'], 1)
        self.assertEqual(report['cooldown_until'], '')
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT error FROM citation_neighbor_checkpoint WHERE doi='10.1234/a'").fetchone(), ('Crossref DOI redirect hop limit reached',))
        c.close()

    def test_three_hops_count_every_http_request_and_apply_public_rate_floor(self):
        self.ref('10.1234/a')
        responses = [Response('10.1234/'+a, status=301, headers={'Location': '/works/10.1234/'+b})
                     for a, b in [('a', 'b'), ('b', 'c'), ('c', 'd')]] + [Response('10.1234/d')]
        ticks = [1000.]

        def sleep(seconds):
            ticks[0] += seconds

        with patch.object(neighbors.time, 'monotonic', side_effect=lambda: ticks[0]), patch.object(neighbors.time, 'sleep', side_effect=sleep) as pause, patch.object(supplement, 'log'):
            client = neighbors.Client(max_requests=4)
            with patch.object(client.session, 'get', side_effect=responses) as request:
                report = neighbors.run(client)
        self.assertEqual(client.count, 4)
        self.assertEqual(report['totals']['accepted_new'], 1)
        self.assertEqual([call.args[0] for call in pause.call_args_list], [0, 1.5, 1.5, 1.5])
        self.assertEqual([call.args[0] for call in request.call_args_list],
                         [neighbors.ENDPOINT+'10.1234%2F'+x for x in 'abcd'])
        self.assertTrue(all(call.kwargs['allow_redirects'] is False for call in request.call_args_list))

    def test_unsafe_unknown_malformed_and_looping_redirects_are_invalid(self):
        locations = ['https://evil.example/works/10.1234/target',
                     'http://api.crossref.org/works/10.1234/target',
                     'https://api.crossref.org@evil.example/works/10.1234/target',
                     'https://api.crossref.org/prefixes/10.1234/target',
                     '/works/10.1234/target?query=x', '/works/10.1234/target#fragment',
                     '/works/not-a-doi', 'target', '/works/10.1234/%0atarget',
                     '/works/10.1234/loop', '']
        for index, location in enumerate(locations):
            doi = '10.1234/loop' if location.endswith('/loop') else '10.1234/unsafe'+str(index)
            with self.subTest(location=location):
                self.ref(doi)
                client, report = self.execute([Response(doi, status=301, headers={'Location': location})])
                self.assertEqual(client.asked, [doi])
                self.assertEqual(report['totals']['invalid'], 1)
                self.assertEqual(report['cooldown_until'], '')
        self.ref('10.1234/unknown')
        _, report = self.execute([Response('10.1234/unknown', status=300)])
        self.assertEqual(report['totals']['invalid'], 1)
        self.assertEqual(report['cooldown_until'], '')

    def legacy_cooldown(self, with_provider_failure=False):
        """Reproduce the initial collector's 301 audit in this temporary DB only."""
        self.ref('10.1234/old')
        run_id = 'legacy-301'
        until = neighbors.after(3600)
        c = atlas.connect()
        c.execute('INSERT INTO citation_neighbor_runs VALUES(?,?,?,?,?,?)',
                  (run_id, atlas.now(), atlas.now(), 'unexpected public-provider HTTP response; resume later', until, '{}'))
        c.commit()
        c.close()
        candidate = next(x for x in self.select() if x['doi'] == '10.1234/old')
        neighbors.remember_origins(candidate, run_id)
        if with_provider_failure:
            attempt = neighbors.begin_attempt('10.1234/old', run_id)
            neighbors.finish_attempt(attempt, '10.1234/old', 'retryable', Response(status=429),
                                     error='HTTP 429', retry_after=until)
        attempt = neighbors.begin_attempt('10.1234/old', run_id)
        neighbors.finish_attempt(attempt, '10.1234/old', 'retryable',
                                 Response('10.1234/old', status=301, headers={'Location': '/works/10.1234/canonical'}),
                                 error='unexpected HTTP 301', retry_after=until)
        return run_id, until

    def test_only_proved_legacy_301_cooldown_waived_and_original_evidence_preserved(self):
        run_id, until = self.legacy_cooldown()
        c = atlas.connect()
        c.execute('INSERT INTO citation_neighbor_runs VALUES(?,?,?,?,?,?)',
                  ('inherited', atlas.now(), atlas.now(), 'stored public-provider cooldown remains active', until, '{}'))
        c.commit()
        runs_before = c.execute('SELECT * FROM citation_neighbor_runs ORDER BY id').fetchall()
        attempts_before = c.execute('SELECT * FROM citation_neighbor_attempts').fetchall()
        c.close()
        client, report = self.execute([Response('10.1234/canonical')])
        self.assertEqual(client.asked, ['10.1234/canonical'])
        self.assertEqual(set(report['ignored_legacy_301_cooldowns']), {run_id, 'inherited'})
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT * FROM citation_neighbor_runs WHERE id IN ('legacy-301','inherited') ORDER BY id").fetchall(), runs_before)
        self.assertEqual(c.execute('SELECT * FROM citation_neighbor_attempts WHERE run=?', (run_id,)).fetchall(), attempts_before)
        c.close()

    def test_actual_provider_cooldown_is_preserved_even_when_last_abnormal_is_301(self):
        self.legacy_cooldown(with_provider_failure=True)
        client, report = self.execute([])
        self.assertEqual(client.count, 0)
        self.assertIn('stored', report['stopped'])
        self.assertEqual(report['ignored_legacy_301_cooldowns'], {})

    def test_network_and_independent_provider_cooldowns_remain_effective(self):
        self.legacy_cooldown()
        c = atlas.connect()
        c.execute('INSERT INTO citation_neighbor_runs VALUES(?,?,?,?,?,?)',
                  ('real-provider-stop', atlas.now(), atlas.now(), 'network failure; resume later', neighbors.after(7200), '{}'))
        c.commit()
        c.close()
        client, report = self.execute([])
        self.assertEqual(client.count, 0)
        self.assertIn('stored', report['stopped'])


if __name__ == '__main__':
    unittest.main()

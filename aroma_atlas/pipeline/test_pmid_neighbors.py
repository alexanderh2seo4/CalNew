"""Offline exact-ID batch, eligibility, provenance, identity and public-budget tests."""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import atlas
import pmid_neighbors as pmids
import supplement

TITLE = 'Predicting odor intensity of aroma molecules'


def record(pmid, **more):
    return {'id': pmid, 'source': 'MED', 'pmid': pmid, 'title': TITLE,
            'abstractText': 'Aroma molecules were assessed for odor intensity.',
            'pubYear': '2020', 'firstPublicationDate': '2020-01-02',
            'pubTypeList': {'pubType': ['Journal Article']}, **more}


class Response:
    def __init__(self, rows=None, status=200, headers=None, payload=None):
        self.status_code = status
        self.headers = headers or {}
        self.url = pmids.ENDPOINT+'?audited=fixture'
        rows = rows or []
        self.payload = payload if payload is not None else {'hitCount': len(rows), 'resultList': {'result': rows}}
        self.text = json.dumps(self.payload)

    def json(self):
        return self.payload


class FixtureClient:
    def __init__(self, responses, maximum=20):
        self.responses = list(responses)
        self.maximum = maximum
        self.count = 0
        self.asked = []

    def available(self):
        return self.count < self.maximum

    def get(self, batch):
        self.count += 1
        self.asked.append(list(batch))
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class PMIDNeighborIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = atlas.DB
        atlas.DB = pathlib.Path(self.tmp.name)/'atlas.sqlite'
        pmids.init()
        atlas.ingest([record('100'), record('200')], 'core-origin')

    def tearDown(self):
        atlas.DB = self.old
        self.tmp.cleanup()

    def ref(self, target, title=TITLE, source='pmid:100', provider='MED', doi=''):
        c = atlas.connect()
        c.execute('INSERT INTO raw_refs VALUES(?,?,?,?,?)', (source, provider, target, doi, title))
        c.commit()
        c.close()

    def select(self):
        c = atlas.connect()
        answer = pmids.select_candidates(c)
        c.close()
        return answer

    def execute(self, responses, **kwargs):
        client = FixtureClient(responses, kwargs.pop('maximum', 20))
        with contextlib.redirect_stdout(io.StringIO()), patch.object(pmids.time, 'sleep'):
            report = pmids.run(client, **kwargs)
        return client, report

    def test_only_actual_unknown_numeric_core_med_ids_with_scope_or_real_recurrence(self):
        self.ref('300')
        self.ref('400', 'Statistical methods')
        self.ref('400', '', source='pmid:200')
        self.ref('500', 'Generic methods')
        self.ref('500', 'Generic methods', provider='PMID')
        self.ref('100')
        self.ref('MED:600')
        self.ref('600', provider='OpenAlex')
        self.ref('700', title='Generic methods; PMID 300 is relevant')
        self.ref('000800')
        self.assertEqual([e['pmid'] for e in self.select()], ['300', '400'])
        c = atlas.connect()
        c.execute("UPDATE papers SET tracks='[\"pharmacology\"]' WHERE id='pmid:200'")
        c.commit()
        c.close()
        self.assertEqual([e['pmid'] for e in self.select()], ['300'])

    def test_explicit_exact_or_batch_query_and_request_batch_limits(self):
        query = pmids.query_params(['123', '456'])
        self.assertEqual(query['query'], '(EXT_ID:123 OR EXT_ID:456) AND SRC:MED AND FIRST_PDATE:[1800-01-01 TO 2026-10-26]')
        self.assertEqual(query['resultType'], 'core')
        self.assertEqual(query['pageSize'], 2)
        for batch in [[], ['1', '1'], ['1 OR 2'], ['0'], [str(n) for n in range(1, 102)]]:
            with self.subTest(batch=batch[:3]), self.assertRaises(ValueError):
                pmids.query_params(batch)
        with self.assertRaises(ValueError):
            pmids.Client(101)
        with self.assertRaises(ValueError):
            pmids.Client(interval=.1)
        with self.assertRaises(ValueError):
            pmids.run(batch_size=101)

    def test_wrong_returned_source_id_duplicate_or_pmid_aborts_entire_batch_before_ingest(self):
        variants = [record('999'), record('300', source='PMC'), {**record('300'), 'pmid': '301'},
                    [record('300'), record('300')]]
        self.ref('300')
        self.ref('400')
        for index, variant in enumerate(variants):
            with self.subTest(variant=index):
                rows = variant if isinstance(variant, list) else [variant]
                client, report = self.execute([Response(rows)])
                self.assertEqual(client.count, 1)
                self.assertEqual(report['totals']['accepted_new_provisional'], 0)
                self.assertEqual(report['totals']['invalid_batches'], 1)
                c = atlas.connect()
                self.assertEqual(c.execute('SELECT count(*) FROM papers').fetchone()[0], 2)
                self.assertTrue(c.execute('SELECT response_body FROM pmid_neighbor_requests ORDER BY id DESC LIMIT 1').fetchone()[0])
                c.execute("UPDATE pmid_neighbor_checkpoint SET attempts=0,retry_after='' ")
                c.commit()
                c.close()

    def test_future_and_ambiguous_dates_retained_but_not_ingested(self):
        for target in ['300', '400', '500', '600', '700']:
            self.ref(target)
        rows = [record('300', firstPublicationDate='2026-10-27', pubYear='2026'),
                record('400', firstPublicationDate='', pubYear='2026'),
                record('500', firstPublicationDate='', pubYear='2025'),
                record('600', firstPublicationDate='2026-10-26', pubYear='2026'),
                record('700', firstPublicationDate='invalid', pubYear='2027')]
        _, report = self.execute([Response(rows)])
        self.assertEqual(report['totals']['retrieved_exact'], 5)
        self.assertEqual(report['totals']['date_rejected'], 3)
        self.assertEqual(report['totals']['accepted_new_provisional'], 2)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT id FROM papers WHERE id NOT IN ("pmid:100","pmid:200") ORDER BY id').fetchall(), [('pmid:500',), ('pmid:600',)])
        self.assertEqual(c.execute("SELECT count(*) FROM pmid_neighbor_records WHERE outcome='date_rejected'").fetchone()[0], 3)
        c.close()

    def test_native_pubtype_and_scope_rejections_remain_auditable_candidates(self):
        for target in ['300', '400', '500']:
            self.ref(target)
        rows = [record('300', pubTypeList={'pubType': ['Book Review']}),
                record('400', pubTypeList={'pubType': ['Retracted Publication']}),
                record('500', title='Kinase inhibitors in cancer', abstractText='Generic drug scaffolds were screened.')]
        _, report = self.execute([Response(rows)])
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        self.assertEqual(report['totals']['rejected_metadata'], 3)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT count(*) FROM papers WHERE accepted=0').fetchone()[0], 3)
        self.assertEqual(c.execute("SELECT count(*) FROM pmid_neighbor_records WHERE outcome='rejected'").fetchone()[0], 3)
        self.assertEqual(c.execute('SELECT count(*) FROM edges').fetchone()[0], 0)
        c.close()

    def test_exact_doi_reuses_existing_metadata_registers_med_alias_and_real_edges(self):
        target_doi = '10.1234/target'
        supplement.init()
        supplement.ingest([{'DOI': target_doi, 'title': [TITLE], 'abstract': 'Preserved enriched aroma molecule intensity abstract',
                           'type': 'journal-article', 'published': {'date-parts': [[2020, 1, 1]]}}], 'existing-doi')
        self.ref('300', doi=target_doi)
        self.ref('300', source='pmid:200', provider='PMID')
        incoming = record('300', doi='https://doi.org/10.1234/TARGET')
        _, report = self.execute([Response([incoming])])
        self.assertEqual(report['totals']['reused_identities'], 1)
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT id,abstract FROM papers WHERE doi=?', (target_doi,)).fetchall(),
                         [('doi:10.1234/target', 'Preserved enriched aroma molecule intensity abstract')])
        self.assertEqual(c.execute("SELECT source,paper FROM source_alias WHERE source_id='300' ORDER BY source").fetchall(),
                         [('MED', 'doi:10.1234/target'), ('PMID', 'doi:10.1234/target')])
        self.assertEqual(c.execute("SELECT source,target FROM edges ORDER BY source").fetchall(),
                         [('pmid:100', 'doi:10.1234/target'), ('pmid:200', 'doi:10.1234/target')])
        self.assertEqual(c.execute("SELECT target_source,target_id FROM raw_refs ORDER BY paper").fetchall(), [('MED', '300'), ('PMID', '300')])
        self.assertEqual(json.loads(c.execute('SELECT raw FROM pmid_neighbor_records').fetchone()[0]), incoming)
        c.close()

    def test_two_med_ids_with_same_exact_doi_do_not_inflate_new_identity_count(self):
        self.ref('300')
        self.ref('400')
        _, report = self.execute([Response([record('300', doi='10.1234/same'), record('400', doi='10.1234/same')])])
        self.assertEqual(report['totals']['accepted_metadata'], 2)
        self.assertEqual(report['totals']['accepted_new_provisional'], 1)
        self.assertEqual(report['totals']['reused_identities'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT count(*) FROM papers WHERE doi='10.1234/same'").fetchone()[0], 1)
        c.close()

    def test_origin_queries_full_batch_and_missing_ids_saved_without_reference_invention(self):
        self.ref('300')
        self.ref('400')
        response = Response([record('300', reference=[{'id': '999', 'source': 'MED'}])])
        _, report = self.execute([response])
        self.assertEqual(report['totals']['accepted_new_provisional'], 1)
        self.assertEqual(report['totals']['not_returned'], 1)
        c = atlas.connect()
        request = c.execute('SELECT requested_pmids,request_params,response_body FROM pmid_neighbor_requests').fetchone()
        self.assertEqual(json.loads(request[0]), ['300', '400'])
        self.assertIn('EXT_ID:400', json.loads(request[1])['query'])
        self.assertEqual(request[2], response.text)
        self.assertEqual(c.execute("SELECT status FROM pmid_neighbor_checkpoint WHERE pmid='400'").fetchone(), ('not_returned',))
        self.assertEqual(json.loads(c.execute('SELECT citing_queries FROM pmid_neighbor_origins LIMIT 1').fetchone()[0]), ['core-origin'])
        self.assertEqual(c.execute("SELECT count(*) FROM raw_refs WHERE paper='pmid:300'").fetchone()[0], 0)
        self.assertEqual(c.execute("SELECT count(*) FROM refs WHERE paper='pmid:300'").fetchone()[0], 0)
        c.close()
        client, _ = self.execute([])
        self.assertEqual(client.count, 0)

    def test_incomplete_batch_counts_do_not_claim_missing_coverage(self):
        self.ref('300')
        _, report = self.execute([Response(payload={'hitCount': 1, 'resultList': {'result': []}})])
        self.assertEqual(report['totals']['not_returned'], 0)
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        self.assertEqual(report['totals']['invalid_batches'], 1)

    def test_resume_skips_completed_unknown_and_retries_interrupted_with_attempt_ceiling(self):
        for target in ['300', '400', '500']:
            self.ref(target)
        client, first = self.execute([Response([record('300')])], batch_size=2, maximum=1, max_candidates=3)
        self.assertEqual(client.asked, [['300', '400']])
        c = atlas.connect()
        c.execute("UPDATE pmid_neighbor_checkpoint SET status='in_progress',attempts=1 WHERE pmid='500'")
        c.commit()
        c.close()
        client, _ = self.execute([Response([record('500')])])
        self.assertEqual(client.asked, [['500']])
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT attempts FROM pmid_neighbor_checkpoint WHERE pmid='500'").fetchone()[0], 2)
        c.close()

    def test_persistent_429_stops_all_batches_and_preserves_global_cooldown(self):
        self.ref('300')
        self.ref('400')
        client, report = self.execute([Response(status=429), Response(status=429)], batch_size=1)
        self.assertEqual(client.asked, [['300'], ['300']])
        self.assertIn('persistent', report['stopped'])
        resumed, report = self.execute([])
        self.assertEqual(resumed.count, 0)
        self.assertIn('stored', report['stopped'])

    def test_long_retry_after_and_network_failure_stop_without_retry_evasion(self):
        self.ref('300')
        client = FixtureClient([Response(status=429, headers={'Retry-After': '120'})])
        with contextlib.redirect_stdout(io.StringIO()), patch.object(pmids.time, 'sleep') as pause:
            report = pmids.run(client)
        pause.assert_not_called()
        self.assertEqual(client.count, 1)
        self.assertIn('cooldown', report['stopped'])

    def test_client_counts_batches_and_respects_one_second_floor_and_budget(self):
        ticks = [1000.]

        def sleep(seconds):
            ticks[0] += seconds

        with patch.object(pmids.time, 'monotonic', side_effect=lambda: ticks[0]), patch.object(pmids.time, 'sleep', side_effect=sleep) as pause:
            client = pmids.Client(2)
            with patch.object(client.session, 'get', return_value=Response()) as request:
                client.get(['300'])
                client.get(['400'])
                with self.assertRaises(pmids.StopHarvest):
                    client.get(['500'])
        self.assertEqual(client.count, 2)
        self.assertEqual([call.args[0] for call in pause.call_args_list], [0, 1.])
        self.assertEqual(request.call_count, 2)
        self.assertFalse(request.call_args.kwargs['allow_redirects'])

    def test_existing_exact_pmid_metadata_is_preserved_if_it_arrives_during_request(self):
        self.ref('300')
        client = FixtureClient([Response([record('300', abstractText='Short replacement aroma abstract')])])
        original = client.get

        def get(batch):
            atlas.ingest([record('300', abstractText='Preserved enriched odor intensity of aroma molecules abstract')], 'race')
            return original(batch)

        client.get = get
        with contextlib.redirect_stdout(io.StringIO()):
            report = pmids.run(client)
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        self.assertEqual(report['totals']['reused_identities'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute("SELECT abstract FROM papers WHERE id='pmid:300'").fetchone(),
                         ('Preserved enriched odor intensity of aroma molecules abstract',))
        c.close()

    def test_dangling_identity_conflict_does_not_insert_a_new_accepted_paper(self):
        self.ref('300')
        c = atlas.connect()
        c.execute("INSERT INTO source_alias VALUES('MED','300','missing-paper')")
        c.commit()
        c.close()
        _, report = self.execute([Response([record('300')])])
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT count(*) FROM papers').fetchone()[0], 2)
        self.assertEqual(c.execute("SELECT status FROM pmid_neighbor_checkpoint WHERE pmid='300'").fetchone(), ('identity_conflict',))
        c.close()

    def test_malformed_native_record_fields_are_audited_without_insertion(self):
        self.ref('300')
        _, report = self.execute([Response([record('300', journalInfo={'journal': {'title': {'bad': 'type'}}})])])
        self.assertEqual(report['totals']['invalid_records'], 1)
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)

    def test_network_failure_is_counted_and_checkpoint_and_global_cooldown_retained(self):
        self.ref('300')
        client, report = self.execute([pmids.requests.ConnectionError('fixture connection failure')])
        self.assertEqual(client.count, 1)
        self.assertEqual(report['unique_pmids_requested_this_run'], 1)
        self.assertEqual(report['totals']['requested_id_occurrences'], 1)
        self.assertIn('network', report['stopped'])
        resumed, _ = self.execute([])
        self.assertEqual(resumed.count, 0)

    def test_exhausted_and_future_retry_checkpoints_are_not_queried(self):
        self.ref('300')
        self.ref('400')
        c = atlas.connect()
        c.execute("INSERT INTO pmid_neighbor_checkpoint(pmid,status,attempts,updated) VALUES('300','retryable',3,?)", (atlas.now(),))
        c.execute("INSERT INTO pmid_neighbor_checkpoint(pmid,status,attempts,updated,retry_after) VALUES('400','retryable',1,?,?)", (atlas.now(), pmids.neighbors.after(3600)))
        c.commit()
        c.close()
        self.assertEqual(self.select(), [])

    def crossref(self, doi='10.1234/target', title=TITLE, abstract='', reference=None):
        supplement.init()
        supplement.ingest([{'DOI': doi, 'title': [title], 'abstract': abstract,
                           'type': 'journal-article', 'published': {'date-parts': [[2020, 1, 1]]},
                           'reference': reference or []}], 'prior-provider')
        return 'doi:'+doi

    def cache(self, incoming, paper, outcome='accepted', aliases=True):
        pmid = incoming['id']
        self.ref(pmid)
        candidate = next(e for e in self.select() if e['pmid'] == pmid)
        run_id = 'legacy-cache-'+pmid
        c = atlas.connect()
        c.execute('INSERT INTO pmid_neighbor_runs VALUES(?,?,?,?,?,?)',
                  (run_id, atlas.now(), atlas.now(), 'legacy complete', '', '{"original":true}'))
        c.commit()
        c.close()
        pmids.remember_origins([candidate], run_id)
        request_id = pmids.begin_request([pmid], run_id)
        response = Response([incoming])
        pmids.finish_request(request_id, 'complete', response=response)
        pmids.response_rows(response, [pmid], request_id)
        pmids.finish_record(request_id, 0, outcome, pmids.screen(incoming), paper)
        pmids.checkpoint(pmid, outcome, paper=paper)
        c = atlas.connect()
        if aliases:
            for source in ['MED', 'PMID']:
                c.execute('INSERT OR IGNORE INTO source_alias VALUES(?,?,?)', (source, pmid, paper))
        c.commit()
        c.close()
        return run_id, request_id

    def test_primary_abstract_promotion_removes_false_acceptance_and_archives_every_field(self):
        title = 'Predicting odor quality from molecular structure'
        paper = self.crossref(title=title)
        self.ref('300')
        c = atlas.connect()
        before = pmids.paper_row(c, paper)
        self.assertEqual(before['accepted'], 1)
        c.close()
        incoming = record('300', doi='10.1234/target', title=title,
                          abstractText='Moth pheromone receptor mechanisms were studied in insect antennae.')
        _, report = self.execute([Response([incoming])])
        self.assertEqual(report['totals']['promoted'], 1)
        self.assertEqual(report['totals']['removed_existing'], 1)
        self.assertEqual(report['totals']['accepted_new_provisional'], 0)
        c = atlas.connect()
        after = pmids.paper_row(c, paper)
        self.assertEqual((after['id'], after['source'], after['source_id'], after['accepted']), (paper, 'MED', '300', 0))
        self.assertEqual(json.loads(after['raw']), incoming)
        archive = c.execute('SELECT canonical_row,raw FROM pmid_neighbor_canonical_archive').fetchone()
        self.assertEqual(json.loads(archive[0]), before)
        self.assertEqual(archive[1], before['raw'])
        with self.assertRaises(pmids.sqlite3.IntegrityError):
            c.execute("UPDATE pmid_neighbor_canonical_archive SET raw='changed'")
        c.rollback()
        with self.assertRaises(pmids.sqlite3.IntegrityError):
            c.execute('DELETE FROM pmid_neighbor_canonical_archive')
        c.close()

    def test_review_exclusions_still_hold_after_richer_native_primary_promotion(self):
        paper = self.crossref()
        self.ref('300')
        review = {paper: {'id': paper, 'verdict': 'out-of-scope', 'reason': 'Explicit frozen diagnostic negative'}}
        with patch.object(atlas, 'review_exclusions', return_value=review):
            _, report = self.execute([Response([record('300', doi='10.1234/target')])])
        self.assertEqual(report['totals']['promoted'], 1)
        self.assertEqual(report['totals']['activated_existing'], 0)
        c = atlas.connect()
        row = pmids.paper_row(c, paper)
        self.assertEqual(row['accepted'], 0)
        self.assertEqual(json.loads(row['tracks']), [])
        self.assertIn('Explicit frozen diagnostic negative', row['evidence'])
        c.close()

    def test_promotion_preserves_old_caches_raw_references_aliases_and_queues_real_med_lookup(self):
        paper = self.crossref(reference=[{'DOI': '10.1234/real-deposited'}])
        self.ref('300')
        c = atlas.connect()
        old_refs = c.execute('SELECT * FROM refs WHERE paper=?', (paper,)).fetchone()
        old_cache = c.execute('SELECT * FROM crossref_responses').fetchall()
        old_raw_refs = c.execute('SELECT * FROM raw_refs ORDER BY paper').fetchall()
        c.close()
        _, report = self.execute([Response([record('300', doi='10.1234/target', hasReferences='Y')])])
        self.assertEqual(report['totals']['refs_reset'], 1)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT * FROM crossref_responses').fetchall(), old_cache)
        self.assertEqual(c.execute('SELECT * FROM raw_refs ORDER BY paper').fetchall(), old_raw_refs)
        self.assertEqual(c.execute("SELECT paper FROM source_alias WHERE source='Crossref' AND source_id='10.1234/target'").fetchone(), (paper,))
        self.assertEqual(json.loads(c.execute('SELECT refs_row FROM pmid_neighbor_canonical_archive').fetchone()[0]), list(old_refs))
        self.assertEqual(c.execute('''SELECT p.id,p.source,p.source_id FROM papers p LEFT JOIN refs r ON r.paper=p.id
            WHERE p.id=? AND p.accepted=1 AND p.source='MED' AND r.paper IS NULL''', (paper,)).fetchone(), (paper, 'MED', '300'))
        c.close()

    def test_less_informative_med_metadata_does_not_replace_existing_richer_primary(self):
        existing = record('300', doi='10.1234/target', abstractText='Aroma molecule intensity was studied. '*20)
        atlas.ingest([existing], 'rich-primary')
        self.ref('400')
        c = atlas.connect()
        before = pmids.paper_row(c, 'pmid:300')
        c.close()
        _, report = self.execute([Response([record('400', doi='10.1234/target', abstractText='Aroma molecules.')])])
        self.assertEqual(report['totals']['promoted'], 0)
        c = atlas.connect()
        self.assertEqual(pmids.paper_row(c, 'pmid:300'), before)
        self.assertEqual(c.execute('SELECT count(*) FROM pmid_neighbor_canonical_archive').fetchone()[0], 0)
        c.close()

    def test_only_proved_old_non_med_overall_reference_status_is_cleared(self):
        paper = self.crossref()
        self.ref('300')
        c = atlas.connect()
        c.execute("UPDATE refs SET error='Europe PMC actual completed lookup' WHERE paper=?", (paper,))
        c.commit()
        before = c.execute('SELECT * FROM refs WHERE paper=?', (paper,)).fetchone()
        c.close()
        _, report = self.execute([Response([record('300', doi='10.1234/target')])])
        self.assertEqual(report['totals']['refs_reset'], 0)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT * FROM refs WHERE paper=?', (paper,)).fetchone(), before)
        c.close()

    def test_explicit_excluded_type_uses_actual_native_raw_and_archives_prior_richer_metadata(self):
        paper = self.crossref(abstract='Aroma molecules were assessed in detailed experiments. '*20)
        self.ref('300')
        incoming = record('300', doi='10.1234/target', abstractText='', pubTypeList={'pubType': ['Retracted Publication']})
        _, report = self.execute([Response([incoming])])
        self.assertEqual(report['totals']['promoted'], 1)
        c = atlas.connect()
        self.assertEqual(pmids.paper_row(c, paper)['accepted'], 0)
        self.assertEqual(json.loads(pmids.paper_row(c, paper)['raw']), incoming)
        self.assertGreater(len(json.loads(c.execute('SELECT canonical_row FROM pmid_neighbor_canonical_archive').fetchone()[0])['abstract']), 500)
        c.close()

    def test_cached_enrichment_uses_no_network_and_keeps_original_requests_records_reports_immutable(self):
        paper = self.crossref()
        legacy_run, _ = self.cache(record('300', doi='10.1234/target'), paper)
        c = atlas.connect()
        original_requests = c.execute('SELECT * FROM pmid_neighbor_requests').fetchall()
        original_records = c.execute('SELECT * FROM pmid_neighbor_records').fetchall()
        original_report = c.execute('SELECT * FROM pmid_neighbor_runs WHERE id=?', (legacy_run,)).fetchone()
        c.close()
        with patch.object(pmids.requests.Session, 'get', side_effect=AssertionError('cached enrichment must not access network')):
            report = pmids.enrich_cached()
        self.assertEqual(report['requests_this_run'], 0)
        self.assertEqual(report['totals']['promoted'], 1)
        self.assertEqual(report['totals']['new_candidates'], 0)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT * FROM pmid_neighbor_requests').fetchall(), original_requests)
        self.assertEqual(c.execute('SELECT * FROM pmid_neighbor_records').fetchall(), original_records)
        self.assertEqual(c.execute('SELECT * FROM pmid_neighbor_runs WHERE id=?', (legacy_run,)).fetchone(), original_report)
        c.close()
        second = pmids.enrich_cached()
        self.assertEqual(second['totals']['promoted'], 0)

    def test_cached_conflicts_stay_held_until_an_existing_exact_doi_alias_proves_identity(self):
        paper = self.crossref(doi='10.1234/canonical')
        self.cache(record('300', doi='10.1234/old-alias'), paper, outcome='identity_conflict', aliases=False)
        c = atlas.connect()
        c.execute("UPDATE papers SET pmid='300' WHERE id=?", (paper,))
        c.commit()
        c.close()
        first = pmids.enrich_cached()
        self.assertEqual(first['totals']['held_conflicts'], 1)
        self.assertEqual(first['totals']['promoted'], 0)
        c = atlas.connect()
        c.execute("INSERT INTO source_alias VALUES('DOI','10.1234/old-alias',?)", (paper,))
        c.commit()
        c.close()
        second = pmids.enrich_cached()
        self.assertEqual(second['totals']['promoted'], 1)
        self.assertEqual(second['totals']['held_conflicts'], 0)
        c = atlas.connect()
        self.assertEqual(c.execute('SELECT doi FROM papers WHERE id=?', (paper,)).fetchone()[0], '10.1234/canonical')
        self.assertEqual(c.execute("SELECT source_id FROM source_alias WHERE source='DOI'").fetchall(), [('10.1234/old-alias',)])
        self.assertEqual(json.loads(c.execute('SELECT raw FROM papers WHERE id=?', (paper,)).fetchone()[0])['doi'], '10.1234/old-alias')
        c.close()

    def test_context_hashes_and_review_map_are_frozen_before_network_and_report_files_not_overwritten(self):
        paper = self.crossref()
        self.ref('300')
        marker = ['start']
        reviews = [{paper: {'id': paper, 'verdict': 'out-of-scope', 'reason': 'Frozen initial negative'}}]
        client = FixtureClient([Response([record('300', doi='10.1234/target')])])
        original_get = client.get

        def get(batch):
            marker[0] = 'changed-after-start'
            reviews[0] = {}
            return original_get(batch)

        client.get = get
        path = pathlib.Path(self.tmp.name)/'original-report.json'
        path.write_text('preserve original report')
        with contextlib.redirect_stdout(io.StringIO()), patch.object(pmids.neighbors, 'file_hash', side_effect=lambda p: marker[0]), patch.object(atlas, 'review_exclusions', side_effect=lambda: reviews[0]):
            report = pmids.run(client, report_path=path)
        self.assertEqual(set(report['hashes'].values()), {'start'})
        self.assertTrue(report['allowlist_hashes'])
        self.assertEqual(set(report['allowlist_hashes'].values()), {'start'})
        self.assertEqual(path.read_text(), 'preserve original report')
        self.assertNotEqual(report['report_file'], str(path))
        c = atlas.connect()
        self.assertEqual(pmids.paper_row(c, paper)['accepted'], 0)
        c.close()


if __name__ == '__main__':
    unittest.main()

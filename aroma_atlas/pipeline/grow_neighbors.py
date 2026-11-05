#!/usr/bin/env python3
"""Finite, checkpointed citation discovery from a validated atlas snapshot.

This counts screened publication records, not manually verified papers. It never
changes scope rules or publishes. Run only as the sole metadata writer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import atlas
import neighbors
import supplement

ROOT = atlas.ROOT
STATE = ROOT/'research/neighbor_growth_job.json'


def policy_hashes():
    paths = [Path(atlas.__file__), Path(supplement.__file__), Path(neighbors.__file__)]
    paths += list((ROOT/'research').glob('*allowlist*.json'))
    paths += [p for p in atlas.review_paths() if p.exists()]
    paths += [ROOT/'research/verified_seeds.json', ROOT/'research/industrial_seed_metadata.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}


def counts():
    c = atlas.connect()
    result = {'candidates': c.execute('SELECT count(*) FROM papers').fetchone()[0],
              'accepted': c.execute('SELECT count(*) FROM papers WHERE accepted=1').fetchone()[0]}
    c.close()
    return result


def save(state):
    state['updated'] = atlas.now()
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', type=int, default=50000)
    p.add_argument('--max-requests', type=int, default=2000)
    p.add_argument('--batch-requests', type=int, default=200)
    p.add_argument('--max-seconds', type=int, default=7200)
    a = p.parse_args()
    if not 0 <= a.max_requests <= 4000 or not 1 <= a.batch_requests <= 200 or not 1 <= a.max_seconds <= 14400:
        p.error('Use at most 4000 total requests, 200/batch, and 14400 seconds.')
    frozen = policy_hashes()
    manifest = json.loads((ROOT/'data/run_manifest.json').read_text())
    mismatch = [path for path, h in frozen.items() if manifest['hashes'].get(path) != h]
    before = counts()
    if mismatch or any(before[k] != manifest['stats'][k] for k in before):
        raise RuntimeError('Run the full validation pipeline before growth; snapshot/policy mismatch: '+','.join(mismatch))
    state = {'pid': os.getpid(), 'started': atlas.now(), 'status': 'running',
             'target': a.target, 'before': before, 'current': before,
             'max_requests': a.max_requests, 'max_seconds': a.max_seconds,
             'requests': 0, 'batches': [], 'policy_hashes': frozen,
             'interpretation': 'Screened publication count only. Full rescreen/export/audit and private Site publication remain required after collection.'}
    started = time.monotonic()
    save(state)
    while state['current']['accepted'] < a.target and state['requests'] < a.max_requests:
        remaining = a.max_seconds - (time.monotonic()-started)
        if remaining < 2:
            state['status'] = 'elapsed_budget_reached'
            break
        if policy_hashes() != frozen:
            state['status'] = 'policy_changed_stop_for_rescreen'
            break
        budget = min(a.batch_requests, a.max_requests-state['requests'])
        report = neighbors.run(neighbors.Client(budget, max_seconds=max(1, min(900, int(remaining)))),
                               max_candidates=min(500, budget+30))
        state['requests'] += report['requests_this_run']
        state['current'] = counts()
        state['batches'].append({k: report[k] for k in ['run', 'started', 'finished', 'requests_this_run', 'totals', 'stopped', 'cooldown_until']})
        save(state)
        print(json.dumps({'stage': 'growth_batch', 'accepted': state['current']['accepted'],
                          'requests_total': state['requests'], 'last': state['batches'][-1]}), flush=True)
        if report['stopped'] not in ('request or elapsed-time budget reached', 'selected snapshot exhausted'):
            state['status'] = 'provider_stop'
            break
        if not report['requests_this_run'] or not report['selected_candidates']:
            state['status'] = 'available_candidate_snapshot_exhausted'
            break
    if state['status'] == 'running':
        state['status'] = 'numeric_target_reached_pending_validation' if state['current']['accepted'] >= a.target else 'request_budget_reached'
    state['finished'] = atlas.now()
    save(state)
    history = ROOT/'research/neighbor_growth_jobs'
    history.mkdir(exist_ok=True)
    (history/(str(state['pid'])+'.json')).write_text(json.dumps(state, indent=2))
    print(json.dumps({'status': state['status'], 'current': state['current'], 'requests': state['requests']}), flush=True)


if __name__ == '__main__':
    main()

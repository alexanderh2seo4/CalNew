"""Command-line interface. All network acquisition is an explicit command."""
import argparse
import importlib.metadata
import json
from pathlib import Path

from .io import clean_json,read_json,write_json


def _jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main(argv=None):
    p=argparse.ArgumentParser(description='CALNEW reproducible molecular odour research')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Check runtime and optional dependencies')
    s=sub.add_parser('sources');s.add_argument('--registry',type=Path,default=Path('configs/sources.json'))
    for name in ('fetch','ingest'):
        s=sub.add_parser(name);s.add_argument('source');s.add_argument('--registry',type=Path,default=Path('configs/sources.json'));s.add_argument('--data',type=Path,default=Path('data'))
    s=sub.add_parser('snapshot');s.add_argument('--data',type=Path,default=Path('data'))
    s=sub.add_parser('import-reviewed');s.add_argument('records',type=Path);s.add_argument('--database',type=Path,default=Path('data/evidence.sqlite'))
    s=sub.add_parser('quality-audit');s.add_argument('snapshot',type=Path);s.add_argument('--out',type=Path,default=Path('data/quality-audit.json'))
    s=sub.add_parser('benchmark');s.add_argument('--snapshot',type=Path);s.add_argument('--endpoint',required=True);s.add_argument('--source',required=True);s.add_argument('--config',type=Path,default=Path('configs/pilot.yaml'));s.add_argument('--out',type=Path,required=True);s.add_argument('--cache',type=Path,default=Path('data/features'))
    s=sub.add_parser('audit-holdout');s.add_argument('run',type=Path)
    s=sub.add_parser('report');s.add_argument('run',type=Path)
    s=sub.add_parser('predict');s.add_argument('--run',type=Path,required=True);s.add_argument('--smiles',nargs='+',required=True);s.add_argument('--endpoint');s.add_argument('--out',type=Path)
    s=sub.add_parser('conformers');s.add_argument('--smiles',nargs='+',required=True);s.add_argument('--seed',type=int,default=42);s.add_argument('--generated',type=int,default=32);s.add_argument('--retained',type=int,default=16)
    s=sub.add_parser('discover');s.add_argument('query');s.add_argument('--out',type=Path,required=True)
    s=sub.add_parser('retrieve');s.add_argument('pmcid');s.add_argument('--out',type=Path,default=Path('data/documents'))
    s=sub.add_parser('extraction-audit');s.add_argument('--gold',type=Path,required=True);s.add_argument('--predicted',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
    s=sub.add_parser('suggest');s.add_argument('pool',type=Path);s.add_argument('--batch-size',type=int,required=True);s.add_argument('--policy',choices=['mixed','random','diversity'],default='mixed');s.add_argument('--out',type=Path,required=True)
    s=sub.add_parser('pipeline',help='Modular quality -> potency -> combiner pipeline')
    ps=s.add_subparsers(dest='pipeline_command',required=True)
    t=ps.add_parser('train');t.add_argument('--snapshot',type=Path);t.add_argument('--out',type=Path,required=True)
    t.add_argument('--reserved-run',type=Path,nargs='*',default=[Path('runs/basic-threshold-models'),Path('runs/basic-descriptor-models')])
    t.add_argument('--anchor',choices=['fingerprint','unimol2'],default='fingerprint');t.add_argument('--folds',type=int,default=5)
    t.add_argument('--fast',action='store_true');t.add_argument('--threads',type=int,default=8);t.add_argument('--cache',type=Path,default=Path('data/features'))
    t=ps.add_parser('predict');t.add_argument('--run',type=Path,required=True);t.add_argument('--smiles',nargs='+',required=True)
    t.add_argument('--dilution',type=float,default=1e-3);t.add_argument('--mixture',action='store_true');t.add_argument('--out',type=Path)
    a=p.parse_args(argv)
    try:
        if a.command=='doctor':
            result={'packages':{}}
            for package in ('calnew','numpy','rdkit','torch','xgboost','transformers','unimol-tools','chemprop','openpom'):
                try: result['packages'][package]=importlib.metadata.version(package)
                except importlib.metadata.PackageNotFoundError: result['packages'][package]=None
            try:
                import torch
                result['compute']={'cuda':torch.cuda.is_available(),'mps':torch.backends.mps.is_available()}
                from .models.classical import load_xgboost
                load_xgboost();result['xgboost_runtime']='available'
            except (ImportError,RuntimeError,OSError) as exc: result['runtime_error']=str(exc)
        elif a.command=='sources': result=read_json(a.registry)
        elif a.command in ('fetch','ingest'):
            from .ingest import fetch_source,ingest_source
            from .store import EvidenceStore
            if a.command=='fetch': result={'raw_path':str(fetch_source(a.registry,a.source,a.data))}
            else:
                registry=read_json(a.registry);raw=a.data/'raw'/a.source/registry['pyrfume_revision']
                store=EvidenceStore(a.data/'evidence.sqlite')
                try: result=ingest_source(raw,store)
                finally: store.close()
        elif a.command=='snapshot':
            from .store import EvidenceStore
            store=EvidenceStore(a.data/'evidence.sqlite')
            manifests={read_json(f)['source_id']:read_json(f) for f in (a.data/'raw').glob('*/*/download.json')}
            try: path=store.snapshot(a.data/'snapshots',manifests)
            finally: store.close()
            result={'snapshot':str(path)};write_json(a.data/'current.json',result)
        elif a.command=='import-reviewed':
            from .ingest import import_reviewed
            from .store import EvidenceStore
            store=EvidenceStore(a.database)
            try: result={'imported':import_reviewed(a.records,store)}
            finally: store.close()
        elif a.command=='quality-audit':
            from .review import quality_audit
            result=quality_audit(a.snapshot);write_json(a.out,result)
        elif a.command=='benchmark':
            import yaml
            from .benchmark import run_benchmark
            from .report import render_report
            snapshot=a.snapshot or Path(read_json(Path('data/current.json'))['snapshot'])
            report=run_benchmark(snapshot,a.endpoint,a.source,yaml.safe_load(a.config.read_text()),a.out,a.cache)
            result={'selected':report['selected'],'status':report['status'],'report':str(render_report(a.out))}
        elif a.command=='audit-holdout':
            from .benchmark import audit_holdout
            result=audit_holdout(a.run)
        elif a.command=='report':
            from .report import render_report
            result={'report':str(render_report(a.run))}
        elif a.command=='predict':
            from .predict import predict_records
            result=predict_records(a.run,a.smiles,a.endpoint)
            if a.out: write_json(a.out,result)
        elif a.command=='conformers':
            from .conformers import generate
            result=[generate(s,seed=a.seed,generated=a.generated,retained=a.retained) for s in a.smiles]
        elif a.command=='discover':
            from .review import discover
            result=discover(a.query);write_json(a.out,result)
        elif a.command=='retrieve':
            from .review import retrieve_open_article
            result=retrieve_open_article(a.pmcid,a.out)
        elif a.command=='extraction-audit':
            from .review import extraction_audit
            result=extraction_audit(_jsonl(a.gold),_jsonl(a.predicted));write_json(a.out,result)
        elif a.command=='suggest':
            from .active import suggest
            pool=read_json(a.pool)
            result=suggest(pool['candidates'],a.batch_size,anchors=pool.get('anchors',[]),protected_groups=pool.get('protected_groups',[]),policy=a.policy)
            write_json(a.out,result)
        elif a.command=='pipeline':
            from .pipeline.run import predict as pipeline_predict,run_pipeline
            if a.pipeline_command=='train':
                snapshot=a.snapshot or Path(read_json(Path('data/current.json'))['snapshot'])
                metrics=run_pipeline(snapshot,a.reserved_run,a.out,anchor=a.anchor,folds=a.folds,fast=a.fast,cache_root=a.cache,threads=a.threads,
                                     log=lambda m:print(m,file=__import__('sys').stderr,flush=True))
                result={'report':str(a.out/'REPORT.md'),'threshold_ensemble':metrics['threshold']['ensemble'],
                        'intensity':metrics['intensity']['pipeline_stage_B2_hill']}
            else:
                result=pipeline_predict(a.run,a.smiles,a.dilution,a.mixture)
                if a.out: write_json(a.out,result)
        print(json.dumps(clean_json(result),indent=2))
    except (ValueError,RuntimeError,OSError,ImportError,KeyError) as exc:
        p.exit(2,f'CALNEW: {type(exc).__name__}: {exc}\n')

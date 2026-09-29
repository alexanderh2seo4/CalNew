"""Structured, calibrated predictions with explicit unavailable endpoints."""
from pathlib import Path
import joblib
import numpy as np

from .benchmark import predict_bundle
from .chemistry import identify,nearest_similarity
from .schema import PredictionRecord


def predict_records(run,smiles,endpoint=None,context=None):
    bundle=joblib.load(Path(run)/'model.joblib')
    endpoint=endpoint or bundle['endpoint']; context=context or {}
    records=[]
    for s in smiles:
        molecule=None
        try:
            molecule=identify(s)
            if endpoint!=bundle['endpoint']:
                raise ValueError(f'This run has no trained {endpoint} head')
            p,disagreement=predict_bundle(bundle,[s])
            if not np.isfinite(p).all(): raise ValueError('No finite prediction available')
            if bundle['task']=='classification': p=bundle['calibrator'].transform(p)
            estimates=dict(zip(bundle['labels'],p[0].tolist()))
            uncertainty={'model_disagreement':dict(zip(bundle['labels'],disagreement[0].tolist())),
                         'participant_variation':{'status':'unavailable','reason':'This run has no participant-level head'},
                         'measurement_variation':{'status':'unavailable','reason':'Not separately identifiable in this run'}}
            if bundle['task']=='regression':
                lo,hi=bundle['calibrator'].interval(p)
                uncertainty['prediction_interval']={label:{'coverage_target':.9,'lower':float(l) if np.isfinite(l) else None,'upper':float(h) if np.isfinite(h) else None,
                    'status':'available' if np.isfinite([l,h]).all() else 'unbounded_insufficient_calibration_groups'} for label,l,h in zip(bundle['labels'],lo[0],hi[0])}
            experts={name:np.mean([m.predict([s])[0] for m in models],axis=0).tolist() for name,models in bundle['models'].items()}
            records.append(PredictionRecord(molecule_id=molecule.molecule_id,smiles=s,endpoint=endpoint,status='available',context={**context,
                'prediction_conditions':bundle['metadata']['target_semantics'],'concentration_specific':False},estimates=estimates,uncertainty=uncertainty,
                applicability={'max_training_tanimoto':float(nearest_similarity([s],bundle['training_smiles'])[0]),'stereochemistry':molecule.stereo_status,
                               'shift_coverage_guarantee':False},
                provenance={'model_version':bundle['run_id'],'data':bundle['metadata'],'selected':bundle['selected'],'expert_outputs':experts,
                            'validation_status':'See run report; prospective validation is not implied'}).model_dump(mode='json'))
        except (ValueError,RuntimeError,ImportError,OSError) as exc:
            records.append(PredictionRecord(molecule_id=molecule.molecule_id if molecule else None,smiles=s,endpoint=endpoint,status='unavailable',reason=str(exc),context=context).model_dump(mode='json'))
    return records

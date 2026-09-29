import math
import pytest
from pydantic import ValidationError
from calnew.chemistry import identify
from calnew.schema import Observation,Endpoint
from calnew.units import to_ppbv,normalise_threshold,inverse_log_ppm_to_log_ppbv
from calnew.panel import threshold_bounds
from calnew.review import extraction_audit


def test_gas_conversion_and_matrix_separation():
    assert to_ppbv(.123,'mg/m3',molecular_weight=74.12,temperature_k=298.15,pressure_pa=101325)==pytest.approx(40.597,rel=.001)
    assert to_ppbv(.1,'ppmv')==100
    assert inverse_log_ppm_to_log_ppbv(2)==1
    assert normalise_threshold(1,'ug/L','water')==(-3,'log10(mg/L)')
    with pytest.raises(ValueError): to_ppbv(1,'mg/m3')
    with pytest.raises(ValueError): normalise_threshold(1,'ppbv','water')
    with pytest.raises(ValueError): normalise_threshold(0,'ppbv','air')


def test_stereo_identity_not_collapsed():
    a,b=identify('C[C@H](O)CC'),identify('C[C@@H](O)CC')
    assert a.molecule_id!=b.molecule_id and a.connectivity_id==b.connectivity_id
    assert identify('CC(O)CC').stereo_status=='unspecified'
    assert identify('CCO').stereo_status=='achiral'
    with pytest.raises(ValueError): identify('not-smiles')
    with pytest.raises(ValueError): identify('CCO.CCC')


def test_bounds_are_not_exact_values():
    common=dict(observation_id='x',molecule_id='m',stimulus_id='s',evidence_id='e',source_id='t',endpoint=Endpoint.AIR,raw_value='<1',unit='log10(ppbv)')
    assert Observation(**common,censoring='left',upper=0).value is None
    with pytest.raises(ValidationError): Observation(**common,censoring='left',upper=0,value=0)
    with pytest.raises(ValidationError): Observation(**common,censoring='interval',lower=1,upper=0)
    assert threshold_bounds([1,2,4],[1,1,1])['censoring']=='left'
    assert threshold_bounds([1,2,4],[0,0,0])['lower']==4
    r=threshold_bounds([1,2,4],[0,1,1]);assert r['censoring']=='interval' and r['value'] is None


def test_extraction_gate_counts_joint_exactness_and_missing_records():
    gold=[dict(observation_id=str(i),review_status='manually_verified',document_class='table',molecule_id='m',raw_value='1',raw_unit='ppbv',endpoint='air',matrix='air',provenance_location='table1',duplicate_of=None) for i in range(200)]
    prediction=[dict(r) for r in gold]
    assert extraction_audit(gold,prediction)['classes']['table']['automatic_acceptance']
    prediction[0]['raw_unit']='ppmv'
    assert not extraction_audit(gold,prediction[:-5])['classes']['table']['automatic_acceptance']
    assert not extraction_audit(gold[:10],prediction[:10])['classes']['table']['automatic_acceptance']
    gold[0]['review_status']='extractor_agreement'
    with pytest.raises(ValueError): extraction_audit(gold,prediction)

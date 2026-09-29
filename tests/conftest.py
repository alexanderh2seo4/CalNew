import numpy as np
import pytest
from calnew.chemistry import identify
from calnew.dataset import TaskDataset


@pytest.fixture
def toy_data():
    # Synthetic labels solely for software tests; never used as sensory evidence.
    smiles=['CCO','CCCO','CCCCO','CC(C)O','CC(C)CO','CC(C)(C)O','CCN','CCCN','CCCCN','CC(C)N',
            'CCS','CCCS','CCCCS','COC','CCOC','CCOCC','CCC','CCCC','CCCCC','CCCCCC',
            'CC=O','CCC=O','CCCC=O','CC(=O)C','CC(=O)CC','CC(=O)O','CCC(=O)O','CCOC(C)=O',
            'c1ccccc1','Cc1ccccc1','Oc1ccccc1','Nc1ccccc1','C1CCCCC1','C1CCCC1','C1CCOC1','c1ccncc1']
    molecules=[identify(s) for s in smiles]; y=np.array([m.molecular_weight/100 for m in molecules])[:,None]
    return TaskDataset(np.array([m.molecule_id for m in molecules]),smiles,np.array([m.connectivity_id for m in molecules]),
        y,['test_threshold'],'regression','air_detection_threshold',np.repeat('synthetic',len(y)),np.full_like(y,np.nan),np.full_like(y,np.nan),
        np.full(y.shape,'exact',object),{'snapshot_id':'synthetic-tests-only','unit':'log10(ppbv)'})

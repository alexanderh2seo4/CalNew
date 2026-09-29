from __future__ import annotations

from pathlib import Path

import joblib


class Model:
    def fit(self, dataset, split=None, configuration=None):
        raise NotImplementedError

    def predict(self, molecules, context=None):
        raise NotImplementedError

    def embed(self, molecules):
        raise NotImplementedError

    def calibrate(self, calibration_data):
        from ..calibration import GroupConformal, ProbabilityCalibrator
        p = self.predict(calibration_data.smiles)
        if calibration_data.task == "classification":
            self.calibrator = ProbabilityCalibrator().fit(calibration_data.y,p,calibration_data.groups)
        else:
            self.calibrator = GroupConformal().fit(calibration_data.y,p,calibration_data.groups)
        return self

    def evaluate(self, test_data):
        from ..metrics import evaluate
        return evaluate(test_data.y,self.predict(test_data.smiles),test_data.task,test_data.labels)

    def suggest_measurements(self,candidate_pool,batch_size,**kwargs):
        from ..active import suggest
        return suggest(candidate_pool,batch_size,**kwargs)

    def save(self, path: Path):
        """Only load artifacts produced by this trusted local run (joblib uses pickle)."""
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        joblib.dump(self,path)

import subprocess
import sys
from pathlib import Path


def test_bet_cli_preserves_censoring(tmp_path):
    log=tmp_path/'responses.csv'
    log.write_text('panelist,nominal_mg_m3,correct\nlow,1,1\nlow,2,1\nhigh,1,0\nhigh,2,0\ninterior,1,0\ninterior,2,1\n')
    script=Path(__file__).resolve().parents[1]/'olfactometer.py'
    output=subprocess.check_output([sys.executable,str(script),'bet',str(log)],text=True)
    assert 'left-censored' in output and 'right-censored' in output
    assert 'interior BET estimates only' in output
    assert 'derived midpoints' in output

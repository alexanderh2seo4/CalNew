@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_threshold_direction_benchmark.py --resume > threshold-resume-20261028.log 2> threshold-resume-20261028.err

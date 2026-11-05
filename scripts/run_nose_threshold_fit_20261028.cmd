@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_threshold_direction_fit.py > threshold-fit-20261028.log 2> threshold-fit-20261028.err

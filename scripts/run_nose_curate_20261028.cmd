@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_curate_release.py > curate-20261028.log 2> curate-20261028.err

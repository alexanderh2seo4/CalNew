@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_cooccurrence_refine.py > cooccurrence-20261028.log 2> cooccurrence-20261028.err

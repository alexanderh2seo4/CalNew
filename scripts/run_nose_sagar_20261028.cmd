@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_sagar_refine.py > sagar-refine-20261028.log 2> sagar-refine-20261028.err

@echo off
cd /d "%~dp0.."
python scripts\ssh_compute.py scripts\nose_compact_heads.py > compact-20261028.log 2> compact-20261028.err

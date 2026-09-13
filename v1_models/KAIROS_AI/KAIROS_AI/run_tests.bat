@echo off
title KAIROS AI - Unit Tests
echo =================================================================
echo   Running KAIROS AI Router Unit Tests (Offline / Mocked)
echo =================================================================
python -m unittest discover -s "%~dp0tests" -p "test_router.py" -v
pause


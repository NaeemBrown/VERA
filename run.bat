@echo off
title V.E.R.A. OS - TERMINAL LINK
color 0B

echo.
echo ==================================================
echo      INITIALIZING VIRTUAL ASSISTANT
echo ==================================================
echo.

:: This launches the interface. 
:: If it crashes, the 'pause' below keeps the window open so you can read the error.
python interface.py

echo.
echo [SYSTEM SHUTDOWN]
pause
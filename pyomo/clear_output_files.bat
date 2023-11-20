@echo off

cd output
set /P input= WARNING: Delete all content within %cd% and subfolders (y/n)? 

if %input%==y (del *.* /s /f /q) else (echo Script aborted.)

cd ..
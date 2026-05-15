@echo off

echo Setting up MSVC environment...

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"

REM 🔥 Remove Strawberry do PATH (importante)
set PATH=%PATH:C:\Strawberry\c\bin;=%

echo.
echo Checking tools...
where cl
where link
where ninja

echo.
echo Environment ready.
:: Copies python files from PythonClient to the sources location in the AndroidWrapper app

:: Goes to the root of the repository and defines paths relative to ROOT
cd ..
set ROOT=%cd%
set PYTHONCLIENT=PythonClient
set WRAPPERSOURCES=AndroidWrapper\app\src\main\python

:: Removes all the py files except main.py
cd %WRAPPERSOURCES%
for %%i in (*.py) do (
if not "%%i"=="main.py" del %%i
)

:: Copies all the py files except main.py
cd %ROOT%\%PYTHONCLIENT%
for %%i in (*.py) do (
if not "%%i"=="main.py" copy %%i %ROOT%\%WRAPPERSOURCES%
)
:: Also copies the password file in case it changes
copy password %ROOT%\%WRAPPERSOURCES%
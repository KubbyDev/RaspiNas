# RaspiNas
A simple NAS on a raspberry pi using a FTP server.

## Installation

On windows: 
```
schtasks /create /sc hourly /tn Tasks\SyncRaspiNas /tr "python F:\\GitHub\\RaspiNas\\PythonClient\\main.py"
```
Don't forget to put python in your Path environment variable or replace python by the path of your interpreter in the command
Also don't forget to put the right path for main.py

On linux:
```
```

On android:
```
```

## TODO:

Encrypt password
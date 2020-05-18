# RaspiNas
A simple NAS on a raspberry pi using a FTP server.
WARNING: This is not secure! The password is sent in plain text through the local network so it can be stolen. Also the files can be intercepted

## Installation

First, go to PythonClient and create a file named client.conf. You can use it to redefine config values. For a list of config values, see sync.py. If you want to place the config file elsewhere, you can either change it in the source code or give the path of the config file as parameter of the script when running it.

This repo only contains the client. You have to install a FTP server on your host and create a storage and a backup folder on its root.

You can automate the synchronization of the local directory by setting a scheduled task that runs main.py.

### On windows:
```
schtasks /create /sc hourly /tn Tasks\SyncRaspiNas /tr "cmd /c start /min F:\\GitHub\\RaspiNas\\PythonClient\\run.bat"
```
Don't forget to put python in your Path environment variable or replace python by the path of your interpreter in the run.bat file
Also don't forget to put the right path for run.bat

Then go to the task scheduler. A task named SyncRaspiNas should have appeared under Tasks. Edit it and check run whether the user is logged on or not and do not store password.

### On UNIX:
```
sudo -- sh -c 'echo "0 * * * * root cd /media/kubby/Data/GitHub/RaspiNas/PythonClient && python3 main.py" >> /etc/crontab'
```
Don't forget to replace /media/kubby/Data/GitHub/RaspiNas/PythonClient by the right path on your machine

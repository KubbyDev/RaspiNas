# RaspiNas
A simple NAS on a raspberry pi using a FTP server.

## Installation

First, go to PythonClient and create a file named client.conf. You can use it to redefine config values. For a list of config values, see main.py. If you want to place the config file elsewhere, you can either change it in the source code or give the path of the config file as parameter of the script when running it.

This repo only contains the client. You have to install a FTP server on your host and create a storage and a backup folder on its root.

You can automate the synchronisation of the local directory by setting a scheduled task that runs main.py.

### On windows: 
```
schtasks /create /sc hourly /tn Tasks\SyncRaspiNas /tr "python F:\\GitHub\\RaspiNas\\PythonClient\\main.py"
```
Don't forget to put python in your Path environment variable or replace python by the path of your interpreter in the command
Also don't forget to put the right path for main.py

### On UNIX:
```
sudo -- sh -c 'echo "* 1 * * * root cd /media/kubby/Data/GitHub/RaspiNas/PythonClient && python3 main.py" >> /etc/crontab'
```
Don't forget to replace /media/kubby..... by the right path on your machine

### On android:
```

```

## TODO:

Encrypt password

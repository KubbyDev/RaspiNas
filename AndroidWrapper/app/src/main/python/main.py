from os.path import dirname
import os
import sync

def launch():
    os.chdir(dirname(__file__))
    os.system("mkdir LocalPicDir")
    sync.main("client.conf")

# default working directory is /data/user/0/com.example.androidwrapper/files/chaquopy/AssetFinder/app
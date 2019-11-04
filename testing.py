from upload_and_setoff_workflows import process_runfolder,runfolder_object
import os
import re
import subprocess
import datetime
import smtplib
from email.message import Message
from shutil import copyfile
import requests
# import config file
import automate_demultiplex_config as config
# import function which reads the git tag
import git_tag as git_tag
from pprint import pprint

runfolder_obj=runfolder_object("abc123")
for i in vars(runfolder_obj):
    print len(vars(runfolder_obj))

class test():
    def __init__(self):
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))
    
    def main(self):
        print self.now
        print '{:%Y-%m-%d}'.format(datetime.datetime.now())
        classobj=process_runfolder("abc123", self.now)
        print classobj.test()
        

test().main()
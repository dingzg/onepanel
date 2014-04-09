#!/usr/bin/env python2.6
#-*- coding: utf-8 -*-
# Copyright [OnePanel]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pexpect
import subprocess
import re

#onepanel@oyyw.com [~]# crontab -l
#0 0 1 * * /.t
#onepanel@oyyw.com [~]# cat /etc/crontab
#SHELL=/bin/bash
#PATH=/sbin:/bin:/usr/sbin:/usr/bin
#MAILTO=root
#HOME=/
#
## run-parts
#49 * * * * root run-parts /etc/cron.hourly
#3 0 * * * root run-parts /etc/cron.daily
#24 2 * * 0 root run-parts /etc/cron.weekly
#20 0 27 * * root run-parts /etc/cron.monthly
#onepanel@oyyw.com [~]#
system_crontab='/etc/crontab'
cronfiles_dir='/etc/cron.d'
user_dir='/var/spool/cron'

def listcron(username):
	arr_cron=[]
	#read the master crontab file
	readcron(system_crontab,"sys")

	#read package-specific cron files
	files = os.listdir(cronfiles_dir)
	for filename in files:
        readcron(cronfiles_dir+'/'+filename,"spec")

    #Read a single user's crontab file

    return arr_cron
# 
def readcron(filename,option):
    with open(filename) as f:
        for line in f:
            line=line.replace('\r','')
            line=line.replace('\n','')
            if re.findall("^\d|^\*|^\-",line):
                text= re.split("\s+",line,5)
                t_min=text[0]
                t_hour=text[1]
                t_dayofmon=text[2]
                t_month=text[3]
                t_dayofweek=text[4]
                #t_user=text[5]
                t_cmd=text[5]
                arr_cron.append(text)

def runshell(pw_cmd):
    try:
        p = subprocess.Popen(pw_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
        result = p.stdout.read()
    except:
        result = 'command error'
    return result

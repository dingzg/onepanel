#!/usr/bin/env python2.6
#-*- coding: utf-8 -*-
# Copyright [OnePanel]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
####################################################################################################
# Script Name	   : task.py
# Function Summary  : read cron
#					 1.listcron
#					 2.readcron
# Parameters		: None
# Return Code	   : None
# Note			  : None
####################################################################################################
# Update History
# Date			  Author			 Reason
# ________________  _________________ ______________________________________________________________
# 2014/04/09		Chen DengYue	   Create
import os
import sys
import pexpect
import subprocess
import re

system_crontab='/etc/crontab'
cronfiles_dir='/etc/cron.d'
user_dir='/var/spool/cron'
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
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : listcron
#Usage			  : 
#Parameters		 : 
#					 1 current user name
#Return value	   :
#					 1 cron task list
#---------------------------------------------------------------------------------------------------
def listcron(username):

	cronlist=readcron(user_dir+'/'+username,'other')

	####read the master crontab file
	#readcron(system_crontab,"sys")

	###read package-specific cron files
	#files = os.listdir(cronfiles_dir)
	#for filename in files:
	#	readcron(cronfiles_dir+'/'+filename,"user")

	#Read a single user's crontab file
	#readcron(user_dir+'/'+username,"none")
	return cronlist
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : readcron
#Usage			  : 
#Parameters		 : 
#					 1 file name with path
#					 2 cron type:has USER in file or not .user:with USER;other:without USER
#Return value	   : None  
#---------------------------------------------------------------------------------------------------
def readcron(filename,option):
	cronlist=[]
	with open(filename) as f:
		i=0
		for line in f:
			line=line.replace('\r','')
			line=line.replace('\n','')
			if re.findall("^\d|^\*|^\-",line):
				if option == "other":
					text= re.split("\s+",line,5)
					t_cmd=text[5]
					#t_user="None"
				else:
					text= re.split("\s+",line,6)
					t_user=text[5]
					t_cmd=text[6]
				t_min=text[0]
				t_hour=text[1]
				t_dayofmon=text[2]
				t_month=text[3]
				t_dayofweek=text[4]
				i=i+1
				cronlist.append(i,text)
		####for multiple cron file
		#		arr_cron.append([filename,arr])
		#print 'arr:',arr_cron
	return cronlist
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : addcron
#Usage			  : 
#Parameters		 : 
#					 1 current user name
#					  2 command
#Return value	   :
#					 1 cron task list
#---------------------------------------------------------------------------------------------------
def addcron(username,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd):
	arr_cron=[]
	####read the master crontab file
	#readcron(system_crontab,"sys")

	###read package-specific cron files
	#files = os.listdir(cronfiles_dir)
	#for filename in files:
	#	readcron(cronfiles_dir+'/'+filename,"user")

	#Read a single user's crontab file
	#readcron(user_dir+'/'+username,"none")
	#return arr_cron
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : modcron
#Usage			  : 
#Parameters		 : 
#					 1 current user name
#					  2 command
#Return value	   :
#					 1 cron task list
#---------------------------------------------------------------------------------------------------
def modcron(username,t_id,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd):
	print 'modcron'
	#arr_cron=[]
	####read the master crontab file
	#readcron(system_crontab,"sys")

	###read package-specific cron files
	#files = os.listdir(cronfiles_dir)
	#for filename in files:
	#	readcron(cronfiles_dir+'/'+filename,"user")

	#Read a single user's crontab file
	#readcron(user_dir+'/'+username,"none")
	#return arr_cron
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : delcron
#Usage			  : 
#Parameters		 : 
#					 1 current user name
#					  2 command
#Return value	   :
#					 1 cron task list
#---------------------------------------------------------------------------------------------------
def delcron(username,t_id):
	print 'delcron'
	#arr_cron=[]
	####read the master crontab file
	#readcron(system_crontab,"sys")

	###read package-specific cron files
	#files = os.listdir(cronfiles_dir)
	#for filename in files:
	#	readcron(cronfiles_dir+'/'+filename,"user")

	#Read a single user's crontab file
	#readcron(user_dir+'/'+username,"none")
	#return arr_cron
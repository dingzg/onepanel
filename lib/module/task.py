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
# Script Name	    : task.py
# Function Summary  : 1 readcron
#					  2 listcron
#					  3 addcron
#					  4 modcron
#					  5 delcron
# Parameters		: None
# Return Code	    : None
# Note			    : None
####################################################################################################
# Update History
# Date			  Author			 Reason
# ________________  _________________ ______________________________________________________________
# 2014/04/09		Chen DengYue	   Create
import re

system_crontab='/etc/crontab'
cronfiles_dir='/etc/cron.d'
user_dir='/var/spool/cron'

#---------------------------------------------------------------------------------------------------
#Function Name	  : main_cron
#Usage			  : 
#Parameters		  : 
#					 1 
#Return value	  :
#					 1 
#---------------------------------------------------------------------------------------------------
def main_process(self):
    action = self.get_argument('action', '')
    #get user name from config.ini
    username = self.config.get('auth', 'username')

    if action == 'list':
        self.write({'code': 0, 'msg': 'Excute Successfully', 'data': listcron(username)}) 
    elif action in ('add', 'mod'):
        t_minute = self.get_argument('minute', '')
        t_hour = self.get_argument('hour', '')
        t_day = self.get_argument('dayofmon', '')
        t_month = self.get_argument('month', '')
        t_weekday = self.get_argument('dayofweek', '')
        t_cmd = self.get_argument('cmd', '')
        if action == 'add':
            self.write({'code': 0, 'msg': 'Excute Successfully', 'data': addcron(username,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd)}) 
        elif action == 'mod':
            t_id = self.get_argument('id', '')
            self.write({'code': 0, 'msg': 'Excute Successfully', 'data': modcron(username,t_id,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd)})   
    elif action == 'del':
        t_id = self.get_argument('id', '')
        self.write({'code': 0, 'msg': 'Excute Successfully', 'data': delcron(username,t_id)}) 
    return
#---------------------------------------------------------------------------------------------------
#Function Name	  : listcron
#Usage			  : 
#Parameters		  : 
#					 1 user name
#Return value	  :
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
#Parameters		  : 
#					 1 file name with path
#					 2 cron type:has USER in file or not .user:with USER;other:without USER
#Return value	  : None  
#---------------------------------------------------------------------------------------------------
def readcron(filename,option):
	cronlist=[]
	with open(filename) as f:
		i=0
		for line in f:
			line = line.strip()
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
				#for Desktop Version
				#cronlist.append([i,text])
				#for Web Version Add-start
				cron={'id':i,'minute':t_min,'hour':t_hour,'dayofmon':t_dayofmon,'month':t_month,'dayofweek':t_dayofweek,'cmd':t_cmd}
				cronlist.append(cron)
				
				#for Web Version Add-end
		####for multiple cron file
		#		arr_cron.append([filename,arr])
		#print 'arr:',arr_cron
	return cronlist
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : addcron
#Usage			  : 
#Parameters		  : 
#					 1 user name
#					 2 minute
#					 3 hour
#					 4 day
#					 5 month
#					 6 weekday
#					 7 command
#Return value	  :
#					 1 message
#---------------------------------------------------------------------------------------------------
def addcron(username,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd):
	t_content=t_minute+' '+t_hour+' '+t_day+' '+t_month+' '+t_weekday+' '+t_cmd+"\n"
	with open(user_dir+'/'+username,'a+') as f:
		f.write(t_content)
	return "Add Cron Successfully"
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : modcron
#Usage			  : 
#Parameters		  : 
#					 1 user name
#					 2 id
#					 3 minute
#					 4 hour
#					 5 day
#					 6 month
#					 7 weekday
#					 8 command
#Return value	  :
#					 1 message
#---------------------------------------------------------------------------------------------------
def modcron(username,t_id,t_minute,t_hour,t_day,t_month,t_weekday,t_cmd):
	t_content=t_minute+' '+t_hour+' '+t_day+' '+t_month+' '+t_weekday+' '+t_cmd+"\n"
	with open(user_dir+'/'+username,'r') as f:
		lines=f.readlines()

	i=0
	j=0
	for line in lines:
		j=j+1
		if re.findall("^\d|^\*|^\-",line):
			i=i+1
			if str(i) == str(t_id):
				lines[j-1]=t_content
				break

	with open(user_dir+'/'+username,'w+') as f:
		f.writelines(lines)

	return "Modify Cron Successfully"
#
#---------------------------------------------------------------------------------------------------
#Function Name	  : delcron
#Usage			  : 
#Parameters		  : 
#					 1 user name
#					 2 id
#Return value	  :
#					 1 message
#---------------------------------------------------------------------------------------------------
def delcron(username,t_id):
	with open(user_dir+'/'+username,'r') as f:
		lines=f.readlines()

	i=0
	j=0
	for line in lines:
		j=j+1
		if re.findall("^\d|^\*|^\-",line):
			i=i+1
			if str(i) == str(t_id):
				del lines[j-1]
				break

	with open(user_dir+'/'+username,'w+') as f:
		f.writelines(lines)

	return "Delete Cron Successfully"

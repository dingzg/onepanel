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
# Script Name		: apache.py
# Function Summary  : 1 getSettings
#					  2 modifyConfig
# Parameters		: None
# Return Code		: None
# Note				: None
####################################################################################################
# Update History
# Date			  Author			 Reason
# ________________  _________________ ______________________________________________________________
# 2014/05/14		Chen DengYue	   Create
from utils import cfg_get_array, cfg_set_array

config_file='/etc/httpd/conf/httpd.conf'
delimiter='\s+'

base_configs = {
	'ServerRoot': '',
	'PidFile': '',
	'ServerName': '',
	'AddDefaultCharset': '',
	'Timeout': '',
	'KeepAlive': '',
	'MaxKeepAliveRequests': '',
	'KeepAliveTimeout': '',
	'Listen': '',
	'ServerAdmin': '',
}

#---------------------------------------------------------------------------------------------------
#Function Name	  : main_process
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1  
#---------------------------------------------------------------------------------------------------
def main_process(self):
    action = self.get_argument('action', '')
    if action == 'getsettings':
        self.write({'code': 0, 'msg': '获取 Apache 配置信息成功！', 'data': loadApacheConfigs()})
    elif action == 'mod':
        self.write({'code': 0, 'msg': 'Apache 服务配置保存成功！','data': modApacheConfigs(self)})
    elif action == 'getsubhttpsetting':
        self.write({'code': 0, 'msg': 'Apache 服务配置保存成功！','data': loadSubHttpApacheConfigs(self)})
    return
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : loadApacheConfigs
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1  array_configs
#---------------------------------------------------------------------------------------------------
def loadApacheConfigs():
	array_configs=cfg_get_array(config_file,base_configs,delimiter)
	return array_configs
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : modApacheConfigs
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1 
#---------------------------------------------------------------------------------------------------
def modApacheConfigs(self):
	result=cfg_set_array(self,config_file,base_configs,delimiter)
	return result
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : loadSubHttpApacheConfigs
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1 
#---------------------------------------------------------------------------------------------------
def loadSubHttpApacheConfigs(self):
	print('Debug')



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
from utils import cfg_get, cfg_set,loadconfig

config_file='/etc/httpd/conf/httpd.conf'

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
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : loadApacheConfigs
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1  base_configs
#---------------------------------------------------------------------------------------------------
def loadApacheConfigs():
	q_keys=base_configs.keys()
	for  key in q_keys:
		q_value=cfg_get(config_file,key)
		base_configs[key]=q_value
	return base_configs
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
	q_keys=base_configs.keys()
	for  key in q_keys:
		q_value = self.get_argument(key, '')
		if q_value: cfg_set(config_file,key, q_value)
	return True

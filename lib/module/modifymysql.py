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

config_file='/etc/my.cnf'
delimiter='='

base_configs = {
	'user': '',
	'datadir': '',
	'socket': '',
}

# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : loadApacheConfigs
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1  array_configs
#---------------------------------------------------------------------------------------------------
def loadMySQLConfigs():
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
def modMySQLConfigs(self):
	result=cfg_set_array(self,config_file,base_configs,delimiter)
	return result

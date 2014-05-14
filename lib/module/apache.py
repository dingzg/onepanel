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
import re
#from utils import cfg_get, cfg_set,loadconfig

config_file='/etc/httpd/conf/httpd.conf'
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : loadconfig
#Usage			  : 
#Parameters		  : None
#					 
#Return value	  :
#					 1 
#---------------------------------------------------------------------------------------------------
def loadconfig(cfgfile=None,detail=False):
	if not cfgfile: cfgfile = config_file

	settings = {}

	with open(cfgfile) as f:
		for line_i, line in enumerate(f):
			line = line.strip()
			if not line or line.startswith('# '): continue
			
			# detect if it's commented
			if line.startswith('#'):
				line = line.strip('#')
				commented = True
				if not detail: continue
			else:
				commented = False

			fs = re.split('\s+', line, 1)
			if len(fs) != 2: continue

			item = fs[0].strip()
			value = fs[1].strip()

			if settings.has_key(item):
				if detail: count = settings[item]['count']+1
				if not commented:
					settings[item] = detail and {
						'file': cfgfile,
						'line': line_i,
						'value': value,
						'commented': commented,
					} or value
			else:
				count = 1
				settings[item] = detail and {
					'file': cfgfile,
					'line': line_i,
					'value': fs[1].strip(),
					'commented': commented,
				} or value
			if detail: settings[item]['count'] = count
	#print settings
	return settings
# 
#---------------------------------------------------------------------------------------------------
#Function Name	  : cfg_set
#Usage			  : 
#Parameters		  : 
#Return value	  :   
#---------------------------------------------------------------------------------------------------
def cfg_set(item, value, commented=False, config=None):
	cfgfile = config_file
	v = cfg_get(item, detail=True, config=config)

	if v:
		# detect if value change
		if v['commented'] == commented and v['value'] == value: return True
		
		# empty value should be commented
		if value == '': commented = True

		# replace item in line
		lines = []
		with open(v['file']) as f:
			for line_i, line in enumerate(f):
				if line_i == v['line']:
					if not v['commented']:
						if commented:
							if v['count'] > 1:
								# delete this line, just ignore it
								pass
							else:
								# comment this line
								lines.append('#%s %s\n' % (item, value))
						else:
							lines.append('%s %s\n' % (item, value))
					else:
						if commented:
							# do not allow change comment value
							lines.append(line)
							pass
						else:
							# append a new line after comment line
							lines.append(line)
							lines.append('%s %s\n' % (item, value))
				else:
					lines.append(line)
		with open(v['file'], 'w') as f: f.write(''.join(lines))
	else:
		# append to the end of file
		with open(inifile, 'a') as f:
			f.write('\n%s%s = %s\n' % (commented and '#' or '', item, value))
	
	return True
#
def cfg_get(item, detail=False, config=None):
	"""Get value of a config item.
	"""
	if not config: config = loadconfig(detail=detail)
	if config.has_key(item):
		return config[item]
	else:
		return None
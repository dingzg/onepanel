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


"""Operation of chkconfig in redhat/centos.
"""

import os
import shlex
import subprocess
#---------------------------------------------------------------------------------------------------
#Function Name    : main_process
#Usage            : 
#Parameters       : None
#                    
#Return value     :
#                    1  
#---------------------------------------------------------------------------------------------------
def main_process(self):
    name = self.get_argument('name', '')
    service = self.get_argument('service', '')
    autostart = self.get_argument('autostart', '')
    if not name: name = service
    
    autostart_str = {'on': u'启用', 'off': u'禁用'}
    if set(_u(service), autostart == 'on' and True or False):
        self.write({'code': 0, 'msg': u'成功%s %s 自动启动！' % (autostart_str[autostart], name)})
    else:
        self.write({'code': -1, 'msg': u'%s %s 自动启动失败！' % (autostart_str[autostart], name)})
    
def set(service, autostart=True):
	"""Add or remove service to autostart list.
	"""
	if autostart:
		cmd = 'chkconfig %s on' % service
	else:
		cmd = 'chkconfig %s off' % service
	p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, close_fds=True)
	p.stdout.read()
	return p.wait() == 0 and True or False
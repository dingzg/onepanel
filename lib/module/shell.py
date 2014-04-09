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
#
####################################################################################################
# Script Name       : shell.py
# Function Summary  : read cron
#                     1.runshell
# Parameters        : None
# Return Code       : None
# Note              : None
####################################################################################################
# Update History
# Date              Author             Reason
# ________________  _________________ ______________________________________________________________
# 2014/04/09        Chen DengYue       Create
import os
import sys
import pexpect
import subprocess
import re

#---------------------------------------------------------------------------------------------------
#Function Name      : executeshell
#Usage              : 
#Parameters         : 
#                     1 shell command
#Return value       :
#                     1 result
#---------------------------------------------------------------------------------------------------
def executeshell(pw_cmd):
    try:
        p = subprocess.Popen(pw_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
        result = p.stdout.read()
    except:
        result = 'command error'
    return result

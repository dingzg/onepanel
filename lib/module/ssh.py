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



"""Package for ssh operations.
"""

import os
if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import re
import pexpect
import shlex
from utils import cfg_get, cfg_set

cfgfile = '/etc/ssh/sshd_config'
delimiter='\s+'
#---------------------------------------------------------------------------------------------------
#Function Name    : main_process
#Usage            : 
#Parameters       : None
#                    
#Return value     :
#                    1  
#---------------------------------------------------------------------------------------------------
def main_process(self):
    #cfg_set(cfgfile, key, q_value, delimiter)
    action = self.get_argument('action', '')

    if action == 'getsettings':
        port = cfg_get(cfgfile,'Port',delimiter)
        enable_pwdauth = cfg_get(cfgfile,'PasswordAuthentication',delimiter) == 'yes'
        enable_pubkauth = cfg_get(cfgfile,'PubkeyAuthentication',delimiter) == 'yes'
        subsystem = cfg_get(cfgfile,'Subsystem',delimiter)
        enable_sftp = subsystem and 'sftp' in subsystem
        pubkey_path = '/root/.ssh/sshkey_onepanel.pub'
        prvkey_path = '/root/.ssh/sshkey_onepanel'
        self.write({'code': 0, 'msg': '获取 SSH 服务配置信息成功！', 'data': {
           'port': port,
           'enable_pwdauth': enable_pwdauth,
           'enable_pubkauth': enable_pubkauth,
           'enable_sftp': enable_sftp,
           'pubkey': os.path.isfile(pubkey_path) and pubkey_path or '',
           'prvkey': os.path.isfile(prvkey_path) and prvkey_path or '',
        }})

    elif action == 'savesettings':
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许修改 SSH 服务设置！'})
            return

        port = self.get_argument('port', '')
        if port: cfg_set(cfgfile,'Port', port,delimiter)
        enable_pwdauth = self.get_argument('enable_pwdauth', '')
        if enable_pwdauth: cfg_set(cfgfile,'PasswordAuthentication', enable_pwdauth=='on' and 'yes' or 'no',delimiter)
        enable_pubkauth = self.get_argument('enable_pubkauth', '')
        if enable_pubkauth:
            if enable_pubkauth == 'on':
                pubkey_path = self.get_argument('pubkey', '')
                if not os.path.isfile(pubkey_path):
                    self.write({'code': -1, 'msg': u'公钥文件不存在！'})
                    return
            cfg_set(cfgfile,'PubkeyAuthentication', enable_pubkauth=='on' and 'yes' or 'no',delimiter)
            cfg_set(cfgfile,'AuthorizedKeysFile', pubkey_path,delimiter)

        enable_sftp = self.get_argument('enable_sftp', '')
        if enable_sftp: cfg_set(cfgfile,'Subsystem', 'sftp /usr/libexec/openssh/sftp-server', enable_sftp!='on',delimiter)
        self.write({'code': 0, 'msg': 'SSH 服务配置保存成功！'})
#
def genkey(path, password=''):
    """Generate a ssh key pair.
    """
    cmd = shlex.split('ssh-keygen -t rsa')
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter file in which to save the key', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(path)
    i = child.expect(['Overwrite', 'Enter passphrase', pexpect.EOF])
    if i == 0:
        child.sendline('y')
        i = child.expect(['Enter passphrase', pexpect.EOF])
        if i == 1:
            if child.isalive(): child.wait()
            return False
    elif i == 2:
        if child.isalive(): child.wait()
        return False

    child.sendline(password)
    i = child.expect(['Enter same passphrase', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(password)
    child.expect(pexpect.EOF)

    if child.isalive():
        return child.wait() == 0
    return True

def chpasswd(path, oldpassword, newpassword):
    """Change password of a private key.
    """
    if len(newpassword) != 0 and not len(newpassword) > 4: return False

    cmd = shlex.split('ssh-keygen -p')
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter file in which the key is', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(path)
    i = child.expect(['Enter old passphrase', 'Enter new passphrase', pexpect.EOF])
    if i == 0:
        child.sendline(oldpassword)
        i = child.expect(['Enter new passphrase', 'Bad passphrase', pexpect.EOF])
        if i != 0:
            if child.isalive(): child.wait()
            return False
    elif i == 2:
        if child.isalive(): child.wait()
        return False

    child.sendline(newpassword)
    i = child.expect(['Enter same passphrase again', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(newpassword)
    child.expect(pexpect.EOF)

    if child.isalive():
        return child.wait() == 0
    return True


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    
    #pp.pprint(loadconfig())
    #print cfg_get('Port')
    #print cfg_get('Subsystem', detail=True)
    #print cfg_set('Protocol', '2', commented=False)
    #print cfg_set('Subsystem', 'sftp\t/usr/libexec/openssh/sftp-server', commented=True)
    
    #print genkey('/root/.ssh/sshkey_onepanel')
    #print chpasswd('/root/.ssh/sshkey_onepanel', '', 'aaaaaa')
    
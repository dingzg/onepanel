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


"""Package for user management.
"""

import os
if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import pexpect
import shlex
import time
import pwd
import grp
import subprocess
from utils import b2h, ftime
#---------------------------------------------------------------------------------------------------
#Function Name    : main_process
#Usage            : 
#Parameters       : None
#                    
#Return value     :
#                    1  
#---------------------------------------------------------------------------------------------------
def main_process(self):
    action = self.get_argument('action', '')

    if action == 'listuser':
        fullinfo = self.get_argument('fullinfo', 'on')
        self.write({'code': 0, 'msg': u'成功获取用户列表！', 'data': listuser(fullinfo=='on')})

    elif action == 'listgroup':
        fullinfo = self.get_argument('fullinfo', 'on')
        self.write({'code': 0, 'msg': u'成功获取用户组列表！', 'data': listgroup(fullinfo=='on')})

    elif action in ('useradd', 'usermod'):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许添加和修改用户！'})
            return

        pw_name = self.get_argument('pw_name', '')
        pw_gecos = self.get_argument('pw_gecos', '')
        pw_gname = self.get_argument('pw_gname', '')
        pw_dir = self.get_argument('pw_dir', '')
        pw_shell = self.get_argument('pw_shell', '')
        pw_passwd = self.get_argument('pw_passwd', '')
        pw_passwdc = self.get_argument('pw_passwdc', '')
        lock = self.get_argument('lock', '')
        lock = (lock == 'on') and True or False
        
        if pw_passwd != pw_passwdc:
            self.write({'code': -1, 'msg': u'两次输入的密码不一致！'})
            return
        
        options = {
            'pw_gecos': _u(pw_gecos),
            'pw_gname': _u(pw_gname),
            'pw_dir': _u(pw_dir),
            'pw_shell': _u(pw_shell),
            'lock': lock
        }
        if len(pw_passwd)>0: options['pw_passwd'] = _u(pw_passwd)

        if action == 'useradd':
            createhome = self.get_argument('createhome', '')
            createhome = (createhome == 'on') and True or False
            options['createhome'] = createhome
            if useradd(_u(pw_name), options):
                self.write({'code': 0, 'msg': u'用户添加成功！'})
            else:
                self.write({'code': -1, 'msg': u'用户添加失败！'})
        elif action == 'usermod':
            if usermod(_u(pw_name), options):
                self.write({'code': 0, 'msg': u'用户修改成功！'})
            else:
                self.write({'code': -1, 'msg': u'用户修改失败！'})

    elif action == 'userdel':
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许删除用户！'})
            return

        pw_name = self.get_argument('pw_name', '')
        if userdel(_u(pw_name)):
            self.write({'code': 0, 'msg': u'用户删除成功！'})
        else:
            self.write({'code': -1, 'msg': u'用户删除失败！'})

    elif action in ('groupadd', 'groupmod', 'groupdel'):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许操作用户组！'})
            return

        gr_name = self.get_argument('gr_name', '')
        gr_newname = self.get_argument('gr_newname', '')
        actionstr = {'groupadd': u'添加', 'groupmod': u'修改', 'groupdel': u'删除'};

        if action == 'groupmod':
            rt = groupmod(_u(gr_name), _u(gr_newname))
        else:
            rt = getattr(user, action)(_u(gr_name))
        if rt:
            self.write({'code': 0, 'msg': u'用户组%s成功！' % actionstr[action]})
        else:
            self.write({'code': -1, 'msg': u'用户组%s失败！' % actionstr[action]})

    elif action in ('groupmems_add', 'groupmems_del'):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许操作用户组成员！'})
            return

        gr_name = self.get_argument('gr_name', '')
        mem = self.get_argument('mem', '')
        option = action.split('_')[1]
        optionstr = {'add': u'添加', 'del': u'删除'}
        if groupmems(_u(gr_name), _u(option), _u(mem)):
            self.write({'code': 0, 'msg': u'用户组成员%s成功！' % optionstr[option]})
        else:
            self.write({'code': -1, 'msg': u'用户组成员%s成功！' % optionstr[option]})
def listuser(fullinfo=True):
    if fullinfo:
        # get lock status from /etc/shadow
        locks = {}
        with open('/etc/shadow') as f:
            for line in f:
                fields = line.split(':', 2)
                locks[fields[0]] = fields[1].startswith('!')
        users = pwd.getpwall()
        for i, user in enumerate(users):
            users[i] = dict((name, getattr(user, name))
                            for name in dir(user)
                            if not name.startswith('__'))
            try:
                gname = grp.getgrgid(user.pw_gid).gr_name
            except:
                gname = ''
            users[i]['pw_gname'] = gname
            users[i]['lock'] = locks[user.pw_name]
    else:
        users = [pw.pw_name for pw in pwd.getpwall()]
    return users


def passwd(username, password):
    try:
        cmd = shlex.split('passwd \'%s\'' % username)
    except:
        return False
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['New password', 'Unknown user name'])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    child.sendline(password)
    child.expect('Retype new password')
    child.sendline(password)
    i = child.expect(['updated successfully', pexpect.EOF])
    if child.isalive(): child.wait()
    return i == 0


def useradd(username, options):
    # command like: useradd -c 'New User' -g newgroup -s /bin/bash -m newuser
    cmd = ['useradd']
    if options.has_key('pw_gname') and options['pw_gname']:
        cmd.extend(['-g', options['pw_gname']])
    if options.has_key('pw_gecos'):
        cmd.extend(['-c', options['pw_gecos']])
    if options.has_key('pw_shell'):
        cmd.extend(['-s', options['pw_shell']])
    if options.has_key('createhome') and options['createhome']:
        cmd.append('-m')
    else:
        cmd.append('-M')
    cmd.append(username)
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    if p.wait() != 0: return False
    
    # check if need to lock/unlock the new account
    if options.has_key('lock') and options['lock']:
        if not usermod(username, {'lock': options['lock']}): return False

    # check if need to set passwd
    if options.has_key('pw_passwd'):
        if not passwd(username, options['pw_passwd']): return False
    
    return True


def usermod(username, options):
    user = pwd.getpwnam(username)
    # command like: usermod -c 'I am root' -g root -d /root/ -s /bin/bash -U root
    cmd = ['usermod']
    if options.has_key('pw_gname'):
        cmd.extend(['-g', options['pw_gname']])
    if options.has_key('pw_gecos') and options['pw_gecos'] != user.pw_gecos:
        cmd.extend(['-c', options['pw_gecos']])
    if options.has_key('pw_dir') and options['pw_dir'] != user.pw_dir:
        cmd.extend(['-d', options['pw_dir']])
    if options.has_key('pw_shell') and options['pw_shell'] != user.pw_shell:
        cmd.extend(['-s', options['pw_shell']])
    if options.has_key('lock') and options['lock']:
        cmd.append('-L')
    else:
        cmd.append('-U')
    cmd.append(username)
    if len(cmd) > 2:
        p = subprocess.Popen(cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p.stdout.read()
        msg = p.stderr.read()
        if p.wait() != 0:
            if not 'no changes' in msg:
                return False

    # check if need to change passwd
    if options.has_key('pw_passwd'):
        if not passwd(username, options['pw_passwd']): return False

    return True
        

def userdel(username):
    p = subprocess.Popen(['userdel', username],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def listgroup(fullinfo=True):
    if fullinfo:
        groups = grp.getgrall()
        for i, group in enumerate(groups):
            groups[i] = dict((name, getattr(group, name))
                            for name in dir(group)
                            if not name.startswith('__'))
    else:
        groups = [gr.gr_name for gr in grp.getgrall()]
    return groups


def groupadd(groupname):
    p = subprocess.Popen(['groupadd', groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupmod(groupname, newgroupname):
    p = subprocess.Popen(['groupmod', '-n', newgroupname, groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupdel(groupname):
    p = subprocess.Popen(['groupdel', groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupmems(groupname, option, mem):
    cmd = ['groupmems', '-g', groupname]
    if option == 'add':
        cmd.extend(['-a', mem])
    elif option == 'del':
        cmd.extend(['-d', mem])
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0

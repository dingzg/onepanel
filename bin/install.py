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


""" Install script for OnePanel """

import os
import sys
import platform
import shlex
import subprocess
import urllib2
import re
import socket

class Install(object):

    def __init__(self):
        if hasattr(platform, 'linux_distribution'):
            self.dist = platform.linux_distribution(full_distribution_name=0)
        else:
            self.dist = platform.dist()
        self.arch = platform.machine()
        if self.arch != 'x86_64': self.arch = 'i386'
        self.installpath = '/usr/local/onepanel'
        self.distname = self.dist[0].lower()
        self.version = self.dist[1]
        
    def _run(self, cmd, shell=False):
        if shell:
            return subprocess.call(cmd, shell=shell)
        else:
            return subprocess.call(shlex.split(cmd))
        
    def check_platform(self):
        supported = True
        if self.distname == 'centos':
            if float(self.version) < 5.4:
                supported = False
        elif self.distname == 'redhat':
            if float(self.version) < 5.4:
                supported = False
        #elif self.distname == 'ubuntu':
        #    if float(self.version) < 10.10:
        #        supported = False
        #elif self.distname == 'debian':
        #    if float(self.version) < 6.0:
        #        supported = False
        else:
            supported = False
        return supported
    
    def install_python(self):
        if self.distname in ('centos', 'redhat'):
            # following this: http://fedoraproject.org/wiki/EPEL/FAQ
            if int(float(self.version)) == 5:
                epelrpm = 'epel-release-5-4.noarch.rpm'
                epelurl = 'http://download.fedoraproject.org/pub/epel/5/%s/%s' % (self.arch, epelrpm)
                # install fastestmirror plugin for yum
                fastestmirror = 'http://mirror.centos.org/centos/5/os/%s/CentOS/yum-fastestmirror-1.1.16-21.el5.centos.noarch.rpm' % (self.arch, )
            elif int(float(self.version)) == 6:
                epelrpm = 'epel-release-6-7.noarch.rpm'
                epelurl = 'http://download.fedoraproject.org/pub/epel/6/%s/' % (self.arch, epelrpm)
                fastestmirror = 'http://mirror.centos.org/centos/6/os/%s/Packages/yum-plugin-fastestmirror-1.1.30-14.el6.noarch.rpm' % (self.arch, )
            self._run('wget -nv -c %s' % epelurl)
            self._run('rpm -Uvh %s' % epelrpm)
            self._run('rpm -Uvh %s' % fastestmirror)
            self._run('yum -y install python26')

        if self.distname == 'centos':
            pass
        elif self.distname == 'redhat':
            pass
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def install_onepanel(self):
        localpkg_found = False
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'onepanel.tar.gz')):
            # local install package found
            localpkg_found = True
        else:
            # or else install online
            print '* Downloading install package from www.onepanel.org'
            f = urllib2.urlopen('http://www.onepanel.org/api/latest')
            data = f.read()
            f.close()
            downloadurl = re.search('"download":"([^"]+)"', data).group(1).replace('\/', '/')
            self._run('wget -nv -c "%s" -O onepanel.tar.gz' % downloadurl)
            
        # uncompress and install it
        self._run('mkdir onepanel')
        self._run('tar zxmf onepanel.tar.gz -C onepanel')
        if not localpkg_found: os.remove('onepanel.tar.gz')
        
        # stop service
        print
        if os.path.exists('/etc/init.d/onepanel'):
            self._run('/etc/init.d/onepanel stop')

        # backup data and remove old code
        if os.path.exists('%s/data/' % self.installpath):
            self._run('cp -r %s/data/* onepanel/data/' % self.installpath, True)
        self._run('rm -rf %s' % self.installpath)
        
        # install new code
        self._run('mv onepanel %s' % self.installpath)
        self._run('chmod +x %s/install_config.py %s/start_server.py' % (self.installpath, self.installpath))
        
        # install service
        initscript = '%s/tools/init.d/%s/onepanel' % (self.installpath, self.distname)
        self._run('cp %s /etc/init.d/onepanel' % initscript)
        self._run('chmod +x /etc/init.d/onepanel')
        
        # start service
        if self.distname in ('centos', 'redhat'):
            self._run('chkconfig onepanel on')
            self._run('service onepanel start')
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def config(self, username, password):
        self._run('%s/install_config.py username "%s"' % (self.installpath, username))
        self._run('%s/install_config.py password "%s"' % (self.installpath, password))
        
    def detect_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('www.baidu.com', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def install(self):
        # check platform environment
        print '* Checking platform...',
        supported = self.check_platform()
        
        if not supported:
            print 'FAILED'
            print 'Unsupport platform %s %s %s' % self.dist
            sys.exit()
        else:
            print 'OK'

        # check python version
        print '* Checking python version ...',
        if sys.version_info[:2] == (2, 6):
            print 'OK'
        else:
            print 'FAILED'

            # install the right version
            print '* Installing python 2.6 ...'
            self.install_python()

        # stop firewall
        if os.path.exists('/etc/init.d/iptables'):
            self._run('/etc/init.d/iptables stop')
        
        # get the latest onepanel version
        print '* Installing latest OnePanel'
        self.install_onepanel()
        
        # set username and password
        print
        print '============================'
        print '*    INSTALL COMPLETED!    *'
        print '============================'
        print 
        username = raw_input('Admin username [default: admin]: ').strip()
        password = raw_input('Admin password [default: admin]: ').strip()
        if len(username) == 0:
            username = 'admin'
        if len(password) == 0:
            password = 'admin'
        self.config(username, password)
        
        print
        print '* Username and password set successfully!'
        print 
        print '* The URL of your OnePanel is:',
        print 'http://%s:8888/' % self.detect_ip()
        print 

        pass


def main():
    install = Install()
    install.install()
    

if __name__ == "__main__":
    main()
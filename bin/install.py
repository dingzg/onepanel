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

onepanel_downloadurl = 'https://github.com/dingzg/onepanel/archive/master.zip'
paramiko_downloadurl = 'https://github.com/paramiko/paramiko/archive/release-1.7.5.zip'

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

    def install_paramiko(self):
        localpkg_found = False
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'paramiko.zip')):
            localpkg_found = True
        else:
            self._run('wget -nv -c "%s" -O paramiko.zip' % paramiko_downloadurl)
        self._run('unzip -o paramiko.zip')
        if not localpkg_found: os.remove('paramiko.zip')
        self._run('cd paramiko-release-1.7.5;python setup.py install;cd ..', True)
        
    def install_onepanel(self):
        localpkg_found = False
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'onepanel.zip')):
            # local install package found
            localpkg_found = True
        else:
            # or else install online
            print '* Downloading install package from www.onepanel.org'
            #f = urllib2.urlopen('http://www.onepanel.org/api/latest')
            #data = f.read()
            #f.close()
            #https://github.com/dingzg/onepanel/archive/master.zip
            #onepanel-master.zip
            #downloadurl = re.search('"download":"([^"]+)"', data).group(1).replace('\/', '/')
            self._run('wget -nv -c "%s" -O onepanel.zip' % onepanel_downloadurl)
            
        # uncompress and install it
        #self._run('mkdir onepanel')
        #self._run('tar zxmf onepanel.tar.gz -C onepanel')
        self._run('unzip onepanel.zip')
        if not localpkg_found: os.remove('onepanel.zip')
        
        # stop service
        print
        if os.path.exists('/etc/init.d/onepanel'):
            self._run('/etc/init.d/onepanel stop')

        # backup data and remove old code
        if os.path.exists('%s/data/' % self.installpath):
            self._run('cp -r %s/data/ onepanel-master/data/' % self.installpath, True)
        self._run('rm -rf %s' % self.installpath)
        
        # install new code
        self._run('mv onepanel-master %s' % self.installpath)
        self._run('chmod +x %s/bin/install_config.py %s/bin/start_server.py' % (self.installpath, self.installpath))
        
        # install service
        initscript = '%s/bin/init.d/%s/onepanel' % (self.installpath, self.distname)
        self._run('cp %s /etc/init.d/onepanel' % initscript)
        if os.path.exists('%s/data/' % self.installpath)==False:
            self._run('mkdir  %s/data/' % self.installpath)
        self._run('chmod +x /etc/init.d/onepanel')
        
        # start service
        if self.distname in ('centos', 'redhat'):
            #self._run('chkconfig onepanel on')
            self._run('service onepanel start')
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def config(self, username, password):
        self._run('%s/bin/install_config.py username "%s"' % (self.installpath, username))
        self._run('%s/bin/install_config.py password "%s"' % (self.installpath, password))
        
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

        # check paramiko
        print '* Checking paramiko ...',
        try:
            import paramiko
            print 'OK'
        except:
            print 'FAILED'

            # install the right version
            print '* Installing paramiko ...'
            self.install_paramiko()


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
        username = 'onepanel'
        password = 'onepanel'
        self.config(username, password)

        print 
        print '* The URL of your OnePanel is:',
        print 'http://%s:6666/' % self.detect_ip()
        print 

        pass


def main():
    print('==============================Warning==============================')
    print('If you want to update OnePanel,please copy install.py to other path and run it!')
    print('')

    continueflg = raw_input('Press "Y" to Continue or press "N" to Quit: ').strip()
    if continueflg in ('Y','y'):
        install = Install()
        install.install()
    else:
        exit
    

if __name__ == "__main__":
    main()
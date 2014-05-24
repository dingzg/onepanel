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

import os
import sys
import re
import binascii
import uuid
import json
import hashlib
import hmac
import time
import datetime
import platform
import subprocess
import functools
import tornado
import tornado.web
import tornado.httpclient
import tornado.gen
import tornado.ioloop
#import si
#import sc
#import user
#import file
#import fdisk
#import chkconfig
#import yum
#import nginx
#import mysql
#import php
#import ssh
sys.path.insert(0, os.path.join(os.path.dirname(__file__), r'../module'))
from module import *
import base64
import pyDes
import utils
from tornado.escape import utf8 as _u
from tornado.escape import to_unicode as _d
from config import Config
from async_process import call_subprocess, callbackable
import paramiko
import log

SERVER_NAME = 'onepanel'
OnePanel_VERSION = '0.0.2'
OnePanel_BUILD = '1'

 
class Application(tornado.web.Application):
    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):
        dist = si.Server.dist()
        settings['dist_name'] = dist['name'].lower()
        settings['dist_version'] = dist['version']
        settings['dist_verint'] = int(float(dist['version']))
        uname = si.Server.uname()
        settings['arch'] = uname['machine']
        if settings['arch'] == 'i686' and settings['dist_verint'] == 5: settings['arch'] = 'i386'
        #if settings['arch'] == 'unknown': settings['arch'] = uname['machine']
        settings['data_path'] = os.path.abspath(settings['data_path'])
        settings['package_path'] = os.path.join(settings['data_path'], 'packages')

        tornado.web.Application.__init__(self, handlers, default_host, transforms,
                 wsgi, **settings)


class RequestHandler(tornado.web.RequestHandler):

    def initialize(self):
        """Parse JSON data to argument list.
        """
        self.inifile = os.path.join(self.settings['data_path'], 'config.ini')
        self.config = Config(self.inifile)

        content_type = self.request.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                arguments = json.loads(tornado.escape.native_str(self.request.body))
                for name, value in arguments.iteritems():
                    name = _u(name)
                    if isinstance(value, unicode):
                        value = _u(value)
                    elif isinstance(value, bool):
                        value = value and 'on' or 'off'
                    else:
                        value = ''
                    self.request.arguments.setdefault(name, []).append(value)
            except:
                pass

    def set_default_headers(self):
        self.set_header('Server', SERVER_NAME)
    
    def check_xsrf_cookie(self):
        token = (self.get_argument("_xsrf", None) or
                 self.request.headers.get("X-XSRF-TOKEN"))
        if not token:
            raise tornado.web.HTTPError(403, "'_xsrf' argument missing from POST")
        if self.xsrf_token != token:
            raise tornado.web.HTTPError(403, "XSRF cookie does not match POST argument")

    def authed(self):
        # check for the access token, token only available within 30 mins
        access_token = (self.get_argument("_access", None) or
                    self.request.headers.get("X-ACCESS-TOKEN"))
        if access_token and self.config.get('auth', 'accesskeyenable'):
            accesskey = self.config.get('auth', 'accesskey')
            try:
                accesskey = base64.b64decode(accesskey)
                key = accesskey[:24]
                iv = accesskey[24:]
                k = pyDes.triple_des(key, pyDes.CBC, iv, pad=None, padmode=pyDes.PAD_PKCS5)
                data = k.decrypt(base64.b64decode(access_token))
                if not data.startswith('timestamp:'): raise Exception()
                if time.time() - int(data.replace('timestamp:', '')) > 30*60: raise Exception()
                return  # token auth ok
            except:
                pass
        
        # get the cookie within 30 mins
        if self.get_secure_cookie('authed', None, 30.0/1440) == 'yes':
            # regenerate the cookie timestamp per 5 mins
            if self.get_secure_cookie('authed', None, 5.0/1440) == None:
                self.set_secure_cookie('authed', 'yes', None)
        else:
            raise tornado.web.HTTPError(403, "Please login first")
    
    def getlastactive(self):
        # get last active from cookie
        cv = self.get_cookie('authed', False)
        try:
            return int(cv.split('|')[1])
        except:
            return 0

    @property
    def xsrf_token(self):
        if not hasattr(self, "_xsrf_token"):
            token = self.get_cookie("XSRF-TOKEN")
            if not token:
                token = binascii.b2a_hex(uuid.uuid4().bytes)
                expires_days = 30 if self.current_user else None
                self.set_cookie("XSRF-TOKEN", token, expires_days=expires_days)
            self._xsrf_token = token
        return self._xsrf_token


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('Server', SERVER_NAME)

class ErrorHandler(tornado.web.ErrorHandler):
    def set_default_headers(self):
        self.set_header('Server', SERVER_NAME)


class FallbackHandler(tornado.web.FallbackHandler):
    def set_default_headers(self):
        self.set_header('Server', SERVER_NAME)


class RedirectHandler(tornado.web.RedirectHandler):
    def set_default_headers(self):
        self.set_header('Server', SERVER_NAME)

        
class FileDownloadHandler(StaticFileHandler):
    def get(self, path):
        self.authed()
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-disposition', 'attachment; filename=%s' % os.path.basename(path))
        self.set_header('Content-Transfer-Encoding', 'binary')
        StaticFileHandler.get(self, path)

    def authed(self):
        # get the cookie within 30 mins
        if self.get_secure_cookie('authed', None, 30.0/1440) == 'yes':
            # regenerate the cookie timestamp per 5 mins
            if self.get_secure_cookie('authed', None, 5.0/1440) == None:
                self.set_secure_cookie('authed', 'yes', None)
        else:
            raise tornado.web.HTTPError(403, "Please login first")


class FileUploadHandler(RequestHandler):
    def post(self):
        self.authed()
        path = self.get_argument('path', '/')

        self.write(u'<body style="font-size:14px;overflow:hidden;margin:0;padding:0;">')

        if not self.request.files.has_key('ufile'):
            self.write(u'请选择要上传的文件！')
        else:
            self.write(u'正在上传...<br>')
            for file in self.request.files['ufile']:
                filename = re.split('[\\\/]', file['filename'])[-1]
                with open(os.path.join(path, filename), 'wb') as f:
                    f.write(file['body'])
                self.write(u'%s 上传成功！<br>' % file['filename'])

        self.write('</body>')


class VersionHandler(RequestHandler):
    def get(self):
        self.authed()
        version_info = {
            'version': OnePanel_VERSION,
            'build': OnePanel_BUILD,
        }
        self.write(version_info)


class XsrfHandler(RequestHandler):
    """Write a XSRF token to cookie
    """
    def get(self):
        self.xsrf_token


class AuthStatusHandler(RequestHandler):
    """Check if client has been authorized
    """
    def get(self):
        self.write({'lastactive': self.getlastactive()})

    def post(self):
        # authorize and update cookie
        try:
            self.authed()
            self.write({'authed': 'yes'})
        except:
            self.write({'authed': 'no'})


class ClientHandler(RequestHandler):
    """Get client infomation.
    """
    def get(self, argument):
        if argument == 'ip':
            self.write(self.request.remote_ip)


class LoginHandler(RequestHandler):
    """Validate username and password.
    """
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')

        loginlock = self.config.get('runtime', 'loginlock')
        if self.config.get('runtime', 'mode') == 'demo': loginlock = 'off'

        # check if login is locked
        if loginlock == 'on':
            loginlockexpire = self.config.getint('runtime', 'loginlockexpire')
            if time.time() < loginlockexpire:
                self.write({'code': -1,
                    'msg': u'登录已被锁定，请在 %s 后重试登录。<br>'\
                        u'如需立即解除锁定，请在服务器上执行以下命令：<br>'\
                        u'/usr/local/onepanel/bin/install_config.py loginlock off' %
                        datetime.datetime.fromtimestamp(loginlockexpire)
                            .strftime('%Y-%m-%d %H:%M:%S')})
                return
            else:
                self.config.set('runtime', 'loginlock', 'off')
                self.config.set('runtime', 'loginlockexpire', 0)

        loginfails = self.config.getint('runtime', 'loginfails')
        #cfg_username = self.config.get('auth', 'username')
        #cfg_password = self.config.get('auth', 'password')
        server_ip = self.config.get('server', 'ip')
        try:
                #paramiko.util.log_to_file('paramiko.log')
                #print ('username:',username)
                #print ('password:',password)
                s=paramiko.SSHClient()
                #s.load_system_host_keys()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                rc_ssh=s.connect(hostname = server_ip,username=username, password=password)
                s.close()
        except:
                rc_ssh='Error'
        if rc_ssh==None:
                #print ('Authentication Successful!')  
                self.config.set('auth', 'username', username)              
                if loginfails > 0:
                    self.config.set('runtime', 'loginfails', 0)
                self.set_secure_cookie('authed', 'yes', None)
                passwordcheck = self.config.getboolean('auth', 'passwordcheck')
                if passwordcheck:
                    self.write({'code': 1, 'msg': u'%s，您已登录成功！' % username})
                else:
                    self.write({'code': 0, 'msg': u'%s，您已登录成功！' % username})
        else:
                #print ('Authentication Fail!')
                if self.config.get('runtime', 'mode') == 'demo':
                    self.write({'code': -1, 'msg': u'用户名或密码错误！'})
                    return
                loginfails = loginfails+1
                self.config.set('runtime', 'loginfails', loginfails)
                if loginfails >= 5:
                    # lock 24 hours
                    self.config.set('runtime', 'loginlock', 'on')
                    self.config.set('runtime', 'loginlockexpire', int(time.time())+86400)
                    self.write({'code': -1, 'msg': u'用户名或密码错误！<br>'\
                        u'已连续错误 5 次，登录已被禁止！'})
                else:
                    self.write({'code': -1, 'msg': u'用户名或密码错误！<br>'\
                        u'连续错误 5 次后将被禁止登录，还有 %d 次机会。' % (5-loginfails)})


'''
        if cfg_password == '':
            self.write({'code': -1,
                'msg': u'登录密码还未设置，请在服务器上执行以下命令进行设置：<br>'\
                    u'/usr/local/onepanel/bin/install_config.py password \'您的密码\''})
        elif username != cfg_username:  # wrong with username
            self.write({'code': -1, 'msg': u'用户不存在！'})
        else:   # username is corret
            cfg_password, key = cfg_password.split(':')
            if hmac.new(key, password).hexdigest() == cfg_password:
                if loginfails > 0:
                    self.config.set('runtime', 'loginfails', 0)
                self.set_secure_cookie('authed', 'yes', None)
                
                passwordcheck = self.config.getboolean('auth', 'passwordcheck')
                if passwordcheck:
                    self.write({'code': 1, 'msg': u'%s，您已登录成功！' % username})
                else:
                    self.write({'code': 0, 'msg': u'%s，您已登录成功！' % username})
            else:
                if self.config.get('runtime', 'mode') == 'demo':
                    self.write({'code': -1, 'msg': u'用户名或密码错误！'})
                    return
                loginfails = loginfails+1
                self.config.set('runtime', 'loginfails', loginfails)
                if loginfails >= 5:
                    # lock 24 hours
                    self.config.set('runtime', 'loginlock', 'on')
                    self.config.set('runtime', 'loginlockexpire', int(time.time())+86400)
                    self.write({'code': -1, 'msg': u'用户名或密码错误！<br>'\
                        u'已连续错误 5 次，登录已被禁止！'})
                else:
                    self.write({'code': -1, 'msg': u'用户名或密码错误！<br>'\
                        u'连续错误 5 次后将被禁止登录，还有 %d 次机会。' % (5-loginfails)})
'''

class LogoutHandler(RequestHandler):
    """Logout
    """
    def post(self):
        self.authed()
        self.clear_cookie('authed')


class SitePackageHandler(RequestHandler):
    """Interface for quering site packages information.
    """
    def get(self, op):
        self.authed()
        if hasattr(self, op):
            getattr(self, op)()
        else:
            self.write({'code': -1, 'msg': u'未定义的操作！'})
    
    @tornado.web.asynchronous
    @tornado.gen.engine
    def getlist(self):
        if not os.path.exists(self.settings['package_path']): os.mkdir(self.settings['package_path'])

        packages = ''
        packages_cachefile = os.path.join(self.settings['package_path'], '.meta')
        
        # fetch from cache
        if os.path.exists(packages_cachefile):
            # check the file modify time
            mtime = os.stat(packages_cachefile).st_mtime
            if time.time() - mtime < 86400: # cache 24 hours
                with open(packages_cachefile) as f: packages = f.read()

        # fetch from api
        if not packages:
            http = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(http.fetch, 'http://api.onepanel.org/site_packages')
            if response.error:
                self.write({'code': -1, 'msg': u'获取网站系统列表失败！'})
                self.finish()
                return
            else:
                packages = response.body
                with open(packages_cachefile, 'w') as f: f.write(packages)
        
        packages = tornado.escape.json_decode(packages)
        self.write({'code': 0, 'msg':'', 'data': packages})

        self.finish()

    def getdownloadtask(self):
        name = self.get_argument('name', '')
        version = self.get_argument('version', '')
        
        if not name or not version:
            self.write({'code': -1, 'msg': u'获取安装包下载地址失败！'})
            return
        
        # fetch package list from cache
        packages_cachefile = os.path.join(self.settings['package_path'], '.meta')
        if not os.path.exists(packages_cachefile):
            self.write({'code': -1, 'msg': u'获取安装包下载地址失败！'})
            return
        with open(packages_cachefile) as f: packages = f.read()
        packages = tornado.escape.json_decode(packages)

        # check if name and version is available
        package = None
        for cate in packages:
            for pkg in cate['packages']:
                if pkg['code'] == name:
                    for v in pkg['versions']:
                        if v['code'] == version:
                            package = v
                            break
                if package: break
            if package: break
        if not package:
            self.write({'code': -1, 'msg': u'获取安装包下载地址失败！'})
            return
        
        filename = '%s-%s' % (name, version)
        workpath = os.path.join(self.settings['package_path'], filename)
        if not os.path.exists(workpath): os.mkdir(workpath)

        filenameext = '%s%s' % (filename, package['ext'])
        filepath = os.path.join(self.settings['package_path'], filenameext)

        self.write({'code': 0, 'msg': '', 'data': {
            'url': 'http://api.onepanel.org/site_packages/download?name=%s&version=%s' % (name, version),
            'path': filepath,
            'temp': workpath,
        }})


class QueryHandler(RequestHandler):
    """Interface for quering server information.
    
    Query one or more items, seperated by comma.
    Examples:
    /query/*
    /query/server.*
    /query/service.*
    /query/server.datetime,server.diskinfo
    /query/config.fstab(sda1)
    """
    def get(self, items):
        self.authed()
        
        items = items.split(',')
        qdict = {'server': [], 'service': [], 'config': [], 'tool': []}
        for item in items:
            if item == '**':
                # query all items
                qdict = {'server': '**', 'service': '**'}
                break
            elif item == '*':
                # query all realtime update items
                qdict = {'server': '*', 'service': '*'}
                break
            elif item == 'server.**':
                qdict['server'] = '**'
            elif item == 'service.**':
                qdict['service'] = '**'
            else:
                item = _u(item)
                iteminfo = item.split('.', 1)
                if len(iteminfo) != 2: continue
                sec, q = iteminfo
                if sec not in ('server', 'service', 'config', 'tool'): continue
                if qdict[sec] == '**': continue
                qdict[sec].append(q)

        # item : realtime update
        server_items = {
            'hostname'     : False,
            'datetime'     : True,
            'uptime'       : True,
            'loadavg'      : True,
            'cpustat'      : True,
            'meminfo'      : True,
            'mounts'       : True, 
            'netifaces'    : True,
            'nameservers'  : True,
            'distribution' : False,
            'uname'        : False, 
            'cpuinfo'      : False,
            'diskinfo'     : False,
            'virt'         : False,
        }
        service_items = {
            'onepanel'      : False,
            'nginx'        : False,
            'httpd'        : False,
            'vsftpd'       : False,
            'mysqld'       : False,
            'redis'        : False,
            'memcached'    : False,
            'mongod'       : False,
            'php-fpm'      : False,
            'sendmail'     : False,
            'sshd'         : False,
            'iptables'     : False,
            'crond'        : False,
            'ntpd'         : False,
        }
        config_items = {
            'fstab'        : False,
        }
        tool_items = {
            'supportfs'    : False,
        }

        result = {}
        for sec, qs in qdict.iteritems():
            if sec == 'server':
                if qs == '**':
                    qs = server_items.keys()
                elif qs == '*':
                    qs = [item for item, relup in server_items.iteritems() if relup==True]
                for q in qs:
                    if not server_items.has_key(q): continue
                    result['%s.%s' % (sec, q)] = getattr(si.Server, q)()
            elif sec == 'service':
                autostart_services = si.Service.autostart_list()
                if qs == '**':
                    qs = service_items.keys()
                elif qs == '*':
                    qs = [item for item, relup in service_items.iteritems() if relup==True]
                for q in qs:
                    if not service_items.has_key(q): continue
                    status = si.Service.status(q)
                    result['%s.%s' % (sec, q)] = status and {        'status': status,
                        'autostart': q in autostart_services,
                    } or None
            elif sec == 'config':
                for q in qs:
                    params = []
                    if q.endswith(')'):
                        q = q.strip(')').split('(', 1)
                        if len(q) != 2: continue
                        q, params = q
                        params = params.split(',')
                    if not config_items.has_key(q): continue
                    result['%s.%s' % (sec, q)] = getattr(sc.Server, q)(*params)
            elif sec == 'tool':
                for q in qs:
                    params = []
                    if q.endswith(')'):
                        q = q.strip(')').split('(', 1)
                        if len(q) != 2: continue
                        q, params = q
                        params = params.split(',')
                    if not tool_items.has_key(q): continue
                    result['%s.%s' % (sec, q)] = getattr(si.Tool, q)(*params)

        self.write(result)

class UtilsNetworkHandler(RequestHandler):
    """Handler for network ifconfig.
    """
    def get(self, sec, ifname):
        self.authed()
        if sec == 'ifnames':
            ifconfigs = sc.Server.ifconfigs()
            # filter lo
            del ifconfigs['lo']
            self.write({'ifnames': sorted(ifconfigs.keys())})
        elif sec == 'ifconfig':
            ifconfig = sc.Server.ifconfig(_u(ifname))
            if ifconfig != None: self.write(ifconfig)
        elif sec == 'nameservers':
            self.write({'nameservers': sc.Server.nameservers()})
        
    def post(self, sec, ifname):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许修改网络设置！'})
            return

        if sec == 'ifconfig':
            ip = self.get_argument('ip', '')
            mask = self.get_argument('mask', '')
            gw = self.get_argument('gw', '')
            
            if not utils.is_valid_ip(_u(ip)):
                self.write({'code': -1, 'msg': u'%s 不是有效的IP地址！' % ip})
                return
            if not utils.is_valid_netmask(_u(mask)):
                self.write({'code': -1, 'msg': u'%s 不是有效的子网掩码！' % mask})
                return
            if gw != '' and not utils.is_valid_ip(_u(gw)):
                self.write({'code': -1, 'msg': u'网关IP %s 不是有效的IP地址！' % gw})
                return

            if sc.Server.ifconfig(_u(ifname), {'ip': _u(ip), 'mask': _u(mask), 'gw': _u(gw)}):
                self.write({'code': 0, 'msg': u'IP设置保存成功！'})
            else:
                self.write({'code': -1, 'msg': u'IP设置保存失败！'})

        elif sec == 'nameservers':
            nameservers = _u(self.get_argument('nameservers', ''))
            nameservers = nameservers.split(',')

            for i, nameserver in enumerate(nameservers):
                if nameserver == '':
                    del nameservers[i]
                    continueSO
                if not utils.is_valid_ip(nameserver):
                    self.write({'code': -1, 'msg': u'%s 不是有效的IP地址！' % nameserver})
                    return

            if sc.Server.nameservers(nameservers):
                self.write({'code': 0, 'msg': u'DNS设置保存成功！'})
            else:
                self.write({'code': -1, 'msg': u'DNS设置保存失败！'})


class UtilsTimeHandler(RequestHandler):
    """Handler for system datetime setting.
    """
    def get(self, sec, region=None):
        self.authed()
        if sec == 'datetime':
            self.write(si.Server.datetime(asstruct=True))
        elif sec == 'timezone':
            self.write({'timezone': sc.Server.timezone(self.inifile)})
        elif sec == 'timezone_list':
            if region == None:
                self.write({'regions': sorted(sc.Server.timezone_regions())})
            else:
                self.write({'cities': sorted(sc.Server.timezone_list(region))})

    def post(self, sec, ifname):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许时区设置！'})
            return

        if sec == 'timezone':
            timezone = self.get_argument('timezone', '')
            if sc.Server.timezone(self.inifile, _u(timezone)):
                self.write({'code': 0, 'msg': u'时区设置保存成功！'})
            else:
                self.write({'code': -1, 'msg': u'时区设置保存失败！'})
        

class SettingHandler(RequestHandler):
    """Settings for onepanel
    """
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, section):
        self.authed()
        if section == 'auth':
            username = self.config.get('auth', 'username')
            passwordcheck = self.config.getboolean('auth', 'passwordcheck')
            self.write({'username': username, 'passwordcheck': passwordcheck})
            self.finish()

        elif section == 'server':
            ip = self.config.get('server', 'ip')
            port = self.config.get('server', 'port')
            self.write({'ip': ip, 'port': port})
            self.finish()

        elif section == 'accesskey':
            accesskey = self.config.get('auth', 'accesskey')
            accesskeyenable = self.config.getboolean('auth', 'accesskeyenable')
            self.write({'accesskey': accesskey, 'accesskeyenable': accesskeyenable})
            self.finish()

        elif section == 'upver':
            force = self.get_argument('force', '')
            lastcheck = self.config.getint('server', 'lastcheckupdate')

            # detect new version daily
            if force or time.time() > lastcheck + 86400:
                http = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(http.fetch, 'https://github.com/dingzg/onepanel/raw/master/version')
                if response.error:
                    self.write({'code': -1, 'msg': u'获取新版本信息失败！'})
                else:
                    data = tornado.escape.json_decode(response.body)
                    self.write({'code': 0, 'msg':'', 'data': data})
                    self.config.set('server', 'lastcheckupdate', int(time.time()))
                    self.config.set('server', 'updateinfo', response.body)
            else:
                data = self.config.get('server', 'updateinfo')
                try:
                    data = tornado.escape.json_decode(data)
                except:
                    data = {}
                self.write({'code': 0, 'msg': '', 'data': data})

            self.finish()

    def post(self, section):
        self.authed()
        if section == 'auth':
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改用户名和密码！'})
                return

            username = self.get_argument('username', '')
            password = self.get_argument('password', '')
            passwordc = self.get_argument('passwordc', '')
            passwordcheck = self.get_argument('passwordcheck', '')

            if username == '':
                self.write({'code': -1, 'msg': u'用户名不能为空！'})
                return
            if password != passwordc:
                self.write({'code': -1, 'msg': u'两次密码输入不一致！'})
                return

            if passwordcheck != 'on': passwordcheck = 'off'
            self.config.set('auth', 'passwordcheck', passwordcheck)

            if username != '':
                self.config.set('auth', 'username', username)
            if password != '':
                key = utils.randstr()
                pwd = hmac.new(key, password).hexdigest()
                self.config.set('auth', 'password', '%s:%s' % (pwd, key))

            self.write({'code': 0, 'msg': u'登录设置更新成功！'})

        elif section == 'server':
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改服务绑定地址！'})
                return

            ip = self.get_argument('ip', '*')
            port = self.get_argument('port', '6666')

            if ip != '*' and ip != '':
                if not utils.is_valid_ip(_u(ip)):
                    self.write({'code': -1, 'msg': u'%s 不是有效的IP地址！' % ip})
                    return
                netifaces = si.Server.netifaces()
                ips = [netiface['ip'] for netiface in netifaces]
                if not ip in ips:
                    self.write({'code': -1, 'msg': u'<p>%s 不是该服务器的IP地址！</p>'\
                                u'<p>可用的IP地址有：<br>%s</p>' % (ip, '<br>'.join(ips))})
                    return
            port = int(port)
            if not port > 0 and port < 65535:
                self.write({'code': -1, 'msg': u'端口范围必须在 0 到 65535 之间！'})
                return
            
            self.config.set('server', 'ip', ip)
            self.config.set('server', 'port', port)
            self.write({'code': 0, 'msg': u'服务设置更新成功！将在重启服务后生效。'})

        elif section == 'accesskey':
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改远程控制设置！'})
                return

            accesskey = self.get_argument('accesskey', '')
            accesskeyenable = self.get_argument('accesskeyenable', '')

            if accesskeyenable == 'on' and accesskey == '':
                self.write({'code': -1, 'msg': u'远程控制密钥不能为空！'})
                return
            
            if accesskey != '':
                try:
                    if len(base64.b64decode(accesskey)) != 32: raise Exception()
                except:
                    self.write({'code': -1, 'msg': u'远程控制密钥格式不正确！'})
                    return

            if accesskeyenable != 'on': accesskeyenable = 'off'
            self.config.set('auth', 'accesskeyenable', accesskeyenable)
            self.config.set('auth', 'accesskey', accesskey)

            self.write({'code': 0, 'msg': u'远程控制设置更新成功！'})


class OperationHandler(RequestHandler):
    """Server operation handler
    """

    def post(self, op):
        """Run a server operation
        """
        self.authed()
        if hasattr(self, op):
            getattr(self, op)()
        else:
            self.write({'code': -1, 'msg': u'未定义的操作！'})
    
    def reboot(self):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许重启服务器！'})
            return

        p = subprocess.Popen('reboot',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
        info = p.stdout.read()
        p.stderr.read()
        if p.wait() == 0:
            self.write({'code': 0, 'msg': u'已向系统发送重启指令，系统即将重启！'})
        else:
            self.write({'code': -1, 'msg': u'向系统发送重启指令失败！'})

    def fdisk(self):
        fdisk.main_process(self)
    
    def chkconfig(self):
        chkconfig.main_process(self)
        
    def user(self):
        user.main_process(self)
    
    def file(self):
        file.main_process(self)
    
    def nginx(self):
        nginx.main_process(self)

    def mysql(self):
        mysql.main_process(self)

    def php(self):
        php.main_process(self)

    def ssh(self):
        ssh.main_process(self)

    def shell(self):
        shell.main_process(self)

    def task(self):
        task.main_process(self)

    def apache(self):
        apache.main_process(self)

    def vsftp(self):
        vsftp.main_process(self)

class PageHandler(RequestHandler):
    """Return some page.
    """
    def get(self, op, action):
        try:
            self.authed()
        except:
            self.write(u'没有权限，请<a href="/">登录</a>后再查看该页！')
            return
        if hasattr(self, op):
            getattr(self, op)(action)
        else:
            self.write(u'未定义的操作！')
    
    def php(self, action):
        if action == 'phpinfo':
            # =PHPE9568F34-D428-11d2-A769-00AA001ACF42 (PHP Logo)
            # =PHPE9568F35-D428-11d2-A769-00AA001ACF42 (Zend logo)
            # =PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000 (PHP Credits)
            # redirect them to http://php.net/index.php?***
            if self.request.query.startswith('=PHP'):
                self.redirect('http://www.php.net/index.php?%s' % self.request.query)
            else:
                self.write(php.phpinfo())


class BackendHandler(RequestHandler):
    """Backend process manager
    """
    jobs = {}
    locks = {}

    def _lock_job(self, lockname):
        cls = BackendHandler
        if cls.locks.has_key(lockname): return False
        cls.locks[lockname] = True
        return True

    def _unlock_job(self, lockname):
        cls = BackendHandler
        if not cls.locks.has_key(lockname): return False
        del cls.locks[lockname]
        return True

    def _start_job(self, jobname):
        cls = BackendHandler
        # check if the job is running
        if cls.jobs.has_key(jobname) and cls.jobs[jobname]['status'] == 'running':
            return False

        cls.jobs[jobname] = {'status': 'running', 'msg': ''}
        return True

    def _update_job(self, jobname, code, msg):
        cls = BackendHandler
        cls.jobs[jobname]['code'] = code
        cls.jobs[jobname]['msg'] = msg
        return True

    def _get_job(self, jobname):
        cls = BackendHandler
        if not cls.jobs.has_key(jobname):
            return {'status': 'none', 'code': -1, 'msg': ''}
        return cls.jobs[jobname]

    def _finish_job(self, jobname, code, msg, data=None):
        cls = BackendHandler
        cls.jobs[jobname]['status'] = 'finish'
        cls.jobs[jobname]['code'] = code
        cls.jobs[jobname]['msg'] = msg
        if data: cls.jobs[jobname]['data'] = data

    def get(self, jobname):
        """Get the status of the new process
        """
        self.authed()
        self.write(self._get_job(_u(jobname)))

    def _call(self, callback):
        #with tornado.stack_context.NullContext():
        tornado.ioloop.IOLoop.instance().add_callback(callback)

    def post(self, jobname):
        """Create a new backend process
        """
        self.authed()

        # centos/redhat only job
        if jobname in ('yum_repolist', 'yum_installrepo', 'yum_info',
                       'yum_install', 'yum_uninstall', 'yum_ext_info'):
            if self.settings['dist_name'] not in ('centos', 'redhat'):
                self.write({'code': -1, 'msg': u'不支持的系统类型！'})
                return

        if self.config.get('runtime', 'mode') == 'demo':
            if jobname in ('update', 'datetime', 'swapon', 'swapoff', 'mount', 'umount', 'format'):
                self.write({'code': -1, 'msg': u'DEMO状态不允许此类操作！'})
                return

        if jobname == 'update':
            self._call(self.update)
        elif jobname in ('service_restart', 'service_start', 'service_stop'):
            name = self.get_argument('name', '')
            service = self.get_argument('service', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if service in ('network', 'sshd', 'onepanel', 'iptables'):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许此类操作！'})
                    return

            if service not in si.Service.support_services:
                self.write({'code': -1, 'msg': u'未支持的服务！'})
                return
            if not name: name = service
            dummy, action = jobname.split('_')
            if service != '':
                self._call(functools.partial(self.service,
                        _u(action),
                        _u(service),
                        _u(name)))
        elif jobname == 'datetime':
            newdatetime = self.get_argument('datetime', '')
            # check datetime format
            try:
                datetime.datetime.strptime(newdatetime, '%Y-%m-%d %H:%M:%S')
            except:
                self.write({'code': -1, 'msg': u'时间格式有错误！'})
                return
            self._call(functools.partial(self.datetime,
                        _u(newdatetime)))
        elif jobname in ('swapon', 'swapoff'):
            devname = self.get_argument('devname', '')
            if jobname == 'swapon':
                action = 'on'
            else:
                action = 'off'
            self._call(functools.partial(self.swapon,
                        _u(action),
                        _u(devname)))
        elif jobname in ('mount', 'umount'):
            devname = self.get_argument('devname', '')
            mountpoint = self.get_argument('mountpoint', '')
            fstype = self.get_argument('fstype', '')
            if jobname == 'mount':
                action = 'mount'
            else:
                action = 'umount'
            self._call(functools.partial(self.mount,
                        _u(action),
                        _u(devname),
                        _u(mountpoint),
                        _u(fstype)))
        elif jobname == 'format':
            devname = self.get_argument('devname', '')
            fstype = self.get_argument('fstype', '')
            self._call(functools.partial(self.format,
                        _u(devname),
                        _u(fstype)))
        elif jobname == 'yum_repolist':
            self._call(self.yum_repolist)
        elif jobname == 'yum_installrepo':
            repo = self.get_argument('repo', '')
            self._call(functools.partial(self.yum_installrepo,
                        _u(repo)))
        elif jobname == 'yum_info':
            pkg = self.get_argument('pkg', '')
            repo = self.get_argument('repo', '*')
            option = self.get_argument('option', '')
            if option == 'update':
                if not pkg in [v for k,vv in yum.yum_pkg_alias.iteritems() for v in vv]:
                    self.write({'code': -1, 'msg': u'未支持的软件包！'})
                    return
            else:
                option = 'install'
                if not yum.yum_pkg_alias.has_key(pkg):
                    self.write({'code': -1, 'msg': u'未支持的软件包！'})
                    return
                if repo not in yum.yum_repolist + ('installed', '*'):
                    self.write({'code': -1, 'msg': u'未知的软件源 %s！' % repo})
                    return
            self._call(functools.partial(self.yum_info,
                        _u(pkg),
                        _u(repo),
                        _u(option)))
        elif jobname in ('yum_install', 'yum_uninstall', 'yum_update'):
            repo = self.get_argument('repo', '')
            pkg = self.get_argument('pkg', '')
            ext = self.get_argument('ext', '')
            version = self.get_argument('version', '')
            release = self.get_argument('release', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if pkg in ('sshd', 'iptables'):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许此类操作！'})
                    return

            if not yum.yum_pkg_relatives.has_key(pkg):
                self.write({'code': -1, 'msg': u'软件包不存在！'})
                return
            if ext and not yum.yum_pkg_relatives[pkg].has_key(ext):
                self.write({'code': -1, 'msg': u'扩展不存在！'})
                return
            if jobname == 'yum_install':
                if repo not in yum.yum_repolist:
                    self.write({'code': -1, 'msg': u'未知的软件源 %s！' % repo})
                    return
                handler = self.yum_install
            elif jobname == 'yum_uninstall':
                handler = self.yum_uninstall
            elif jobname == 'yum_update':
                handler = self.yum_update
            self._call(functools.partial(handler,
                        _u(repo),
                        _u(pkg),
                        _u(version),
                        _u(release),
                        _u(ext)))
        elif jobname == 'yum_ext_info':
            pkg = self.get_argument('pkg', '')
            if not yum.yum_pkg_relatives.has_key(pkg):
                self.write({'code': -1, 'msg': u'软件包不存在！'})
                return
            self._call(functools.partial(self.yum_ext_info,
                        _u(pkg)))
        elif jobname in ('move', 'copy'):
            srcpath = self.get_argument('srcpath', '')
            despath = self.get_argument('despath', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if jobname == 'move':
                    if not srcpath.startswith('/var/www') or not despath.startswith('/var/www'):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                        return
                elif jobname == 'copy':
                    if not despath.startswith('/var/www'):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                        return

            if not os.path.exists(srcpath):
                if not os.path.exists(srcpath.strip('*')):
                    self.write({'code': -1, 'msg': u'源路径不存在！'})
                    return
            if jobname == 'copy':
                handler = self.copy
            elif jobname == 'move':
                handler = self.move
            self._call(functools.partial(handler,
                        _u(srcpath),
                        _u(despath)))
        elif jobname == 'remove':
            paths = self.get_argument('paths', '')
            paths = _u(paths).split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www') and not p.startswith(self.settings['package_path']):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下执行删除操作！'})
                        return

            self._call(functools.partial(self.remove, paths))
        elif jobname == 'compress':
            zippath = self.get_argument('zippath', '')
            paths = self.get_argument('paths', '')
            paths = _u(paths).split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                if not zippath.startswith('/var/www'):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下创建压缩包！'})
                    return
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下创建压缩包！'})
                        return

            self._call(functools.partial(self.compress,
                        _u(zippath), paths))
        elif jobname == 'decompress':
            zippath = self.get_argument('zippath', '')
            despath = self.get_argument('despath', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if not zippath.startswith('/var/www') and not zippath.startswith(self.settings['package_path']) or \
                   not despath.startswith('/var/www') and not despath.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下执行解压操作！'})
                    return

            self._call(functools.partial(self.decompress,
                        _u(zippath),
                        _u(despath)))
        elif jobname == 'ntpdate':
            server = self.get_argument('server', '')
            self._call(functools.partial(self.ntpdate,
                        _u(server)))
        elif jobname == 'chown':
            paths = _u(self.get_argument('paths', ''))
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下执行此操作！'})
                        return

            a_user = _u(self.get_argument('user', ''))
            a_group = _u(self.get_argument('group', ''))
            recursively = self.get_argument('recursively', '')
            option = recursively == 'on' and '-R' or ''
            self._call(functools.partial(self.chown, paths, a_user, a_group, option))
        elif jobname == 'chmod':
            paths = _u(self.get_argument('paths', ''))
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': u'DEMO状态不允许在 /var/www 以外的目录下执行此操作！'})
                        return

            perms = _u(self.get_argument('perms', ''))
            recursively = self.get_argument('recursively', '')
            option = recursively == 'on' and '-R' or ''
            self._call(functools.partial(self.chmod, paths, perms, option))
        elif jobname == 'wget':
            url = _u(self.get_argument('url', ''))
            path = _u(self.get_argument('path', ''))

            if self.config.get('runtime', 'mode') == 'demo':
                if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许下载到 /var/www 以外的目录！'})
                    return

            self._call(functools.partial(self.wget, url, path))
        elif jobname == 'mysql_fupdatepwd':
            password = _u(self.get_argument('password', ''))
            passwordc = _u(self.get_argument('passwordc', ''))
            if password != passwordc:
                self.write({'code': -1, 'msg': u'两次密码输入不一致！'})
                return
            self._call(functools.partial(self.mysql_fupdatepwd, password))
        elif jobname == 'mysql_databases':
            password = _u(self.get_argument('password', ''))
            self._call(functools.partial(self.mysql_databases, password))
        elif jobname == 'mysql_dbinfo':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            self._call(functools.partial(self.mysql_dbinfo, password, dbname))
        elif jobname == 'mysql_users':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            self._call(functools.partial(self.mysql_users, password, dbname))
        elif jobname == 'mysql_rename':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            newname = _u(self.get_argument('newname', ''))
            if dbname == newname:
                self.write({'code': -1, 'msg': u'数据库名无变化！'})
                return
            self._call(functools.partial(self.mysql_rename, password, dbname, newname))
        elif jobname == 'mysql_create':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            collation = _u(self.get_argument('collation', ''))
            self._call(functools.partial(self.mysql_create, password, dbname, collation))
        elif jobname == 'mysql_export':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            path = _u(self.get_argument('path', ''))
            
            if not path:
                self.write({'code': -1, 'msg': u'请选择数据库导出目录！'})
                return

            if self.config.get('runtime', 'mode') == 'demo':
                if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许导出到 /var/www 以外的目录！'})
                    return

            self._call(functools.partial(self.mysql_export, password, dbname, path))
        elif jobname == 'mysql_drop':
            password = _u(self.get_argument('password', ''))
            dbname = _u(self.get_argument('dbname', ''))
            self._call(functools.partial(self.mysql_drop, password, dbname))
        elif jobname == 'mysql_createuser':
            password = _u(self.get_argument('password', ''))
            user = _u(self.get_argument('user', ''))
            host = _u(self.get_argument('host', ''))
            pwd = _u(self.get_argument('pwd', ''))
            self._call(functools.partial(self.mysql_createuser, password, user, host, pwd))
        elif jobname == 'mysql_userprivs':
            password = _u(self.get_argument('password', ''))
            username = _u(self.get_argument('username', ''))
            if not '@' in username:
                self.write({'code': -1, 'msg': u'用户不存在！'})
                return
            user, host = username.split('@', 1)
            self._call(functools.partial(self.mysql_userprivs, password, user, host))
        elif jobname == 'mysql_updateuserprivs':
            password = _u(self.get_argument('password', ''))
            username = _u(self.get_argument('username', ''))
            privs = self.get_argument('privs', '')
            try:
                privs = tornado.escape.json_decode(privs)
            except:
                self.write({'code': -1, 'msg': u'权限数据有误！'})
                return
            dbname = _u(self.get_argument('dbname', ''))
            if not '@' in username:
                self.write({'code': -1, 'msg': u'用户不存在！'})
                return
            user, host = username.split('@', 1)
            privs = [
                priv.replace('_priv', '').replace('_', ' ').upper()
                    .replace('CREATE TMP TABLE', 'CREATE TEMPORARY TABLES')
                    .replace('SHOW DB', 'SHOW DATABASES')
                    .replace('REPL CLIENT', 'REPLICATION CLIENT')
                    .replace('REPL SLAVE', 'REPLICATION SLAVE')
                for priv, value in privs.iteritems() if '_priv' in priv and value == 'Y']
            self._call(functools.partial(self.mysql_updateuserprivs, password, user, host, privs, dbname))
        elif jobname == 'mysql_setuserpassword':
            password = _u(self.get_argument('password', ''))
            username = _u(self.get_argument('username', ''))
            if not '@' in username:
                self.write({'code': -1, 'msg': u'用户不存在！'})
                return
            user, host = username.split('@', 1)
            pwd = _u(self.get_argument('pwd', ''))
            self._call(functools.partial(self.mysql_setuserpassword, password, user, host, pwd))
        elif jobname == 'mysql_dropuser':
            password = _u(self.get_argument('password', ''))
            username = _u(self.get_argument('username', ''))
            if not '@' in username:
                self.write({'code': -1, 'msg': u'用户不存在！'})
                return
            user, host = username.split('@', 1)
            user, host = user.strip(), host.strip()
            if user == 'root' and host != '%':
                self.write({'code': -1, 'msg': u'该用户不允许删除！'})
                return
            self._call(functools.partial(self.mysql_dropuser, password, user, host))
        elif jobname == 'ssh_genkey':
            path = _u(self.get_argument('path', ''))
            password = _u(self.get_argument('password', ''))
            if not path: path = '/root/.ssh/sshkey_onepanel'
            self._call(functools.partial(self.ssh_genkey, path, password))
        elif jobname == 'ssh_chpasswd':
            path = _u(self.get_argument('path', ''))
            oldpassword = _u(self.get_argument('oldpassword', ''))
            newpassword = _u(self.get_argument('newpassword', ''))
            if not path: path = '/root/.ssh/sshkey_onepanel'
            self._call(functools.partial(self.ssh_chpasswd, path, oldpassword, newpassword))
        else:   # undefined job
            self.write({'code': -1, 'msg': u'未定义的操作！'})
            return

        self.write({'code': 0, 'msg': ''})

    @tornado.gen.engine
    def update(self):
        if not self._start_job('update'): return
        
        root_path = self.settings['root_path']
        data_path = self.settings['data_path']
        distname = self.settings['dist_name']

        # don't do it in dev environment
        if os.path.exists('%s/../.svn' % root_path):
            self._finish_job('update', 0, u'升级成功！')
            return
        
        # install the latest version
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(http.fetch, 'https://github.com/dingzg/onepanel/raw/master/version')
        if response.error:
            self._update_job('update', -1, u'获取版本信息失败！')
            return
        versioninfo = tornado.escape.json_decode(response.body)
        downloadurl = versioninfo['download']
        version = versioninfo['version']
        initscript = u'%s/bin/init.d/%s/onepanel' % (root_path, distname)

        steps = [
            {'desc': u'正在下载安装包...',
                'cmd': u'wget -q "%s" -O %s/v%s.tar.gz' % (downloadurl, data_path, version),
            }, {'desc': u'正在创建解压目录...',
                'cmd': u'mkdir %s/onepanel' % data_path,
            }, {'desc': u'正在解压安装包...',
                'cmd': u'tar zxmf %s/v%s.tar.gz -C %s/onepanel' % (data_path, version, data_path),
            }, {'desc': u'正在删除旧版本...',
                'cmd': u'find %s -mindepth 1 -maxdepth 1 -path %s -prune -o -exec rm -rf {} \;' % (root_path, data_path),
            }, {'desc': u'正在复制新版本...',
                'cmd': u'find %s/onepanel/onepanel-%s -mindepth 1 -maxdepth 1 -exec cp -r {} %s \;' % (data_path, version, root_path),
            }, {'desc': u'正在删除旧的服务脚本...',
                'cmd': u'rm -f /etc/init.d/onepanel',
            }, {'desc': u'正在安装新的服务脚本...',
                'cmd': u'cp %s /etc/init.d/onepanel' % initscript,
            }, {'desc': u'正在更改脚本权限...',
                'cmd': u'chmod +x /etc/init.d/onepanel %s/bin/install_config.py %s/bin/start_server.py' % (root_path, root_path),
            }, {'desc': u'正在删除安装临时文件...',
                'cmd': u'rm -rf %s/onepanel %s/v%s.tar.gz %s/version' % (data_path, data_path, version, root_path),
            },
        ]
        for step in steps:
            desc = _u(step['desc'])
            cmd = _u(step['cmd'])
            self._update_job('update', 2, desc)
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result != 0:
                self._update_job('update', -1, desc+'失败！')
                break
            
        if result == 0:
            code = 0
            msg = u'升级成功！请刷新页面重新登录。'
        else:
            code = -1
            msg = u'升级失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job('update', code, msg)

    @tornado.gen.engine
    def service(self, action, service, name):
        """Service operation.
        """
        jobname = 'service_%s_%s' % (action, service)
        if not self._start_job(jobname): return

        action_str = {'start': u'启动', 'stop': u'停止', 'restart': u'重启'}
        self._update_job(jobname, 2, u'正在%s %s 服务...' % (action_str[action], _d(name)))
        
        # patch before start sendmail in redhat/centos 5.x
        # REF: http://www.mombu.com/gnu_linux/red-hat/t-why-does-sendmail-hang-during-rh-9-start-up-1068528.html
        if action == 'start' and service in ('sendmail', )\
            and self.settings['dist_name'] in ('redhat', 'centos')\
            and self.settings['dist_verint'] == 5:
            # check if current hostname line in /etc/hosts have a char '.'
            hostname = si.Server.hostname()
            hostname_found = False
            dot_found = False
            lines = []
            with open('/etc/hosts') as f:
                for line in f:
                    if not line.startswith('#') and not hostname_found:
                        fields = line.strip().split()
                        if hostname in fields:
                            hostname_found = True
                            # find '.' in this line
                            dot_found = any(field for field in fields[1:] if '.' in field)
                            if not dot_found:
                                line = '%s %s.localdomain\n' % (line.strip(), hostname)
                    lines.append(line)
            if not dot_found:
                with open('/etc/hosts', 'w') as f: f.writelines(lines)

        cmd = '/etc/init.d/%s %s' % (service, action)
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'%s 服务%s成功！' % (_d(name), action_str[action])
        else:
            code = -1
            msg = u'%s 服务%s失败！<p style="margin:10px">%s</p>' % (_d(name), action_str[action], _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def datetime(self, newdatetime):
        """Set datetime using system's date command.
        """
        jobname = 'datetime'
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在设置系统时间...')

        cmd = 'date -s \'%s\'' % (newdatetime, )
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'系统时间设置成功！'
        else:
            code = -1
            msg = u'系统时间设置失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def ntpdate(self, server):
        """Run ntpdate command to sync time.
        """
        jobname = 'ntpdate_%s' % server
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在从 %s 同步时间...' % server)
        cmd = 'ntpdate -u %s' % server
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            offset = float(output.split(' offset ')[-1].split()[0])
            msg = u'同步时间成功！（时间偏差 %f 秒）' % _d(offset)
        else:
            code = -1
            # no server suitable for synchronization found
            if 'no server suitable' in output:
                msg = u'同步时间失败！没有找到合适同步服务器。'
            else:
                msg = u'同步时间失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def swapon(self, action, devname):
        """swapon or swapoff swap partition.
        """
        jobname = 'swapon_%s_%s' % (action, devname)
        if not self._start_job(jobname): return

        action_str = {'on': u'启用', 'off': u'停用'}
        self._update_job(jobname, 2, u'正在%s %s...' % \
                    (action_str[action], _d(devname)))

        if action == 'on':
            cmd = 'swapon /dev/%s' % devname
        else:
            cmd = 'swapoff /dev/%s' % devname

        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'%s %s 成功！' % (action_str[action], _d(devname))
        else:
            code = -1
            msg = u'%s %s 失败！<p style="margin:10px">%s</p>' % (action_str[action], _d(devname), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def mount(self, action, devname, mountpoint, fstype):
        """Mount or umount using system's mount command.
        """
        jobname = 'mount_%s_%s' % (action, devname)
        if not self._start_job(jobname): return

        action_str = {'mount': u'挂载', 'umount': u'卸载'}
        self._update_job(jobname, 2, u'正在%s %s 到 %s...' % \
                    (action_str[action], _d(devname), _d(mountpoint)))

        if action == 'mount':
            # write config to /etc/fstab
            sc.Server.fstab(_u(devname), {
                'devname': _u(devname),
                'mount': _u(mountpoint),
                'fstype': _u(fstype),
            })
            cmd = 'mount -t %s /dev/%s %s' % (fstype, devname, mountpoint)
        else:
            cmd = 'umount /dev/%s' % (devname)

        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'%s %s 成功！' % (action_str[action], _d(devname))
        else:
            code = -1
            msg = u'%s %s 失败！<p style="margin:10px">%s</p>' % (action_str[action], _d(devname), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def format(self, devname, fstype):
        """Format partition using system's mkfs.* commands.
        """
        jobname = 'format_%s' % devname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在格式化 %s，可能需要较长时间，请耐心等候...' % _d(devname))

        if fstype in ('ext2', 'ext3', 'ext4'):
            cmd = 'mkfs.%s -F /dev/%s' % (fstype, devname)
        elif fstype in ('xfs', 'reiserfs', 'btrfs'):
            cmd = 'mkfs.%s -f /dev/%s' % (fstype, devname)
        elif fstype == 'swap':
            cmd = 'mkswap -f /dev/%s' % devname
        else:
            cmd = 'mkfs.%s /dev/%s' % (fstype, devname)
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'%s 格式化成功！' % _d(devname)
        else:
            code = -1
            msg = u'%s 格式化失败！<p style="margin:10px">%s</p>' % (_d(devname), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def yum_repolist(self):
        """Get yum repository list.
        """
        jobname = 'yum_repolist'
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，读取软件源列表失败。')
            return

        self._update_job(jobname, 2, u'正在获取软件源列表...')

        cmd = 'yum repolist --disableplugin=fastestmirror'
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        data = []
        if result == 0:
            code = 0
            msg = u'获取软件源列表成功！'
            lines = output.split('\n')
            for line in lines:
                if not line: continue
                repo = line.split()[0]
                if repo in yum.yum_repolist:
                    data.append(repo)
        else:
            code = -1
            msg = u'获取软件源列表失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')

    @tornado.gen.engine
    def yum_installrepo(self, repo):
        """Install yum repository.
        
        REFs:
        http://jyrxs.blogspot.com/2008/02/using-centos-5-repos-in-rhel5-server.html
        http://www.tuxradar.com/answers/440
        """
        jobname = 'yum_installrepo_%s' % repo
        if not self._start_job(jobname): return

        if repo not in yum.yum_repolist:
            self._finish_job(jobname, -1, u'不可识别的软件源！')
            self._unlock_job('yum')
            return

        self._update_job(jobname, 2, u'正在安装软件源 %s...' % _d(repo))

        arch = self.settings['arch']
        dist_verint = self.settings['dist_verint']
        
        cmds = []
        if repo == 'base':
            if dist_verint == 5:
                if self.settings['dist_name'] == 'redhat':
                    # backup system version info
                    cmds.append('cp -f /etc/redhat-release /etc/redhat-release.onepanel')
                    cmds.append('cp -f /etc/issue /etc/issue.onepanel')
                    #cmds.append('rpm -e redhat-release-notes-5Server --nodeps')
                    cmds.append('rpm -e redhat-release-5Server --nodeps')

            for rpm in yum.yum_reporpms[repo][dist_verint][arch]:
                cmds.append('rpm -U %s' % rpm)

            cmds.append('cp -f /etc/issue.onepanel /etc/issue')
            cmds.append('cp -f /etc/redhat-release.onepanel /etc/redhat-release')

        elif repo in ('epel', 'CentALT', 'ius'):
            # CentALT and ius depends on epel
            for rpm in yum.yum_reporpms['epel'][dist_verint][arch]:
                cmds.append('rpm -U %s' % rpm)

            if repo in ('CentALT', 'ius'):
                for rpm in yum.yum_reporpms[repo][dist_verint][arch]:
                    cmds.append('rpm -U %s' % rpm)
        
        elif repo == '10gen':
            # REF: http://docs.mongodb.org/manual/tutorial/install-mongodb-on-redhat-centos-or-fedora-linux/
            with open('/etc/yum.repos.d/10gen.repo', 'w') as f:
                f.write(yum.yum_repostr['10gen'][self.settings['arch']])
        
        elif repo == 'atomic':
            # REF: http://www.atomicorp.com/channels/atomic/
            result, output = yield tornado.gen.Task(call_subprocess, self, yum.yum_repoinstallcmds['atomic'], shell=True)
            if result != 0: error = True

        error = False
        for cmd in cmds:
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result !=0 and not 'already installed' in output:
                error = True
                break
        
        # CentALT doesn't have any mirror, we have make a mirror for it
        if repo == 'CentALT':
            repofile = '/etc/yum.repos.d/centalt.repo'
            if os.path.exists(repofile):
                lines = []
                baseurl_found = False
                with open(repofile) as f:
                    for line in f:
                        if line.startswith('baseurl='):
                            baseurl_found = True
                            line = '#%s' % line
                            lines.append(line)
                            # add a mirrorlist line
                            metalink = 'http://www.onepanel.org/mirrorlist?'\
                                'repo=centalt-%s&arch=$basearch' % self.settings['dist_verint']
                            line = 'mirrorlist=%s\n' % metalink
                        lines.append(line)
                if baseurl_found:
                    with open(repofile, 'w') as f: f.writelines(lines)

        if not error:
            code = 0
            msg = u'软件源 %s 安装成功！' % _d(repo)
        else:
            code = -1
            msg = u'软件源 %s 安装失败！<p style="margin:10px">%s</p>' % (_d(repo), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def yum_info(self, pkg, repo, option):
        """Get package info in repository.
        
        Option can be 'install' or 'update'.
        """
        jobname = 'yum_info_%s' % pkg
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，读取软件包信息失败。')
            return

        self._update_job(jobname, 2, u'正在获取软件版本信息...')

        if repo == '*': repo = ''
        if option == 'install':
            cmds = ['yum info %s %s.%s --showduplicates --disableplugin=fastestmirror'
                    % (repo, alias, self.settings['arch']) for alias in yum.yum_pkg_alias[pkg]]
        else:
            cmds = ['yum info %s.%s --disableplugin=fastestmirror' % (pkg, self.settings['arch'])]

        data = []
        matched = False
        for cmd in cmds:
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result == 0:
                matched = True
                lines = output.split('\n')
                for line in lines:
                    if any(line.startswith(word)
                        for word in ('Name', 'Version', 'Release', 'Size',
                                     'Repo', 'From repo')):
                        fields = line.strip().split(':', 1)
                        if len(fields) != 2: continue
                        field_name = fields[0].strip().lower().replace(' ', '_')
                        field_value = fields[1].strip()
                        if field_name == 'name': data.append({})
                        data[-1][field_name] = field_value
        
        if matched:
            code = 0
            msg = u'获取软件版本信息成功！'
            data = [pkg for pkg in data if pkg['repo'] in yum.yum_repolist+('installed',)]
            if option == 'update' and len(data) == 1:
                msg = u'没有找到可用的新版本！'
        else:
            code = -1
            msg = u'获取软件版本信息失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')

    @tornado.gen.engine
    def yum_install(self, repo, pkg, version, release, ext):
        """Install specified version of package.
        """
        jobname = 'yum_install_%s_%s_%s_%s_%s' % (repo, pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，安装失败。')
            return

        if ext:
            self._update_job(jobname, 2, u'正在下载并安装扩展包，请耐心等候...')
        else:
            self._update_job(jobname, 2, u'正在下载并安装软件包，请耐心等候...')
        
        if ext: # install extension
            if version: 
                if release:
                    pkgs = ['%s-%s-%s.%s' % (ext, version, release, self.settings['arch'])]
                else:
                    pkgs = ['%s-%s.%s' % (ext, version, self.settings['arch'])]
            else:
                pkgs = ['%s.%s' % (ext, self.settings['arch'])]
        else:   # install package
            if version: # install special version
                if release:
                    pkgs = ['%s-%s-%s.%s' % (p, version, release, self.settings['arch'])
                        for p, pinfo in yum.yum_pkg_relatives[pkg].iteritems() if pinfo['default']]
                else:
                    pkgs = ['%s-%s.%s' % (p, version, self.settings['arch'])
                        for p, pinfo in yum.yum_pkg_relatives[pkg].iteritems() if pinfo['default']]
            else:   # or judge by the system
                pkgs = ['%s.%s' % (p, self.settings['arch'])
                    for p, pinfo in yum.yum_pkg_relatives[pkg].iteritems() if pinfo['default']]
        repos = [repo, ]
        if repo in ('CentALT', 'ius', 'atomic', '10gen'):
            repos.extend(['base', 'updates', 'epel'])
        exclude_repos = [r for r in yum.yum_repolist if r not in repos]

        endinstall = False
        hasconflict = False
        conflicts_backups = []
        while not endinstall:
            cmd = 'yum install -y %s --disablerepo=%s' % (' '.join(pkgs), ','.join(exclude_repos))
            #cmd = 'yum install -y %s' % (' '.join(pkgs), )
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            pkgstr = version and '%s v%s-%s' % (ext and ext or pkg, version, release) or (ext and ext or pkg)
            if result == 0:
                if hasconflict:
                    # install the conflict packages we just remove
                    cmd = 'yum install -y %s' % (' '.join(conflicts_backups), )
                    result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
                endinstall = True
                code = 0
                msg = u'%s 安装成功！' % _d(pkgstr)
            else:
                # check if conflicts occur
                # error message like this:
                #   Error: mysql55 conflicts with mysql
                # or:
                #   file /etc/my.cnf conflicts between attempted installs of mysql-libs-5.5.28-1.el6.x86_64 and mysql55-libs-5.5.28-2.ius.el6.x86_64
                #   file /usr/lib64/mysql/libmysqlclient.so.18.0.0 conflicts between attempted installs of mysql-libs-5.5.28-1.el6.x86_64 and mysql55-libs-5.5.28-2.ius.el6.x86_64
                clines = output.split('\n')
                for cline in clines:
                    if cline.startswith('Error:') and ' conflicts with ' in cline:
                        hasconflict = True
                        conflict_pkg = cline.split(' conflicts with ', 1)[1]
                        # remove the conflict package and packages depend on it
                        self._update_job(jobname, 2, u'检测到软件冲突，正在卸载处理冲突...')
                        tcmd = 'yum erase -y %s' % conflict_pkg
                        result, output = yield tornado.gen.Task(call_subprocess, self, tcmd)
                        if result == 0:
                            lines = output.split('\n')
                            conflicts_backups = []
                            linestart = False
                            for line in lines:
                                if not linestart:
                                    if not line.startswith('Removing for dependencies:'): continue
                                    linestart = True
                                if not line.strip(): break # end
                                fields = line.split()
                                conflicts_backups.append('%s-%s' % (fields[0], fields[2]))
                        else:
                            endinstall = True
                        break
                    elif 'conflicts between' in cline:
                        pass
                if not hasconflict:
                    endinstall = True
                if endinstall:
                    code = -1
                    msg = u'%s 安装失败！<p style="margin:10px">%s</p>' % (_d(pkgstr), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    @tornado.gen.engine
    def yum_uninstall(self, repo, pkg, version, release, ext):
        """Uninstall specified version of package.
        """
        jobname = 'yum_uninstall_%s_%s_%s_%s' % (pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，卸载失败。')
            return

        if ext:
            self._update_job(jobname, 2, u'正在卸载扩展包...')
        else:
            self._update_job(jobname, 2, u'正在卸载软件包...')
        
        if ext:
            pkgs = ['%s-%s-%s.%s' % (ext, version, release, self.settings['arch'])]
        else:
            pkgs = ['%s-%s-%s.%s' % (p, version, release, self.settings['arch'])
                for p, pinfo in yum.yum_pkg_relatives[pkg].iteritems()
                if pinfo.has_key('base') and pinfo['base']]
        ## also remove depends pkgs
        #for p, pinfo in yum.yum_pkg_relatives[pkg].iteritems():
        #    if pinfo.has_key('depends'):
        #        pkgs += pinfo['depends']
        cmd = 'yum erase -y %s' % (' '.join(pkgs), )
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'%s v%s-%s 卸载成功！' % (_d(ext and ext or pkg), _d(version), _d(release))
        else:
            code = -1
            msg = u'%s v%s-%s 卸载失败！<p style="margin:10px">%s</p>' % \
                (_d(ext and ext or pkg), _d(version), _d(release), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    @tornado.gen.engine
    def yum_update(self, repo, pkg, version, release, ext):
        """Update a package.
        
        The parameter repo and version here are only for showing.
        """
        jobname = 'yum_update_%s_%s_%s_%s_%s' % (repo, pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，更新失败。')
            return

        if ext:
            self._update_job(jobname, 2, u'正在下载并升级扩展包，请耐心等候...')
        else:
            self._update_job(jobname, 2, u'正在下载并升级软件包，请耐心等候...')

        cmd = 'yum update -y %s-%s-%s.%s' % (ext and ext or pkg, version, release, self.settings['arch'])
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'成功升级 %s 到版本 v%s-%s！' % (_d(ext and ext or pkg), _d(version), _d(release))
        else:
            code = -1
            msg = u'%s 升级到版本 v%s-%s 失败！<p style="margin:10px">%s</p>' % \
                (_d(ext and ext or pkg), _d(version), _d(release), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    @tornado.gen.engine
    def yum_ext_info(self, pkg):
        """Get ext info list of a pkg info.
        """
        jobname = 'yum_ext_info_%s' % pkg
        if not self._start_job(jobname): return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, u'已有一个YUM进程在运行，获取扩展信息失败。')
            return
 
        self._update_job(jobname, 2, u'正在收集扩展信息...')

        exts = [k for k, v in yum.yum_pkg_relatives[pkg].iteritems() if v.has_key('isext') and v['isext']]
        cmd = 'yum info %s --disableplugin=fastestmirror' % (' '.join(['%s.%s' % (ext, self.settings['arch']) for ext in exts]))

        data = []
        matched = False
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            matched = True
            lines = output.split('\n')
            for line in lines:
                if any(line.startswith(word)
                    for word in ('Name', 'Version', 'Release', 'Size',
                                 'Repo', 'From repo')):
                    fields = line.strip().split(':', 1)
                    if len(fields) != 2: continue
                    field_name = fields[0].strip().lower().replace(' ', '_')
                    field_value = fields[1].strip()
                    if field_name == 'name': data.append({})
                    data[-1][field_name] = field_value
        if matched:
            code = 0
            msg = u'获取扩展信息成功！'
        else:
            code = -1
            msg = u'获取扩展信息失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')
        
    @tornado.gen.engine
    def copy(self, srcpath, despath):
        """Copy a directory or file to a new path.
        """
        jobname = 'copy_%s_%s' % (srcpath, despath)
        if not self._start_job(jobname): return
 
        self._update_job(jobname, 2, u'正在复制 %s 到 %s...' % (_d(srcpath), _d(despath)))

        cmd = 'cp -rf %s %s' % (srcpath, despath)
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd, shell='*' in srcpath)
        if result == 0:
            code = 0
            msg = u'复制 %s 到 %s 完成！' % (_d(srcpath), _d(despath))
        else:
            code = -1
            msg = u'复制 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (_d(srcpath), _d(despath), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)
        
    @tornado.gen.engine
    def move(self, srcpath, despath):
        """Move a directory or file recursively to a new path.
        """
        jobname = 'move_%s_%s' % (srcpath, despath)
        if not self._start_job(jobname): return
 
        self._update_job(jobname, 2, u'正在移动 %s 到 %s...' % (_d(srcpath), _d(despath)))
        
        # check if the despath exists
        # if exists, we first copy srcpath to despath, then remove the srcpath
        despath_exists = os.path.exists(despath)

        shell = False
        if despath_exists:
            # secure check
            if not os.path.exists(srcpath):
                self._finish_job(jobname, -1, u'不可识别的源！')
                return
            cmd = 'cp -rf %s/* %s' % (srcpath, despath)
            shell = True
        else:
            cmd = 'mv %s %s' % (srcpath, despath)
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd, shell=shell)
        if result == 0:
            code = 0
            msg = u'移动 %s 到 %s 完成！' % (_d(srcpath), _d(despath))
        else:
            code = -1
            msg = u'移动 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (_d(srcpath), _d(despath), _d(output.strip().replace('\n', '<br>')))

        if despath_exists and code == 0:
            # remove the srcpath
            cmd = 'rm -rf %s' % (srcpath, )
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result == 0:
                code = 0
                msg = u'移动 %s 到 %s 完成！' % (_d(srcpath), _d(despath))
            else:
                code = -1
                msg = u'移动 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (_d(srcpath), _d(despath), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def remove(self, paths):
        """Remove a directory or file recursively.
        """
        jobname = 'remove_%s' % ','.join(paths)
        if not self._start_job(jobname): return
 
        for path in paths:
            self._update_job(jobname, 2, u'正在删除 %s...' % _d(path))
            cmd = 'rm -rf %s' % (path)
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result == 0:
                code = 0
                msg = u'删除 %s 成功！' % _d(path)
            else:
                code = -1
                msg = u'删除 %s 失败！<p style="margin:10px">%s</p>' % (_d(path), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)
        
    @tornado.gen.engine
    def compress(self, zippath, paths):
        """Compress files or directorys.
        """
        jobname = 'compress_%s_%s' % (zippath, ','.join(paths))
        if not self._start_job(jobname): return
        
        self._update_job(jobname, 2, u'正在压缩生成 %s...' % _d(zippath))

        shell = False
        if zippath.endswith('.gz'): path = ' '.join(paths)

        basepath = os.path.dirname(zippath)+'/'
        paths = [path.replace(basepath, '') for path in paths]

        if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
            cmd = 'tar zcf %s -C %s %s' % (zippath, basepath, ' '.join(paths))
        elif zippath.endswith('.tar.bz2'):
            cmd = 'tar jcf %s -C %s %s' % (zippath, basepath, ' '.join(paths))
        elif zippath.endswith('.zip'):
            self._update_job(jobname, 2, u'正在安装 zip...')
            if not os.path.exists('/usr/bin/zip'):
                if self.settings['dist_name'] in ('centos', 'redhat'):
                    cmd = 'yum install -y zip unzip'
                    result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
                    if result == 0:
                        self._update_job(jobname, 0, u'zip 安装成功！')
                    else:
                        self._update_job(jobname, -1, u'zip 安装失败！')
                        return
            cmd = 'cd %s; zip -rq9 %s %s' % (basepath, zippath, ' '.join(paths))
            shell = True
        elif zippath.endswith('.gz'):
            cmd = 'gzip -f %s' % path
        else:
            self._finish_job(jobname, -1, u'不支持的类型！')
            return

        result, output = yield tornado.gen.Task(call_subprocess, self, cmd, shell=shell)
        if result == 0:
            code = 0
            msg = u'压缩到 %s 成功！' % _d(zippath)
        else:
            code = -1
            msg = u'压缩失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
        
    @tornado.gen.engine
    def decompress(self, zippath, despath):
        """Decompress a zip file.
        """
        jobname = 'decompress_%s_%s' % (zippath, despath)
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在解压 %s...' % _d(zippath))
        if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
            cmd = 'tar zxf %s -C %s' % (zippath, despath)
        elif zippath.endswith('.tar.bz2'):
            cmd = 'tar jxf %s -C %s' % (zippath, despath)
        elif zippath.endswith('.zip'):
            if not os.path.exists('/usr/bin/unzip'):
                self._update_job(jobname, 2, u'正在安装 unzip...')
                if self.settings['dist_name'] in ('centos', 'redhat'):
                    cmd = 'yum install -y zip unzip'
                    result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
                    if result == 0:
                        self._update_job(jobname, 0, u'unzip 安装成功！')
                    else:
                        self._update_job(jobname, -1, u'unzip 安装失败！')
                        return
            cmd = 'unzip -q -o %s -d %s' % (zippath, despath)
        elif zippath.endswith('.gz'):
            cmd = 'gunzip -f %s' % zippath
        else:
            self._finish_job(jobname, -1, u'不支持的类型！')
            return

        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'解压 %s 成功！' % _d(zippath)
        else:
            code = -1
            msg = u'解压 %s 失败！<p style="margin:10px">%s</p>' % (_d(zippath), _d(output.strip().replace('\n', '<br>')))

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def chown(self, paths, user, group, option):
        """Change owner of paths.
        """
        jobname = 'chown_%s' % ','.join(paths)
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在设置用户和用户组...')
        
        #cmd = 'chown %s %s:%s %s' % (option, user, group, ' '.join(paths))
        
        for path in paths:
            result = yield tornado.gen.Task(callbackable(file.chown), path, user, group, option=='-R')
            if result == True:
                code = 0
                msg = u'设置用户和用户组成功！'
            else:
                code = -1
                msg = u'设置 %s 的用户和用户组时失败！' % _d(path)
                break

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def chmod(self, paths, perms, option):
        """Change perms of paths.
        """
        jobname = 'chmod_%s' % ','.join(paths)
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在设置权限...')
        
        #cmd = 'chmod %s %s %s' % (option, perms, ' '.join(paths))
        try:
            perms = int(perms, 8)
        except:
            self._finish_job(jobname, -1, u'权限值输入有误！')
            return

        for path in paths:
            result = yield tornado.gen.Task(callbackable(file.chmod), path, perms, option=='-R')
            if result == True:
                code = 0
                msg = u'权限修改成功！'
            else:
                code = -1
                msg = u'修改 %s 的权限时失败！' % _d(path)
                break

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def wget(self, url, path):
        """Run wget command to download file.
        """
        jobname = 'wget_%s' % tornado.escape.url_escape(url)
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在下载 %s...' % _d(url))
        
        if os.path.isdir(path): # download to the directory
            cmd = 'wget -q "%s" --directory-prefix=%s' % (url, path)
        else:
            cmd = 'wget -q "%s" -O %s' % (url, path)
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result == 0:
            code = 0
            msg = u'下载成功！'
        else:
            code = -1
            msg = u'下载失败！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
    
    @tornado.gen.engine
    def mysql_fupdatepwd(self, password):
        """Force updating mysql root password.
        """
        jobname = 'mysql_fupdatepwd'
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在检测 MySQL 服务状态...')
        cmd = 'service mysqld status'
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        isstopped = 'stopped' in output
        
        if not isstopped:
            self._update_job(jobname, 2, u'正在停止 MySQL 服务...')
            cmd = 'service mysqld stop'
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result != 0:
                self._finish_job(jobname, -1, u'停止 MySQL 服务时出错！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>')))
                return

        self._update_job(jobname, 2, u'正在启用 MySQL 恢复模式...')
        manually = False
        cmd = 'service mysqld startsos'
        result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
        if result != 0:
            # some version of mysqld init.d script may not have startsos option
            # we run it manually
            manually = True
            cmd = 'mysqld_safe --skip-grant-tables --skip-networking'
            p = subprocess.Popen(cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    close_fds=True, shell=True)
            if not p:
                self._finish_job(jobname, -1, u'启用 MySQL 恢复模式时出错！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>')))
                return

        # wait for the mysqld_safe to start up
        if manually: time.sleep(2)

        error = False
        self._update_job(jobname, 2, u'正在强制重置 root 密码...')
        if not mysql.fupdatepwd(password):
            error = True

        if manually:
            # 'service mysqld restart' cannot stop the manually start-up mysqld_safe process
            result = yield tornado.gen.Task(callbackable(mysql.shutdown), password)
            if result:
                self._update_job(jobname, 0, u'成功停止 MySQL 服务！')
            else:
                self._update_job(jobname, -1, u'停止 MySQL 服务失败！')
            p.terminate()
            p.wait()

        msg = ''
        if not isstopped:
            if error:
                msg = u'重置 root 密码时发生错误！正在重启 MySQL 服务...'
                self._update_job(jobname, -1, msg)
            else:
                self._update_job(jobname, 2, u'正在重启 MySQL 服务...')
            if manually:
                cmd = 'service mysqld start'
            else:
                cmd = 'service mysqld restart'
        else:
            if error:
                msg = u'重置 root 密码时发生错误！正在停止 MySQL 服务...'
                self._update_job(jobname, -1, msg)
            else:
                self._update_job(jobname, 2, u'正在停止 MySQL 服务...')
            if manually:
                cmd = ''
            else:
                cmd = 'service mysqld stop'

        if not cmd:
            if error:
                code = -1
                msg = u'%sOK' % msg
            else:
                code = 0
                msg = u'root 密码重置成功！'
        else:
            result, output = yield tornado.gen.Task(call_subprocess, self, cmd)
            if result == 0:
                if error:
                    code = -1
                    msg = u'%sOK' % msg
                else:
                    code = 0
                    msg = u'root 密码重置成功！'
            else:
                if error:
                    code = -1
                    msg = u'%sOK' % msg
                else:
                    code = -1
                    msg = u'root 密码重置成功，但在操作服务时出错！<p style="margin:10px">%s</p>' % _d(output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
    
    @tornado.gen.engine
    def mysql_databases(self, password):
        """Show MySQL database list.
        """
        jobname = 'mysql_databases'
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在获取数据库列表...')
        dbs = []
        dbs = yield tornado.gen.Task(callbackable(mysql.show_databases), password)
        if dbs:
            code = 0
            msg = u'获取数据库列表成功！'
        else:
            code = -1
            msg = u'获取数据库列表失败！'

        self._finish_job(jobname, code, msg, dbs)
    
    @tornado.gen.engine
    def mysql_users(self, password, dbname=None):
        """Show MySQL user list.
        """
        if not dbname:
            jobname = 'mysql_users'
        else:
            jobname = 'mysql_users_%s' % dbname
        if not self._start_job(jobname): return

        if not dbname:
            self._update_job(jobname, 2, u'正在获取用户列表...')
        else:
            self._update_job(jobname, 2, u'正在获取数据库 %s 的用户列表...' % _d(dbname))

        users = []
        users = yield tornado.gen.Task(callbackable(mysql.show_users), password, dbname)
        if users:
            code = 0
            msg = u'获取用户列表成功！'
        else:
            code = -1
            msg = u'获取用户列表失败！'

        self._finish_job(jobname, code, msg, users)
    
    @tornado.gen.engine
    def mysql_dbinfo(self, password, dbname):
        """Get MySQL database info.
        """
        jobname = 'mysql_dbinfo_%s' % dbname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在获取数据库 %s 的信息...' % _d(dbname))
        dbinfo = False
        dbinfo = yield tornado.gen.Task(callbackable(mysql.show_database), password, dbname)
        if dbinfo:
            code = 0
            msg = u'获取数据库 %s 的信息成功！' % _d(dbname)
        else:
            code = -1
            msg = u'获取数据库 %s 的信息失败！' % _d(dbname)

        self._finish_job(jobname, code, msg, dbinfo)
    
    @tornado.gen.engine
    def mysql_rename(self, password, dbname, newname):
        """MySQL database rename.
        """
        jobname = 'mysql_rename_%s' % dbname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在重命名 %s...' % _d(dbname))
        result = yield tornado.gen.Task(callbackable(mysql.rename_database), password, dbname, newname)
        if result == True:
            code = 0
            msg = u'%s 重命名成功！' % _d(dbname)
        else:
            code = -1
            msg = u'%s 重命名失败！' % _d(dbname)

        self._finish_job(jobname, code, msg)
    
    @tornado.gen.engine
    def mysql_create(self, password, dbname, collation):
        """Create MySQL database.
        """
        jobname = 'mysql_create_%s' % dbname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在创建 %s...' % _d(dbname))
        result = yield tornado.gen.Task(callbackable(mysql.create_database), password, dbname, collation=collation)
        if result == True:
            code = 0
            msg = u'%s 创建成功！' % _d(dbname)
        else:
            code = -1
            msg = u'%s 创建失败！' % _d(dbname)

        self._finish_job(jobname, code, msg)
    
    @tornado.gen.engine
    def mysql_export(self, password, dbname, path):
        """MySQL database export.
        """
        jobname = 'mysql_export_%s' % dbname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在导出 %s...' % _d(dbname))
        result = yield tornado.gen.Task(callbackable(mysql.export_database), password, dbname, path)
        if result == True:
            code = 0
            msg = u'%s 导出成功！' % _d(dbname)
        else:
            code = -1
            msg = u'%s 导出失败！' % _d(dbname)

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def mysql_drop(self, password, dbname):
        """Drop a MySQL database.
        """
        jobname = 'mysql_drop_%s' % dbname
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在删除 %s...' % _d(dbname))
        result = yield tornado.gen.Task(callbackable(mysql.drop_database), password, dbname)
        if result == True:
            code = 0
            msg = u'%s 删除成功！' % _d(dbname)
        else:
            code = -1
            msg = u'%s 删除失败！' % _d(dbname)

        self._finish_job(jobname, code, msg)
    
    @tornado.gen.engine
    def mysql_createuser(self, password, user, host, pwd=None):
        """Create MySQL user.
        """
        username = '%s@%s' % (user, host)
        jobname = 'mysql_createuser_%s' % username
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在添加用户 %s...' % _d(username))
        result = yield tornado.gen.Task(callbackable(mysql.create_user), password, user, host, pwd)
        if result == True:
            code = 0
            msg = u'用户 %s 添加成功！' % _d(username)
        else:
            code = -1
            msg = u'用户 %s 添加失败！' % _d(username)

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def mysql_userprivs(self, password, user, host):
        """Get MySQL user privileges.
        """
        username = '%s@%s' % (user, host)
        jobname = 'mysql_userprivs_%s' % username
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在获取用户 %s 的权限...' % _d(username))
        
        privs = {'global':{}, 'bydb':{}}
        globalprivs = yield tornado.gen.Task(callbackable(mysql.show_user_globalprivs), password, user, host)
        if globalprivs != False:
            code = 0
            msg = u'获取用户 %s 的全局权限成功！' % _d(username)
            privs['global'] = globalprivs
        else:
            code = -1
            msg = u'获取用户 %s 的全局权限失败！' % _d(username)
            privs = False
        
        if privs:
            dbprivs = yield tornado.gen.Task(callbackable(mysql.show_user_dbprivs), password, user, host)
            if dbprivs != False:
                code = 0
                msg = u'获取用户 %s 的数据库权限成功！' % _d(username)
                privs['bydb'] = dbprivs
            else:
                code = -1
                msg = u'获取用户 %s 的数据库权限失败！' % _d(username)
                privs = False

        self._finish_job(jobname, code, msg, privs)

    @tornado.gen.engine
    def mysql_updateuserprivs(self, password, user, host, privs, dbname=None):
        """Update MySQL user privileges.
        """
        username = '%s@%s' % (user, host)
        if dbname:
            jobname = 'mysql_updateuserprivs_%s_%s' % (username, dbname)
        else:
            jobname = 'mysql_updateuserprivs_%s' % username
        if not self._start_job(jobname): return

        if dbname:
            self._update_job(jobname, 2, u'正在更新用户 %s 在数据库 %s 中的权限...' % (_d(username), _d(dbname)))
        else:
            self._update_job(jobname, 2, u'正在更新用户 %s 的权限...' % _d(username))
            
        rt = yield tornado.gen.Task(callbackable(mysql.update_user_privs), password, user, host, privs, dbname)
        if rt != False:
            code = 0
            msg = u'用户 %s 的权限更新成功！' % _d(username)
        else:
            code = -1
            msg = u'用户 %s 的权限更新失败！' % _d(username)

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def mysql_setuserpassword(self, password, user, host, pwd):
        """Set password of MySQL user.
        """
        username = '%s@%s' % (user, host)
        jobname = 'mysql_setuserpassword_%s' % username
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在更新用户 %s 的密码...' % _d(username))
            
        rt = yield tornado.gen.Task(callbackable(mysql.set_user_password), password, user, host, pwd)
        if rt != False:
            code = 0
            msg = u'用户 %s 的密码更新成功！' % _d(username)
        else:
            code = -1
            msg = u'用户 %s 的密码更新失败！' % _d(username)

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def mysql_dropuser(self, password, user, host):
        """Drop a MySQL user.
        """
        username = '%s@%s' % (user, host)
        jobname = 'mysql_dropuser_%s' % username
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在删除用户 %s...' % _d(username))
            
        rt = yield tornado.gen.Task(callbackable(mysql.drop_user), password, user, host)
        if rt != False:
            code = 0
            msg = u'用户 %s 删除成功！' % _d(username)
        else:
            code = -1
            msg = u'用户 %s 删除失败！' % _d(username)

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def ssh_genkey(self, path, password=''):
        """Generate a ssh key pair.
        """
        jobname = 'ssh_genkey'
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在生成密钥对...')
            
        rt = yield tornado.gen.Task(callbackable(ssh.genkey), path, password)
        if rt != False:
            code = 0
            msg = u'密钥对生成成功！'
        else:
            code = -1
            msg = u'密钥对生成失败！'

        self._finish_job(jobname, code, msg)

    @tornado.gen.engine
    def ssh_chpasswd(self, path, oldpassword, newpassword=''):
        """Change password of a ssh private key.
        """
        jobname = 'ssh_chpasswd'
        if not self._start_job(jobname): return

        self._update_job(jobname, 2, u'正在修改私钥密码...')
            
        rt = yield tornado.gen.Task(callbackable(ssh.chpasswd), path, oldpassword, newpassword)
        if rt != False:
            code = 0
            msg = u'私钥密码修改成功！'
        else:
            code = -1
            msg = u'私钥密码修改失败！'

        self._finish_job(jobname, code, msg)
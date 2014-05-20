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
root_path =  os.path.split(os.path.dirname(__file__))[0]
sys.path.insert(0, os.path.join(root_path, 'lib'))

import ssl
import tornado.ioloop
import tornado.httpserver
#import com.web
#import com.config
import com

#from com.utils import make_cookie_secret

def write_pid():
    pidfile = '/var/run/onepanel.pid'
    pidfp = open(pidfile, 'w')
    pidfp.write(str(os.getpid()))
    pidfp.close()

def main():
    
    # settings of tornado application
    settings = {
        'root_path': root_path,
        'data_path': os.path.join(root_path, 'data'),
        'static_path': os.path.join(root_path, 'static'),
        'xsrf_cookies': True,
        'cookie_secret': com.utils.make_cookie_secret(),
    }

    # read configuration from config.ini
    cfg = com.config.Config(settings['data_path'] + '/config.ini')
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')
    application = com.set_ui.SetUI(settings)

    server = tornado.httpserver.HTTPServer(application)
    server.listen(server_port, address=server_ip)
    write_pid()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
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

import web

def SetUI(settings):
    # settings of tornado application
    
    application = web.Application([
        (r'/xsrf', web.XsrfHandler),
        (r'/authstatus', web.AuthStatusHandler),
        (r'/login', web.LoginHandler),
        (r'/logout', web.LogoutHandler),
        (r'/query/(.+)', web.QueryHandler),
        (r'/utils/network/(.+?)(?:/(.+))?', web.UtilsNetworkHandler),
        (r'/utils/time/(.+?)(?:/(.+))?', web.UtilsTimeHandler),
        (r'/setting/(.+)', web.SettingHandler),
        (r'/operation/(.+)', web.OperationHandler),
        (r'/page/(.+)/(.+)', web.PageHandler),
        (r'/backend/(.+)', web.BackendHandler),
        (r'/sitepackage/(.+)', web.SitePackageHandler),
        (r'/client/(.+)', web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)',
            web.StaticFileHandler, {'path': settings['static_path']}),
        (r'/($)', web.StaticFileHandler,
            {'path': settings['static_path'] + '/index.html'}),
        (r'/file/(.+)', web.FileDownloadHandler, {'path': '/'}),
        (r'/fileupload', web.FileUploadHandler),
        (r'/version', web.VersionHandler),
        (r'/.*', web.ErrorHandler, {'status_code': 404}),
    ], **settings)

    return application   


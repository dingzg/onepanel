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


"""Package for file operations.
"""

import os
import sys
if __name__ == '__main__':
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import time
import pwd
import grp
import re
import magic
import mimetypes
import anydbm
import subprocess
from stat import *
from uuid import uuid4
sys.path.insert(0, os.path.join(os.path.dirname(__file__), r'../com'))
from utils import b2h, ftime
from si import Server

charsets = ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'euc-jp', 'euc-kr', 'iso-8859-2', 'shift_jis')

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

    if action == 'last':
        lastdir = self.config.get('file', 'lastdir')
        lastfile = self.config.get('file', 'lastfile')
        self.write({'code': 0, 'msg': '', 'data': {'lastdir': lastdir, 'lastfile': lastfile}})
        
    elif action == 'listdir':
        path = self.get_argument('path', '')
        showhidden = self.get_argument('showhidden', 'off')
        remember = self.get_argument('remember', 'on')
        onlydir = self.get_argument('onlydir', 'off')
        items = listdir(_u(path), showhidden=='on', onlydir=='on')
        if items == False:
            self.write({'code': -1, 'msg': u'目录 %s 不存在！' % path})
        else:
            if remember == 'on': self.config.set('file', 'lastdir', path)
            self.write({'code': 0, 'msg': u'成功获取文件列表！', 'data': items})
        
    elif action == 'getitem':
        path = self.get_argument('path', '')
        item = getitem(_u(path))
        if item == False:
            self.write({'code': -1, 'msg': u'%s 不存在！' % path})
        else:
            self.write({'code': 0, 'msg': u'成功获取 %s 的信息！' % path, 'data': item})

    elif action == 'fread':
        path = self.get_argument('path', '')
        remember = self.get_argument('remember', 'on')
        size = fsize(_u(path))
        if size == None:
            self.write({'code': -1, 'msg': u'文件 %s 不存在！' % path})
        elif size > 1024*1024: # support 1MB of file at max
            self.write({'code': -1, 'msg': u'读取 %s 失败！不允许在线编辑超过1MB的文件！' % path})
        elif not istext(_u(path)):
            self.write({'code': -1, 'msg': u'读取 %s 失败！无法识别文件类型！' % path})
        else:
            if remember == 'on': self.config.set('file', 'lastfile', path)
            with open(path) as f: content = f.read()
            charset, content = decode(content)
            if not charset:
                self.write({'code': -1, 'msg': u'不可识别的文件编码！'})
                return
            data = {
                'filename': os.path.basename(path),
                'filepath': path,
                'mimetype': mimetype(_u(path)),
                'charset': charset,
                'content': content,
            }
            self.write({'code': 0, 'msg': u'成功读取文件内容！', 'data': data})

    elif action == 'fclose':
        self.config.set('file', 'lastfile', '')
        self.write({'code': 0, 'msg': ''})

    elif action == 'fwrite':
        path = self.get_argument('path', '')
        charset = self.get_argument('charset', '')
        content = self.get_argument('content', '')

        if self.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                return

        if not charset in charsets:
            self.write({'code': -1, 'msg': u'不可识别的文件编码！'})
            return
        content = encode(content, charset)
        if not content:
            self.write({'code': -1, 'msg': u'文件编码转换出错，保存失败！'})
            return
        if fsave(_u(path), content):
            self.write({'code': 0, 'msg': u'文件保存成功！'})
        else:
            self.write({'code': -1, 'msg': u'文件保存失败！'})

    elif action == 'createfolder':
        path = self.get_argument('path', '')
        name = self.get_argument('name', '')

        if self.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                return

        if dadd(_u(path), _u(name)):
            self.write({'code': 0, 'msg': u'文件夹创建成功！'})
        else:
            self.write({'code': -1, 'msg': u'文件夹创建失败！'})

    elif action == 'createfile':
        path = self.get_argument('path', '')
        name = self.get_argument('name', '')

        if self.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                return

        if fadd(_u(path), _u(name)):
            self.write({'code': 0, 'msg': u'文件创建成功！'})
        else:
            self.write({'code': -1, 'msg': u'文件创建失败！'})

    elif action == 'rename':
        path = self.get_argument('path', '')
        name = self.get_argument('name', '')

        if self.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                self.write({'code': -1, 'msg': u'DEMO状态不允许修改除 /var/www 以外的目录！'})
                return

        if rename(_u(path), _u(name)):
            self.write({'code': 0, 'msg': u'重命名成功！'})
        else:
            self.write({'code': -1, 'msg': u'重命名失败！'})

    elif action == 'exist':
        path = self.get_argument('path', '')
        name = self.get_argument('name', '')
        self.write({'code': 0, 'msg': '', 'data': os.path.exists(os.path.join(path, name))})

    elif action == 'link':
        srcpath = self.get_argument('srcpath', '')
        despath = self.get_argument('despath', '')

        if self.config.get('runtime', 'mode') == 'demo':
            if not despath.startswith('/var/www') and not despath.startswith(self.settings['package_path']):
                self.write({'code': -1, 'msg': u'DEMO状态不允许在除 /var/www 以外的目录下创建链接！'})
                return

        if link(_u(srcpath), _u(despath)):
            self.write({'code': 0, 'msg': u'链接 %s 创建成功！' % despath})
        else:
            self.write({'code': -1, 'msg': u'链接 %s 创建失败！' % despath})
    
    elif action == 'delete':
        paths = self.get_argument('paths', '')
        paths = paths.split(',')

        if self.config.get('runtime', 'mode') == 'demo':
            for path in paths:
                if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': u'DEMO状态不允许在除 /var/www 以外的目录执行删除操作！'})
                    return

        if len(paths) == 1:
            path = paths[0]
            if delete(_u(path)):
                self.write({'code': 0, 'msg': u'已将 %s 移入回收站！' % path})
            else:
                self.write({'code': -1, 'msg': u'将 %s 移入回收站失败！' % path})
        else:
            for path in paths:
                if not delete(_u(path)):
                    self.write({'code': -1, 'msg': u'将 %s 移入回收站失败！' % path})
                    return
            self.write({'code': 0, 'msg': u'批量移入回收站成功！'})

    elif action == 'tlist':
        self.write({'code': 0, 'msg': '', 'data': tlist()})

    elif action == 'trashs':
        self.write({'code': 0, 'msg': '', 'data': trashs()})

    elif action == 'titem':
        mount = self.get_argument('mount', '')
        uuid = self.get_argument('uuid', '')
        info = titem(_u(mount), _u(uuid))
        if info:
            self.write({'code': 0, 'msg': '', 'data': info})
        else:
            self.write({'code': -1, 'msg': '获取项目信息失败！'})

    elif action == 'trestore':
        mount = self.get_argument('mount', '')
        uuid = self.get_argument('uuid', '')
        info = titem(_u(mount), _u(uuid))
        if info and trestore(_u(mount), _u(uuid)):
            self.write({'code': 0, 'msg': u'已还原 %s 到 %s！' % \
                (_d(info['name']), _d(info['path']))})
        else:
            self.write({'code': -1, 'msg': u'还原失败！'})

    elif action == 'tdelete':
        mount = self.get_argument('mount', '')
        uuid = self.get_argument('uuid', '')
        info = titem(_u(mount), _u(uuid))
        if info and tdelete(_u(mount), _u(uuid)):
            self.write({'code': 0, 'msg': u'已删除 %s！' % _d(info['name'])})
        else:
            self.write({'code': -1, 'msg': u'删除失败！'})
def listdir(path, showdotfiles=False, onlydir=None):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path): return False
    items = sorted(os.listdir(path))
    if not showdotfiles:
        items = [item for item in items if not item.startswith('.')]
    for i, item in enumerate(items):
        items[i] = getitem(os.path.join(path, item))
    # let folders list before files
    rt = []
    for i in xrange(len(items)-1, -1, -1):
        if items[i]['isdir'] \
            or items[i]['islnk'] \
                and not items[i]['link_broken'] \
                and items[i]['link_isdir']:
            rt.insert(0, items.pop(i))
    # check if only list directories
    if not onlydir: rt.extend(items)
    return rt

def getitem(path):
    if not os.path.exists(path) and not os.path.islink(path): return False
    name = os.path.basename(path)
    basepath = os.path.dirname(path)
    stat = os.lstat(path)
    mode = stat.st_mode
    try:
        uname = pwd.getpwuid(stat.st_uid).pw_name
    except:
        uname = ''
    try:
        gname = grp.getgrgid(stat.st_gid).gr_name
    except:
        gname = ''
    item = {
        'name': name,
        'isdir': S_ISDIR(mode),
        #'ischr': S_ISCHR(mode),
        #'isblk': S_ISBLK(mode),
        'isreg': S_ISREG(mode),
        #'isfifo': S_ISFIFO(mode),
        'islnk': S_ISLNK(mode),
        #'issock': S_ISSOCK(mode),
        'perms': oct(stat.st_mode & 0777),
        'uid': stat.st_uid,
        'gid': stat.st_gid,
        'uname': uname,
        'gname': gname,
        'size': b2h(stat.st_size),
        'atime': ftime(stat.st_atime),
        'mtime': ftime(stat.st_mtime),
        'ctime': ftime(stat.st_ctime),
    }
    if item['islnk']:
        linkfile = os.readlink(path)
        item['linkto'] = linkfile
        if not linkfile.startswith('/'):
            linkfile = os.path.abspath(os.path.join(basepath, linkfile))
        try:
            stat = os.stat(linkfile)
            item['link_isdir'] = S_ISDIR(stat.st_mode)
            item['link_isreg'] = S_ISREG(stat.st_mode)
            item['link_broken'] = False
        except:
            item['link_broken'] = True
    return item

def rename(oldpath, newname):
    path = os.path.abspath(oldpath)
    if not os.path.exists(oldpath): return False
    try:
        basepath = os.path.dirname(oldpath)
        newpath = os.path.join(basepath, newname)
        os.rename(oldpath, newpath)
        return True
    except:
        return False

def link(srcpath, despath):
    try:
        os.symlink(srcpath, despath)
        return True
    except:
        return False

def dadd(path, name):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path): return False
    dpath = os.path.join(path, name)
    if os.path.exists(dpath): return False
    try:
        os.mkdir(dpath)
        return True
    except:
        return False

def istext(path):
    if not os.path.exists('/usr/file') and not os.path.exists('/usr/bin/file'):
        return True
    return (re.search(r':(.* text|.* empty)',
            subprocess.Popen(["file", '-L', path], 
                            stdout=subprocess.PIPE).stdout.read())
            is not None)

def mimetype(filepath):
    if not os.path.exists(filepath): return False
    if os.path.islink(filepath):
        linkfile = os.readlink(filepath)
        if linkfile.startswith('/'):
            filepath = linkfile
        else:
            basepath = os.path.dirname(filepath)
            filepath = os.path.abspath(os.path.join(basepath, linkfile))
        if not os.path.exists(filepath): return False
    mime = magic.from_file(filepath, mime=True)
    # sometimes it still return like "text/plain; charset=us-ascii"
    if ';' in mime: mime = mime.split(';', 1)[0]
    if mime == 'text/plain':
        tmime = mimetypes.guess_type(filepath)[0]
        if tmime: mime = tmime 
    return mime

def fsize(filepath):
    if not os.path.exists(filepath): return None
    return os.lstat(filepath).st_size

def fadd(path, name):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path): return False
    fpath = os.path.join(path, name)
    if os.path.exists(fpath): return False
    try:
        with open(fpath, 'w'): pass
        return True
    except:
        return False

def fsave(path, content, bakup=True):
    if not os.path.exists(path): return False
    try:
        if bakup:
            dirname = os.path.dirname(path)
            filename = '.%s.bak' % os.path.basename(path)
            os.rename(path, os.path.join(dirname, filename))
        with open(path, 'w') as f: f.write(content)
        return True
    except:
        return False

def decode(content):
    """Detect charset of content and decode it.
    """
    for charset in charsets:
        try:
            content = content.decode(charset)
            return (charset, content)
        except:
            pass
    return (None, content)

def encode(content, charset):
    """Encode content using specified charset.
    """
    try:
        return content.encode(charset)
    except:
        return False

def delete(path):
    if not os.path.exists(path) and not os.path.islink(path): return False
    path = os.path.realpath(path)
    mounts = _getmounts()
    mount = ''
    for m in mounts:
        if path.startswith(m):
            mount = m
            break
    if not mount: return False
    trashpath = os.path.join(mount, '.deleted_files')
    _inittrash(mounts)
    try:
        uuid = str(uuid4())
        db = anydbm.open(os.path.join(trashpath, '.fileinfo'), 'c')
        db[uuid] = '\t'.join([os.path.basename(path), path, str(int(time.time()))])
        db.close()
        os.rename(path, os.path.join(trashpath, uuid))
        # deal with the .filename.bak
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        bakfilepath = os.path.join(dirname, '.%s.bak' % filename)
        if os.path.exists(bakfilepath): return delete(bakfilepath)
        return True
    except:
        return False

def _getmounts():
    mounts = Server.mounts()
    mounts = [mount['path'] for mount in mounts]
    # let the longest path at the first
    mounts.sort(lambda x,y: cmp(len(y),len(x)))
    return mounts

def _inittrash(mounts=None):
    # initialize the trash
    if not mounts: mounts = _getmounts()
    for mount in mounts:
        trashpath = os.path.join(mount, '.deleted_files')
        if not os.path.exists(trashpath):
            os.mkdir(trashpath)
            metafile = os.path.join(trashpath, '.fileinfo')
            anydbm.open(metafile, 'c').close()

def trashs():
    """Return trash path list.
    """
    mounts = _getmounts()
    return [os.path.join(mount, '.deleted_files') for mount in mounts]

def tlist():
    mounts = _getmounts()
    _inittrash(mounts)
    # gather informations in each mount point's trash
    items = []
    for mount in mounts:
        db = anydbm.open(os.path.join(mount, '.deleted_files', '.fileinfo'), 'c')
        for uuid, info in db.iteritems():
            fields = info.split('\t')
            item = {
                'uuid': uuid,
                'name': fields[0],
                'path': fields[1],
                'time': ftime(float(fields[2])),
                'mount': mount
            }
            filepath = os.path.join(mount, '.deleted_files', uuid)
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                item['isdir'] = S_ISDIR(stat.st_mode)
                item['isreg'] = S_ISREG(stat.st_mode)
                item['islnk'] = S_ISLNK(stat.st_mode)
            items.append(item)
        db.close()
    items.sort(lambda x,y: cmp(y['time'], x['time']))
    return items

def titem(mount, uuid):
    #_inittrash()
    try:
        trashpath = os.path.join(mount, '.deleted_files')
        db = anydbm.open(os.path.join(trashpath, '.fileinfo'), 'c')
        info = db[uuid]
        db.close()
        fields = info.split('\t')
        info = {
            'uuid': uuid,
            'name': fields[0],
            'path': fields[1],
            'time': ftime(float(fields[2])),
            'mount': mount
        }
        info['realpath'] = os.path.join(trashpath, uuid)
        return info
    except:
        return False

def trestore(mount, uuid):
    #_inittrash()
    try:
        info = titem(mount, uuid)
        trashpath = os.path.join(mount, '.deleted_files')
        os.rename(os.path.join(trashpath, uuid), info['path'])
        db = anydbm.open(os.path.join(trashpath, '.fileinfo'), 'c')
        del db[uuid]
        db.close()
        return True
    except:
        return False

def tdelete(mount, uuid):
    # the real file or directory should be deleted external
    #_inittrash()
    try:
        db = anydbm.open(os.path.join(mount, '.deleted_files', '.fileinfo'), 'c')
        del db[uuid]
        db.close()
        return True
    except:
        return False

def chown(path, user, group, recursively=False):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    try:
        userid = groupid = -1
        if user: userid = pwd.getpwnam(user).pw_uid
        if group: groupid = grp.getgrnam(group).gr_gid
        if os.path.isdir(path) and recursively:
            for root, dirs, files in os.walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath): continue  # maybe broken link
                    os.chown(tpath, userid, groupid)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath): continue
                    os.chown(tpath, userid, groupid)
        os.chown(path, userid, groupid)
    except:
        return False
    return True

def chmod(path, perms, recursively=False):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    try:
        if os.path.isdir(path) and recursively:
            for root, dirs, files in os.walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath): continue  # maybe broken link
                    os.chmod(tpath, perms)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath): continue
                    os.chmod(tpath, perms)
        os.chmod(path, perms)
    except:
        return False
    return True


if __name__ == '__main__':
    print '* List directory of /root:'
    for item in listdir('/root'):
        print '  name: %s' % item['name']
        print '  isdir: %s' % str(item['isdir'])
        print '  isreg: %s' % str(item['isreg'])
        print '  islnk: %s' % str(item['islnk'])
        print '  perms: %s' % str(item['perms'])
        print '  uname: %s' % item['uname']
        print '  gname: %s' % item['gname']
        print '  size: %s' % item['size']
        print '  atime: %s' % item['atime']
        print '  mtime: %s' % item['mtime']
        print '  ctime: %s' % item['ctime']
        print '  istext: %s' % str(istext(os.path.join('/root', item['name'])))
        print '  mimetype: %s' % mimetype(os.path.join('/root', item['name']))
        print 
    print 
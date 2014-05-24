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



"""Package for fdisk operations.
"""

import os
if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import pexpect
import shlex

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
    devname = self.get_argument('devname', '')

    if action == 'add':
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许添加分区！'})
            return

        size = self.get_argument('size', '')
        unit = self.get_argument('unit', '')

        if unit not in ('M', 'G'):
            self.write({'code': -1, 'msg': u'错误的分区大小！'})
            return

        if size == '':
            size = None # use whole left space
        else:
            try:
                size = float(size)
            except:
                self.write({'code': -1, 'msg': u'错误的分区大小！'})
                return

            if unit == 'G' and size-int(size) > 0:
                size *= 1024
                unit = 'M'
            size = '%d%s' % (round(size), unit)

        if add('/dev/%s' % _u(devname), _u(size)):
            self.write({'code': 0, 'msg': u'在 %s 设备上创建分区成功！' % devname})
        else:
            self.write({'code': -1, 'msg': u'在 %s 设备上创建分区失败！' % devname})

    elif action == 'delete':
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许删除分区！'})
            return

        if delete('/dev/%s' % _u(devname)):
            # remove config from /etc/fstab
            sc.Server.fstab(_u(devname), {
                'devname': _u(devname),
                'mount': None,
            })
            self.write({'code': 0, 'msg': u'分区 %s 删除成功！' % devname})
        else:
            self.write({'code': -1, 'msg': u'分区 %s 删除失败！' % devname})

    elif action == 'scan':
        if fdisk.scan('/dev/%s' % _u(devname)):
            self.write({'code': 0, 'msg': u'扫描设备 %s 的分区成功！' % devname})
        else:
            self.write({'code': -1, 'msg': u'扫描设备 %s 的分区失败！' % devname})

    else:
        self.write({'code': -1, 'msg': u'未定义的操作！'})

def add(disk, size=''):
    """Add a new partition on a disk.

    If the size exceed the max available space the disk left, then the
    new partition will be created with the left space.
    
    A disk can have 4 partitions at max.
    
    True will return if create successfully, or else False will return.
    
    Example:
    fdisk.add('/dev/sdb')   # use all of the space
    fdisk.add('/dev/sdb', '5G') # create a partition with at most 5G space
    """
    try:
        cmd = shlex.split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    
    rt = True
    partno_found = False
    partno = 1
    while not partno_found:
        child.sendline('n')
        i = child.expect(['primary partition', 'You must delete some partition'])
        if i == 1: break
        child.sendline('p')

        i = child.expect(['Partition number', 'Selected partition'])
        if i == 0: child.sendline('%d' % partno)

        i = child.expect(['First cylinder', '(m for help)'])
        if i == 0: partno_found = True
        partno += 1
        if partno > 4: break
    
    if not partno_found: rt = False

    if rt:
        child.sendline('')
        child.expect('Last cylinder')
        child.sendline('+%s' % size)
        i = child.expect(['(m for help)', 'Value out of range', 'Last cylinder'])
        if i == 1:
            child.sendline('')
            child.expect('(m for help)')
        elif i == 2:    # wrong size input
            child.sendline('')
            child.expect('(m for help)')
            rt = False

    if rt:
        child.sendline('w')
    else:
        child.sendline('q')

    if child.isalive(): child.wait()
    return rt


def delete(partition):
    """Delete a partition.

    True will return if delete successfully, or else False will return.
    
    Example:
    fdisk.delete('/dev/sdb1')
    """
    disk = partition[:-1]
    partno = partition[-1:]
    try:
        cmd = shlex.split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline('d')

    rt = True
    i = child.expect([
            'Partition number',
            'Selected partition %s' % partno,
            'No partition is defined yet',
            pexpect.TIMEOUT
        ], timeout=1)
    if i == 0:
        child.sendline(partno)
    elif i == 2 or i == 3:
        rt = False
    
    if rt:
        i = child.expect(['(m for help)', 'has empty type'])
        if i == 0:
            child.sendline('w')
        elif i == 1:
            rt = False

    if not rt: child.sendline('q')

    if child.isalive(): child.wait()
    return rt


def scan(disk, size=''):
    """Rescan partitions on a disk.
    
    True will return if scan successfully, or else False will return.
    
    Example:
    fdisk.scan('/dev/sdb')
    """
    try:
        cmd = shlex.split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        child.wait()
        return False

    child.sendline('w')
    i = child.expect([
            'The kernel still uses the old table',
            pexpect.TIMEOUT,
            pexpect.EOF
        ], timeout=1)
    if i == 0:
        rt = False
    else:
        rt = True
        
    if child.isalive(): child.wait()
    return rt


if __name__ == '__main__':
# !!!!!!!!!!! DANGEROUS TESTING !!!!!!!!!!!
#    print '* Add partition to sdb with 5G:',
#    print add('/dev/sdb', '5G')
    
#    print '* Delete partition /dev/sdb1:',
#    print delete('/dev/sdb1')

    print '* Rescan partitions of /dev/sdb:',
    print scan('/dev/sdb')
    print 
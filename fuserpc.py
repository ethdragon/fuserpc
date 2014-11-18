from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time
from xmlrpclib import Binary
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import Proxy, getopt, sys, math
import sys, pickle, xmlrpclib

class Memory(LoggingMixIn, Operations):
  """Example memory filesystem. Supports only one level of files."""
  def __init__(self, ht):
    self.files = ht
    self.fd = 0
    now = time()
    if '/' not in self.files:
      self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
        st_mtime=now, st_atime=now, st_nlink=2, contents=['/'])

  def chmod(self, path, mode):
    ht = self.files[path]
    ht['st_mode'] &= 077000
    ht['st_mode'] |= mode
    self.files[path] = ht
    return 0

  def chown(self, path, uid, gid):
    ht = self.files[path]
    if uid != -1:
      ht['st_uid'] = uid
    if gid != -1:
      ht['st_gid'] = gid
    self.files[path] = ht
  
  '''Data and meta are separated here'''
  def create(self, path, mode):
    self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1, st_size=0,
        st_ctime=time(), st_mtime=time(), st_atime=time(), contents='',
        tk_size=0, tk_piece=[], bk_piece=[], tk_name=[]) # for data stripping
    
    '''The next statement needs to be changed'''
    self.files[pickle.dumps(path)] = ''

    ht = self.files['/']
    ht['contents'].append(path)
    ht['st_nlink'] += 1
    self.files['/'] = ht

    self.fd += 1
    return self.fd
  
  def getattr(self, path, fh=None):
    if path not in self.files['/']['contents']:
      raise FuseOSError(ENOENT)
    return self.files[path]
  
  def getxattr(self, path, name, position=0):
    attrs = self.files[path].get('attrs', {})
    try:
      return attrs[name]
    except KeyError:
      return ''    # Should return ENOATTR
  
  def listxattr(self, path):
    return self.files[path].get('attrs', {}).keys()
  
  def mkdir(self, path, mode):
    self.files[path] = dict(st_mode=(S_IFDIR | mode),
        st_nlink=2, st_size=0, st_ctime=time(), st_mtime=time(),
        st_atime=time(), contents=[])
    ht = self.files['/']
    ht['st_nlink'] += 1
    ht['contents'].append(path)
    self.files['/'] = ht

  def open(self, path, flags):
    self.fd += 1
    return self.fd
  
  def read(self, path, size, offset, fh):
    remain = offset%4096
    piece = int(math.floor(offset/4096.0))
    begin = 0
    if remain != 0:
      begin = 4095-remain
    data = self.files[pickle.dumps(path)+str(piece)][begin:]
    piece += 1
    size -= (4096-remain)
    while size >= 4096:
      data += self.files[pickle.dumps(path)+str(piece)]
      piece += 1
      size -= 4096
    if size > 0:
      data += self.files[pickle.dumps(path)+str(piece)][:size]
    return data
  
  def readdir(self, path, fh):
    return ['.', '..'] + [x[1:] for x in self.files['/']['contents'] if x != '/']
  
  def readlink(self, path):
    return self.files[path]['contents']
  
  def removexattr(self, path, name):
    ht = self.files[path]
    attrs = ht.get('attrs', {})
    if name in attrs:
      del attrs[name]
      ht['attrs'] = attrs
      self.files[path] = ht
    else:
      pass    # Should return ENOATTR
  
  def rename(self, old, new):
    '''
    sure to have problem
    '''
    meta = self.files[old]
    self.files[new] = meta
    size = meta['st_size']
    del self.files[old]

    # Problem here
    piece = int(math.ceil(size/4096.0))
    for i in range(piece):
      f = self.files[pickle.dumps(old)+str(i)]
      self.files[pickle.dumps(new)+str(i)] = f
      del self.files[pickle.dumps(old)+str(i)]
    
    ht = self.files['/']
    ht['contents'].remove(old)
    ht['contents'].append(new)
    self.files['/'] = ht
  
  def rmdir(self, path):
    del self.files[path]
    ht = self.files['/']
    ht['st_nlink'] -= 1
    ht['contents'].remove(path)
    self.files['/'] = ht
  
  def setxattr(self, path, name, value, options, position=0):
    # Ignore options
    ht = self.files[path]
    attrs = ht.get('attrs', {})
    attrs[name] = value
    ht['attrs'] = attrs
    self.files[path] = ht
  
  def statfs(self, path):
    return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)
  
  def symlink(self, target, source):
    self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
      st_size=len(source), contents=source)

    ht = self.files['/']
    ht['st_nlink'] += 1
    ht['contents'].append(target)
    self.files['/'] = ht
  
  def truncate(self, path, length, fh=None):
    ht = self.files[path]
    size = ht['st_size']
    lmax = int(math.ceil(size/4096.0))
    remain = length%4096
    piece = int(math.floor(length/4096.0))
    data = self.files[pickle.dumps(path)+str(piece)]
    n_data = data[:remain]
    self.files[pickle.dumps(path)+str(piece)] = n_data
    for i in range(remain+1, lmax):
      del files[pickle.dumps(path)+str(i)]
    ht['st_size'] = length
    self.files[path] = ht
  
  def unlink(self, path):
    ht = self.files['/']
    ht['contents'].remove(path)
    self.files['/'] = ht
    del self.files[path]
  
  def utimens(self, path, times=None):
    now = time()
    ht = self.files[path]
    atime, mtime = times if times else (now, now)
    ht['st_atime'] = atime
    ht['st_mtime'] = mtime
    self.files[path] = ht
  
  def write(self, path, data, offset, fh):
    # Get file data
    ht = self.files[path]
    remain = offset%4096
    piece = int(math.floor(offset/4096.0))
    if remain != 0:
      o_data = self.files[pickle.dumps(path)+str(piece)]
      n_data = o_data + data
      self.files[pickle.dumps(path)+str(piece)] = n_data
    else:
      self.files[pickle.dumps(path)+str(piece)] = data
      
    size = len(data) + offset
    ht['st_size'] = size
    self.files[path] = ht
    return len(data)

if __name__ == "__main__":
  if len(argv) < 3:
    print 'usage: %s <mountpoint> <ip:port1> <ip:port2> ....' % argv[0]
    exit(1)
  url = argv[2:]
  enProxy = Proxy.EnhancedProxy(url)
  # Create a new HtProxy object using the URL specified at the command-line
  fuse = FUSE(Memory(enProxy), argv[1], foreground=True)
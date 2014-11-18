#!/usr/bin/env python
'''
Author: Yang LIU
'''
from collections import defaultdict
from errno import ENOENT

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from xmlrpclib import Binary
import sys, pickle, xmlrpclib
import threading, math

class EnhancedProxy:
    """ Wrapper functions so the FS doesn't need to worry about HT primitives."""
    # A hashtable supporting atomic operations, i.e., retrieval and setting
    # must be done in different operations
    def __init__(self, url):
        self.hdata = {}
        self.proxy = []
        self.n = len(url)
        self.url = url
      
    # Retrieves a value from the SimpleHT, returns KeyError, like dictionary, if
    # there is no entry in the SimpleHT
    def __getitem__(self, key):
        filename = ''
        threadlist = []
        #print type(key), key
        if type(key) != str and type(key) != unicode:
            #print type(key)
            filename = key.data
            meta = pickle.loads(self.get(filename))
            if meta == None:
                raise KeyError()
            #print meta
            size = meta['st_size']
            piece = 0
            if size%4096 != 0:
                piece = int(math.floor(size/4096.0))+1
            else:
                piece = size/4096

            pkey = pickle.dumps(filename)
            keystr = [pkey+str(i) for i in range(piece)]
            for keys in keystr:
                t = threading.Thread(target=self.get2, args=(keys,))
                t.daemon = True
                t.start()
                threadlist.append(t)

            for t in threadlist:
                t.join()

            data = ""
            for keys in keystr:
                #print 'keys: ~~~~~', keys
                data += pickle.loads(self.hdata[keys])
                del self.hdata[keys]

            self.hdata.clear()
            return data

        rv = self.get(key)
        if rv == None:
            raise KeyError()

        return pickle.loads(rv)
    
  # Stores a value in the SimpleHT
    def __setitem__(self, key, value):
        if type(value) == str:
            pass
            #print 'value is str'
        elif type(value) == dict:
            pass
            #print "value is dict"
        else:
            pass
            #print 'value is other type'
        self.put(key, pickle.dumps(value))

    # Sets the TTL for a key in the SimpleHT to 0, effectively deleting it
    def __delitem__(self, key):
        self.put(key, "", 0)
      
    # Retrieves a value from the DHT, if the results is non-null return true,
    # otherwise false
    def __contains__(self, key):
        return self.get(key) != None

    def get(self, key):
        sel = (hash(key) % self.n)
        sernum = len(self.url)
        res = {}
        ite = 0
        while ite < 5:
        	try:
        		rpc = xmlrpclib.Server(self.url[sel])
        		res = rpc.get(Binary(key))
        		break
        	except:
        		pass
        	try:
        		if sel == sernum-1:
        			rpc = xmlrpclib.Server(self.url[0])
        			res = rpc.get(Binary(key))
        		else:
        			rpc = xmlrpclib.Server(self.url[sel+1])
        			res = rpc.get(Binary(key))
        	except:
        		pass
        	ite = ite + 1
        	
        if "value" in res:
            return res["value"].data
        else:
            return None

    def get2(self, key):
        #print '====get2=====', key
        sel = (hash(key) % self.n)
        sernum = len(self.url)
        res = {}
        ite = 0
        while ite < 5:
        	try:
        		rpc = xmlrpclib.Server(self.url[sel])
        		res = rpc.get(Binary(key))
        		break
        	except:
        		pass
        	try:
        		if sel == sernum-1:
        			rpc = xmlrpclib.Server(self.url[0])
        			res = rpc.get(Binary(key))
        		else:
        			rpc = xmlrpclib.Server(self.url[sel+1])
        			res = rpc.get(Binary(key))
        	except:
        		pass
        	ite = ite + 1
        if "value" in res:
            self.hdata[key] = res["value"].data

    def put(self, key, val, ttl=10000):
        sel = (hash(key) % self.n)
        rpc = xmlrpclib.Server(self.url[sel])
        return rpc.put(Binary(key), Binary(val), ttl)
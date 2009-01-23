import imp
import sys
from nose.config import Config
from nose.plugins.manager import NoPlugins
from nose.util import odict


def mod(name):
    m = imp.new_module(name)
    sys.modules[name] = m
    return m
    
    

class RecordingPluginManager(object):

    def __init__(self):
        self.reset()

    def __getattr__(self, call):
        return RecordingPluginProxy(self, call)

    def null_call(self, call, *arg, **kw):
        return getattr(self._nullPluginManager, call)(*arg, **kw)

    def reset(self):
        self._nullPluginManager = NoPlugins()
        self.called = odict()

    def calls(self):
        return list(self.called.keys())


class RecordingPluginProxy(object):

    def __init__(self, manager, call):
        self.man = manager
        self.call = call

    def __call__(self, *arg, **kw):
        self.man.called.setdefault(self.call, []).append((arg, kw))
        return self.man.null_call(self.call, *arg, **kw)


class Bucket(object):
    def __init__(self, **kw):
        self.__dict__['d'] = {}
        self.__dict__['d'].update(kw)
        
    def __getattr__(self, attr):
        if 'd' not in self.__dict__:
            return None
        return self.__dict__['d'].get(attr)

    def __setattr__(self, attr, val):        
        self.d[attr] = val


class MockOptParser(object):
    def __init__(self):
        self.opts = []
    def add_option(self, *args, **kw):
        self.opts.append((args, kw))

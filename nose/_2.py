from __future__ import print_function
import ConfigParser as configparser

def reraise(exc_class, exc_val, tb):
    raise exc_class, exc_val, tb

def prt(*terms, **kw):
    print(*[unicode(t) for t in terms], end=u"\n", sep=u" ", **kw)

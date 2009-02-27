try:
    from nose._3 import *
except (ImportError, SyntaxError):
    from nose._2 import *

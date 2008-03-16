from nose.plugins.skip import SkipTest
from todo import Todo

def test_pass():
    pass

def test_fail():
    assert False, "I failed"

def test_error():
    print 1/0

def test_skip():
    raise SkipTest("skip me")

def test_todo():
    raise Todo("Do something later")

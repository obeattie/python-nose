called = []

def globs(globs):
    globs['something'] = 'Something?'
    return globs

def setup_module(module):
    module.called[:] = []

def setup_test(test):
    called.append(test)
    test.globs['count'] = len(called)

def teardown_test(test):
    pass

import os
import sys
import unittest
from nose.plugins.performance import Performance
from nose.plugins import PluginTester

support = os.path.join(os.path.dirname(__file__), 'support')

class TestPerformancePlugin(PluginTester, unittest.TestCase):
    activate = "--performance"
    args = ['--iters', '5']
    plugins = [Performance()]
    suitepath = os.path.join(support, 'perf')

    def runTest(self):
        print '+' * 70
        print str(self.output)
        print '+' * 70
        
        assert 'perf_method (test_perf.PerformanceTest)' in self.output
        assert 'test_perf.perf_function' in self.output
        assert 'Ran 10 tests in' in self.output
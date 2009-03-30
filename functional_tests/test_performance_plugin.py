import os
import sys
import unittest
import tempfile
import csv

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


class TestPerformancePluginCsvReport(PluginTester, unittest.TestCase):
    
    csv_report = tempfile.mktemp()
    activate = "--performance"
    args = ['--performance-csv', csv_report]
    plugins = [Performance()]
    suitepath = os.path.join(support, 'perf')

    def runTest(self):
        output = file(self.csv_report).read()
        print '+' * 70
        print output
        print '+' * 70
        
        # check this parses as csv
        parser = csv.reader(file(self.csv_report))
        for line in parser:
            pass
        
        # check contents
        assert 'perf_method (test_perf.PerformanceTest),' in output
        assert 'test_perf.perf_function,' in output

import os
import unittest
from cStringIO import StringIO
from nose.core import TestProgram
from nose.config import Config

here = os.path.dirname(__file__)
support = os.path.join(here, 'support', 'lazy_import')

def printstrm(stream):
    stream.seek(0)
    print ""
    for line in stream:
        print "  >", line,

class TestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        self.result = unittest._TextTestResult(
            self.stream, self.descriptions, self.verbosity)
        return self.result 

class TestTestProgram(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.runner = TestRunner(stream=self.stream)
        
    def test_simple_dir_suite(self):
        prog = TestProgram(defaultTest=os.path.join(support, 
                                            'simple_suite'),
                           argv=['<TestProgram>'],
                           testRunner=self.runner,
                           config=Config(),
                           exit=False)
        res = self.runner.result
        printstrm(self.stream)
        self.assertEqual(res.testsRun, 1,
                         "Expected to run 1 test, ran %s" % res.testsRun)
        assert res.wasSuccessful()
        assert not res.errors
        assert not res.failures
        
    def test_simple_module_suite(self):
        prog = TestProgram(defaultTest=os.path.join(support, 
                                            'simple_suite_as_module'),
                           argv=['<TestProgram>'],
                           testRunner=self.runner,
                           config=Config(),
                           exit=False)
        res = self.runner.result
        printstrm(self.stream)
        self.assertEqual(res.testsRun, 1,
                         "Expected to run 1 test, ran %s" % res.testsRun)
        assert res.wasSuccessful()
        assert not res.errors
        assert not res.failures
        
if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
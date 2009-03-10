from __future__ import print_function
import unittest
from nose.config import Config
from nose.plugins.skip import Skip, SkipTest
from nose.result import TextTestResult
from nose.compat import StringIO
from optparse import OptionParser


class TestSkipPlugin(unittest.TestCase):

    def test_api_present(self):
        sk = Skip()
        sk.addOptions
        sk.configure
        sk.prepareTestResult                

    def test_skip_output(self):
        class TC(unittest.TestCase):
            def test(self):
                raise SkipTest('skip me')

        stream = unittest._WritelnDecorator(StringIO())
        res = TextTestResult(stream, 0, 1)
        sk = Skip()
        sk.prepareTestResult(res)

        test = TC('test')
        test(res)
        assert not res.errors, "Skip was not caught: %s" % res.errors
        assert res.skipped            

        res.printErrors()
        out = stream.getvalue()
        assert out
        assert out.strip() == "S"
        assert res.wasSuccessful()

    def test_skip_output_verbose(self):

        class TC(unittest.TestCase):
            def test(self):
                raise SkipTest('skip me too')
        
        stream = unittest._WritelnDecorator(StringIO())
        res = TextTestResult(stream, 0, verbosity=2)
        sk = Skip()
        sk.prepareTestResult(res)
        test = TC('test')
        test(res)
        assert not res.errors, "Skip was not caught: %s" % res.errors
        assert res.skipped            

        res.printErrors()
        out = stream.getvalue()
        print(out)
        assert out

        assert ' ... SKIP' in out
        assert 'skip me too' in out

    def test_enabled_by_default(self):
        sk = Skip()
        assert sk.enabled, "Skip was not enabled by default"

    def test_can_be_disabled(self):
        parser = OptionParser()
        sk = Skip()
        sk.addOptions(parser)
        options, args = parser.parse_args(['--no-skip'])
        sk.configure(options, Config())
        assert not sk.enabled, "Skip was not disabled by noSkip option"
        

if __name__ == '__main__':
    unittest.main()


import sys
import unittest
from optparse import OptionParser
from nose.config import Config
from nose.plugins.logcapture import LogCapture
import logging

class TestLogCapturePlugin(unittest.TestCase):

    def test_enabled_by_default(self):
        c = LogCapture()
        assert c.enabled

    def test_can_be_disabled(self):
        parser = OptionParser()
        c = LogCapture()
        c.addOptions(parser)
        options, args = parser.parse_args(['test_can_be_disabled_long',
                                           '--nologcapture'])
        c.configure(options, Config())
        assert not c.enabled

        env = {'NOSE_NOLOGCAPTURE': 1}
        c = LogCapture()
        parser = OptionParser()
        c.addOptions(parser, env)
        options, args = parser.parse_args(['test_can_be_disabled'])
        c.configure(options, Config())
        assert not c.enabled

        c = LogCapture()
        parser = OptionParser()
        c.addOptions(parser)

        options, args = parser.parse_args(['test_can_be_disabled'])
        c.configure(options, Config())
        assert c.enabled

    def test_captures_logging(self):
        c = LogCapture()
        c.start()
        log = logging.getLogger("foobar.something")
        log.debug("Hello")
        c.end()
        self.assertEqual(1, len(c.buffer))
        self.assertEquals("Hello", c.buffer[0].msg)

    def test_custom_formatter(self):
        c = LogCapture()
        c.logformat = '++%(message)s++'
        c.start()
        log = logging.getLogger("foobar.something")
        log.debug("Hello")
        c.end()
        records = c.formatLogRecords()
        self.assertEqual(1, len(records))
        self.assertEquals("++Hello++", records[0])

if __name__ == '__main__':
    unittest.main()

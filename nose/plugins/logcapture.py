
"""
This plugin captures logging statements issued during test execution,
appending any output captured to the error or failure output, should the test fail
or raise an error. It is enabled by default but may be disabled with
the options --nologcapture.

TODO

 * Implement better formatting (more than plain %(message)s format)
 * Implement --logging-package= option, similar to --cover-package=
"""

import os
import logging
from logging.handlers import BufferingHandler

from nose.plugins.base import Plugin
from nose.util import ln

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

log = logging.getLogger(__name__)

class MyMemoryHandler(BufferingHandler):
    def flush(self):
        pass # do nothing
    def truncate(self):
        self.buffer = []

class LogCapture(Plugin):
    """
    Log capture plugin. Enabled by default. Disable with --nologcapture.
    This plugin captures logging statement issued during test execution,
    appending any output captured to the error or failure output,
    should the test fail or raise an error.
    """
    enabled = True
    env_opt = 'NOSE_NOLOGCAPTURE'
    name = 'logcapture'
    score = 500
    logformat = "%(filename)s:%(lineno)d %(message)s"

    def options(self, parser, env=os.environ):
        parser.add_option(
            "", "--nologcapture", action="store_false",
            default=not env.get(self.env_opt), dest="logcapture",
            help="Don't capture logging output [NOSE_NOLOGCAPTURE]")
        parser.add_option(
            "", "--logging-format", action="store",
            default=self.logformat, dest="logcapture_format",
            help="Formatting of the logging statements (default: %s)" % self.logformat)

    def configure(self, options, conf):
        self.conf = conf
        if not options.logcapture:
            self.enabled = False
        self.logformat = options.logcapture_format

    def setup_loghandler(self):
        # setup our handler with root logger
        root_logger = logging.getLogger()
        # unless it's already there
        if self.handler not in root_logger.handlers:
            root_logger.addHandler(self.handler)
        # to make sure everything gets captured
        root_logger.setLevel(logging.NOTSET)

    def begin(self):
        self.start()
        #import sys
        #logging.basicConfig(stream=sys.stderr)

    def start(self):
        self.handler = MyMemoryHandler(1000)
        fmt = logging.Formatter(self.logformat)
        self.handler.setFormatter(fmt)
        self.setup_loghandler()

    def end(self):
        pass

    def beforeTest(self, test):
        self.setup_loghandler()

    def afterTest(self, test):
        self.handler.truncate()

    def formatError(self, test, err):
        # logic flow copied from Capture.formatError
        records = self.formatLogRecords()
        if not records:
            return err 
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, records), tb)

    def formatLogRecords(self):
        format = self.handler.format
        return [format(r) for r in self.buffer]

    def formatFailure(self, test, err):
        return self.formatError(test, err)

    def addCaptureToErr(self, ev, records):
        return '\n'.join([str(ev), ln('>> begin captured logging <<')] + \
                          records + \
                          [ln('>> end captured logging <<')])

    def _get_buffer(self):
        return self.handler.buffer

    buffer = property(fget=_get_buffer,
                      doc="""Captured logging statements.""")

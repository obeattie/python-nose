"""
This plugin adds a test id (like #1) to each test name output. After
you've run once to generate test ids, you can re-run individual
tests by activating the plugin and passing the ids (with or
without the # prefix) instead of test names.

For example, if your normal test run looks like::

  % nosetests -v
  tests.test_a ... ok
  tests.test_b ... ok
  tests.test_c ... ok

When adding --with-id you'll see::

  % nosetests -v --with-id
  #1 tests.test_a ... ok
  #2 tests.test_b ... ok
  #2 tests.test_c ... ok

Then you can rerun individual tests by supplying just the id numbers::

  % nosetests -v --with-id 2
  #2 tests.test_b ... ok

Then you can rerun individual tests by supplying just the id numbers::

  % nosetests -v --with-id 2 3
  #2 tests.test_b ... ok
  #3 tests.test_c ... ok
  
Since most shells consider '#' a special character, you can leave it out when
specifying a test id.

Looping over failed tests
-------------------------

This plugin also adds a mode where it will direct the test run to record
failed tests, and on subsequent runs, include only the tests that failed the
last time. Activate this mode with the --failed switch::

 % nosetests -v --failed
 #1 test.test_a ... ok
 #2 test.test_b ... ERROR
 #3 test.test_c ... FAILED
 #4 test.test_d ... ok
 
And on the 2nd run, only tests #2 and #3 will run::

 % nosetests -v --failed
 #2 test.test_b ... ERROR
 #3 test.test_c ... FAILED

Then as you correct errors and tests pass, they'll drop out of subsequent
runs.

First::

 % nosetests -v --failed
 #2 test.test_b ... ok
 #3 test.test_c ... FAILED

Second::

 % nosetests -v --failed
 #3 test.test_c ... FAILED

Until finally when all tests pass, the full set will run again on the next
invocation.

First::

 % nosetests -v --failed
 #3 test.test_c ... ok

Second::
 
 % nosetests -v --failed
 #1 test.test_a ... ok
 #2 test.test_b ... ok
 #3 test.test_c ... ok
 #4 test.test_d ... ok
"""
__test__ = False

import logging
import os
from nose.plugins import Plugin
from nose.util import src

try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

log = logging.getLogger(__name__)


class TestId(Plugin):
    """
    Activate to add a test id (like #1) to each test name output. After
    you've run once to generate test ids, you can re-run individual
    tests by activating the plugin and passing the ids (with or
    without the # prefix) instead of test names. Activate with --failed
    to rerun failing tests only.
    """
    name = 'id'
    idfile = None
    collecting = True
    loopOnFailed = False
    
    def options(self, parser, env):
        Plugin.options(self, parser, env)
        parser.add_option('--id-file', action='store', dest='testIdFile',
                          default='.noseids',
                          help="Store test ids found in test runs in this "
                          "file. Default is the file .noseids in the "
                          "working directory.")
        parser.add_option('--failed', action='store_true',
                          dest='failed', default=False,
                          help="Run the tests that failed in the last "
                          "test run.")

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        if options.failed:
            self.enabled = True
            self.loopOnFailed = True
            log.debug("Looping on failed tests")
        self.idfile = os.path.expanduser(options.testIdFile)
        if not os.path.isabs(self.idfile):
            self.idfile = os.path.join(conf.workingDir, self.idfile)
        self.id = 1
        # Ids and tests are mirror images: ids are {id: test address} and
        # tests are {test address: id}
        self.ids = {}
        self.tests = {}
        self.failed = []
        # used to track ids seen when tests is filled from
        # loaded ids file
        self._seen = {}

    def finalize(self, result):
        if result.wasSuccessful():
            self.failed = []
        if self.collecting:
            ids = dict(zip(self.tests.values(), self.tests.keys()))
        else:
            ids = self.ids
        fh = open(self.idfile, 'w')
        dump({'ids': ids, 'failed': self.failed}, fh)
        fh.close()
        log.debug('Saved test ids: %s, failed %s to %s',
                  ids, self.failed, self.idfile)

    def loadTestsFromNames(self, names, module=None):
        """Translate ids in the list of requested names into their
        test addresses, if they are found in my dict of tests.
        """
        log.debug('ltfn %s %s', names, module)
        try:
            fh = open(self.idfile, 'r')
            data = load(fh)
            if 'ids' in data:
                self.ids = data['ids']
                self.failed = data['failed']
            else:
                # old ids field
                self.ids = data
                self.failed = []
            log.debug('Loaded test ids %s/failed %s from %s',
                      self.ids, self.failed, self.idfile)
            fh.close()
        except IOError:
            log.debug('IO error reading %s', self.idfile)
            return

        if self.loopOnFailed and self.failed:
            self.collecting = False
            names = self.failed
            self.failed = []
        # I don't load any tests myself, only translate names like '#2'
        # into the associated test addresses
        result = (None, map(self.tr, names))
        if not self.collecting:
            # got some ids in names, so make sure that the ids line
            # up in output with what I said they were last time
            self.tests = dict(zip(self.ids.values(), self.ids.keys()))
        return result

    def makeName(self, addr):
        log.debug("Make name %s", addr)
        filename, module, call = addr
        if filename is not None:
            head = src(filename)
        else:
            head = module
        if call is not None:
            return "%s:%s" % (head, call)
        return head
        
    def setOutputStream(self, stream):
        self.stream = stream

    def startTest(self, test):
        adr = test.address()
        if adr in self.tests:
            if self.collecting or adr in self._seen:
                self.stream.write('   ')
            else:
                self.stream.write('#%s ' % self.tests[adr])
                self._seen[adr] = 1
            return
        self.tests[adr] = self.id
        self.stream.write('#%s ' % self.id)
        self.id += 1

    def afterTest(self, test):
        # None means test never ran, False means failed/err
        if test.passed is False:
            key = str(self.tests[test.address()])
            if key not in self.failed:
                self.failed.append(key)
        
    def tr(self, name):
        log.debug("tr '%s'", name)
        try:
            key = int(name.replace('#', ''))
        except ValueError:
            return name
        log.debug("Got key %s", key)
        # I'm running tests mapped from the ids file,
        # not collecting new ones
        self.collecting = False
        if key in self.ids:
            return self.makeName(self.ids[key])
        return name
        

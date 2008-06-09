import logging
import sys
import time
import unittest
from nose.core import TextTestRunner
from nose import loader
from nose.plugins.base import Plugin
from nose.result import TextTestResult
from nose.suite import ContextSuite, ContextSuiteFactory
from nose.util import test_address
from Queue import Empty

# log = logging.getLogger(__name__)
# debugging repeat log messages
class FakeLog:
    def __init__(self, out=sys.stderr):
        self.out = out
    def debug(self, msg, *arg):
        print >> self.out, "!", msg % arg
log = FakeLog()
        
try:
    from processing import Process, Queue, Pool
except ImportError:
    Process = Queue = Pool = None
    log.debug("processing module not available")
try:
    from cStringIO import StringIO
except ImportError:
    import StringIO


class MultiProcess(Plugin):
    """
    Run tests in multiple processes. Requires processing module.
    """
    score = 1000

    def options(self, parser, env={}):
        if Process is None:
            self.can_configure = False
            self.enabled = False
            return
        parser.add_option("--processes", action="store",
                          default=env.get('NOSE_PROCESSES'),
                          dest="multiprocess_workers",
                          help="Spread test run among this many processes. "
                          "Set a number equal to the number of processors "
                          "or cores in your machine for best results. "
                          "[NOSE_PROCESSES]")
        parser.add_option("--process-timeout", action="store",
                          default=env.get('NOSE_PROCESS_TIMEOUT', 10),
                          dest="multiprocess_timeout",
                          help="Set timeout for return of results from each "
                          "test runner process. [NOSE_PROCESS_TIMEOUT]")

    def configure(self, options, config):
        self.config = config
        if options.multiprocess_workers:
            self.enabled = True
            self.config.multiprocess_workers = int(options.multiprocess_workers)
            self.config.multiprocess_timeout = int(options.multiprocess_timeout)
    
    def prepareTestLoader(self, loader):
        self.loaderClass = loader.__class__
        
    def prepareTestRunner(self, runner):
        # replace with our runner class
        return MultiProcessTestRunner(stream=runner.stream,
                                      verbosity=self.config.verbosity,
                                      config=self.config,
                                      loaderClass=self.loaderClass)


class MultiProcessTestRunner(TextTestRunner):

    def __init__(self, **kw):
        self.loaderClass = kw.pop('loaderClass', loader.defaultTestLoader)
        super(MultiProcessTestRunner, self).__init__(**kw)
    
    def run(self, test):
        wrapper = self.config.plugins.prepareTest(test)
        if wrapper is not None:
            test = wrapper
        
        # plugins can decorate or capture the output stream
        wrapped = self.config.plugins.setOutputStream(self.stream)
        if wrapped is not None:
            self.stream = wrapped

        testQueue = Queue()
        resultQueue = Queue()
        tasks = []
            
        result = self._makeResult()    
        start = time.time()
        
        # dispatch and collect results
        # put indexes only on queue because tests aren't picklable
        for case in self.next_batch(test):
            test_addr = self.address(case)
            testQueue.put(test_addr, block=False)
            tasks.append(test_addr)
            log.debug("Queued test %s (%s) to %s",
                      len(tasks), test_addr, testQueue)
            
        log.debug("Starting %s workers", self.config.multiprocess_workers)
        for i in range(self.config.multiprocess_workers):
            testQueue.put('STOP', block=False)
            # FIXME should be daemon?
            p = Process(target=runner, args=(i,
                                             testQueue,
                                             resultQueue,
                                             self.loaderClass,
                                             result.__class__,
                                             self.config))
            p.setDaemon(True)
            p.start()
            log.debug("Started worker process %s", i+1)

        log.debug("Waiting for results (%s tasks)", len(tasks))
        try:
            num_tasks = len(tasks)
            for i in range(num_tasks):
                batch_result = resultQueue.get(
                    timeout=self.config.multiprocess_timeout)                
                log.debug(">> got result %s: %s", i, batch_result)
                self.consolidate(result, batch_result)
        except Empty:
            log.debug("Timed out with %s tasks pending", num_tasks - i)
            # FIXME add a failure to result
        stop = time.time()
        result.printErrors()
        result.printSummary(start, stop)
        self.config.plugins.finalize(result)
        return result

    def address(self, case):
        if hasattr(case, 'address'):
            file, mod, call = case.address()
        elif hasattr(case, 'context'):
            file, mod, call = test_address(case.context)
        else:
            raise Exception("Unable to convert %s to address" % case)
        parts = []
        if file is None:
            if mod is None:
                raise Exception("Unaddressable case %s" % case)
            else:
                parts.append(mod)
        else:
            parts.append(file)
        if call is not None:
            parts.append(call)
        return ':'.join(map(str, parts))
            
    def next_batch(self, test):
        if ((isinstance(test, ContextSuite)
             and test.hasFixtures())
            or not getattr(test, 'can_split', True)
            or not isinstance(test, unittest.TestSuite)):
            # regular test case, or a suite with context fixtures
            # either way we've hit something we can ask a worker
            # to run
            yield test
        else:
            # Suite is without fixtures at this level; but it may have
            # fixtures at any deeper level, so we need to examine it all
            # the way down to the case level
            for case in test:
                for batch in self.next_batch(case):
                    yield batch

    def consolidate(self, result, batch_result):
        log.debug("batch result is %s" , batch_result)
        try:
            output, testsRun, failures, errors, errorClasses = batch_result
        except ValueError:
            # FIXME add a failure and return
            return 
        self.stream.write(output)
        return

        result.testsRun += testsRun
        result.failures.extend(failures)
        result.errors.extend(errors)
        for key, (storage, label, isfail) in errorClasses:
            if key not in result.errorClasses:
                # Ordinarily storage is result attribute
                # but it's only processed through the errorClasses
                # dict, so it's ok to fake it here
                result.errorClasses[key] = ([], label, isfail)
            mystorage, _junk, _junk = result.errorClasses[key]
            mystorage.extend(storage)
        log.debug("Ran % tests (%s)", testsRun, result.testsRun)

            
def runner(ix, testQueue, resultQueue, loaderClass, resultClass, config):
    resultQueue.canceljoin() # don't join on exit
        
    log.debug("Worker %s executing", ix)
    loader = loaderClass(config=config)

    def get():
        log.debug("Worker %s get from test queue %s", ix, testQueue)
        case = testQueue.get(block=False) # q must be fully populated
        log.debug("Worker %s got case %s", ix, case)
        return case
            
    def makeResult():
        stream = unittest._WritelnDecorator(StringIO())
        return resultClass(stream, descriptions=1,
                           verbosity=config.verbosity,
                           config=config)
    try:
        for test_addr in iter(get, 'STOP'):
            log.debug("Worker %s running test %s", ix, test_addr)
            result = makeResult()
            test = loader.loadTestsFromNames([test_addr])
            log.debug("Worker %s Test is %s", ix, test)
            test(result)
            tup = (
                result.stream.getvalue(),
                result.testsRun,
                result.failures,
                result.errors,
                getattr(result, 'errorClasses', {}))
            log.debug("Worker %s returning %s", ix, tup)
            resultQueue.put(tup)
    except Empty:
        resultQueue.close()
    else:
        resultQueue.close()
    log.debug("Worker %s ending", ix)


import logging
import sys
import time
import traceback
import unittest
import nose.case
from nose.core import TextTestRunner
from nose import failure
from nose import loader
from nose.plugins.base import Plugin
from nose.result import TextTestResult
from nose.suite import ContextSuite, ContextSuiteFactory
from nose.util import test_address
from Queue import Empty

log = logging.getLogger(__name__)
# debugging repeat log messages
class FakeLog:
    def __init__(self, out=sys.stderr):
        self.out = out
    def debug(self, msg, *arg):
        print >> self.out, "!", msg % arg
#log = FakeLog()
        
try:
    from processing import Process, Queue, Pool
except ImportError:
    Process = Queue = Pool = None
    log.debug("processing module not available")
try:
    from cStringIO import StringIO
except ImportError:
    import StringIO


class TestLet:
    def __init__(self, case):
        try:
            self._id = case.id()
        except AttributeError:
            pass 
        self._short_description = case.shortDescription()
        self._str = str(case)

    def id(self):
        return self._id

    def shortDescription(self):
        return self._short_description

    def __str__(self):
        return self._str


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
        tasks = {}
        completed = {}
        workers = []
            
        result = self._makeResult()    
        start = time.time()
        
        # dispatch and collect results
        # put indexes only on queue because tests aren't picklable
        for case in self.next_batch(test):
            log.debug("Next batch %s (%s)", case, type(case))
            if (isinstance(case, nose.case.Test) and
                isinstance(case.test, failure.Failure)):
                log.debug("Case is a Failure")
                case(result) # run here to capture the failure
                continue
            test_addr = self.address(case)
            testQueue.put(test_addr, block=False)
            tasks[test_addr] = None
            log.debug("Queued test %s (%s) to %s",
                      len(tasks), test_addr, testQueue)
            
        log.debug("Starting %s workers", self.config.multiprocess_workers)
        for i in range(self.config.multiprocess_workers):
            p = Process(target=runner, args=(i,
                                             testQueue,
                                             resultQueue,
                                             self.loaderClass,
                                             result.__class__,
                                             self.config))
            p.setDaemon(True)
            p.start()
            workers.append(p)
            log.debug("Started worker process %s", i+1)

        num_tasks = len(tasks)            
        while tasks:
            log.debug("Waiting for results (%s/%s tasks)",
                      len(completed), num_tasks)
            try:
                addr, batch_result = resultQueue.get(
                    timeout=self.config.multiprocess_timeout)
                log.debug('Results received for %s', addr)
                completed[addr] = batch_result
                tasks.pop(addr)
                self.consolidate(result, batch_result)
            except Empty:
                log.debug("Timed out with %s tasks pending", len(tasks))
                any_alive = False
                for w in workers:
                    if w.isAlive():
                        any_alive = True
                        break
                if not any_alive:
                    log.debug("All workers dead")
                    break
        log.debug("Completed %s/%s tasks (%s remain)",
                  len(completed), num_tasks, len(tasks))
        stop = time.time()
        
        result.printErrors()
        result.printSummary(start, stop)
        self.config.plugins.finalize(result)

        # Tell all workers to stop
        for w in workers:
            if w.isAlive():
                testQueue.put('STOP', block=False)
        
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
        # allows tests or suites to mark themselves as not safe
        # for multiprocess execution
        if hasattr(test, 'context'):
            if not getattr(test.context, '_multiprocess_', True):
                return
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

        result.testsRun += testsRun
        result.failures.extend(failures)
        result.errors.extend(errors)
        for key, (storage, label, isfail) in errorClasses.items():
            if key not in result.errorClasses:
                # Ordinarily storage is result attribute
                # but it's only processed through the errorClasses
                # dict, so it's ok to fake it here
                result.errorClasses[key] = ([], label, isfail)
            mystorage, _junk, _junk = result.errorClasses[key]
            mystorage.extend(storage)
        log.debug("Ran %s tests (%s)", testsRun, result.testsRun)

            
def runner(ix, testQueue, resultQueue, loaderClass, resultClass, config):
    log.debug("Worker %s executing", ix)
    loader = loaderClass(config=config)

    def get():
        log.debug("Worker %s get from test queue %s", ix, testQueue)
        case = testQueue.get(timeout=config.multiprocess_timeout)
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
            try:
                test(result)

                # We can't send back failures, errors, etc as is
                # since cases can't be pickled
                failures = [(TestLet(c), err) for c, err in result.failures]
                errors = [(TestLet(c), err) for c, err in result.errors]
                errorClasses = {}
                log.debug("result errorClasses %s", result.errorClasses)
                for key, (storage, label, isfail) in result.errorClasses.items():
                    errorClasses[key] = ([(TestLet(c), err) for c in storage],
                                         label, isfail)                
                tup = (
                    result.stream.getvalue(),
                    result.testsRun,
                    failures,
                    errors,
                    errorClasses)
                log.debug("Worker %s returning %s", ix, tup)
                resultQueue.put((test_addr, tup))
            except:
                # FIXME add exception info to errors list
                ec, ev, tb = sys.exc_info()
                log.debug("ec %s ev %s tb %s",
                          ec, ev, traceback.format_tb(tb))
                resultQueue.put((test_addr, ("FAILED %s" % ec, 0, [], [], {})))
    except Empty:
        log.debug("Worker %s timed out waiting for tasks", ix)
        resultQueue.close()
    else:
        resultQueue.close()
    log.debug("Worker %s ending", ix)


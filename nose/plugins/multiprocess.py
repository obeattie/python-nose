from nose.core import TextTestRunner
from nose.plugins.base import Plugin
from nose.suite import ContextSuite, ContextSuiteFactory
import sys
try:
    from processing import Process, Queue, Pool
except ImportError:
    Process = Queue = Pool = None
try:
    from cStringIO import StringIO
except ImportError:
    import StringIO

"""
Loading & running notes

Is it easier to replace the test runner or to handle everything at the suite
level

at test runner level it seems simple enough
instead of calling test(result) we do a deep iteration
def next_chunk(suite):
    for test in suite:
        if testcase or hascontext(test): yield test
        for case in next_chunk(test):
            yield case

... to get the next severable chunk of tests. Then we enqueue that, and
track it in the tasks list so we know how many answers to wait for.
            
"""

    
    
class MultiProcess(Plugin):
    score = 1000

    def prepareTestLoader(self, loader):
        loader.depthFirst = True

    def prepareTestRunner(self, runner):
        # replace with our runner class
        return MultiProcessTestRunner(stream=runner.stream,
                                      verbosity=self.config.verbosity,
                                      config=self.config)


class MultiProcessTestRunner(TextTestRunner):

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
        workers = []
        tasks = []
        for i in range(self.config.multiprocess_workers):
            workers.append(
                Process(target=Worker(testQueue,
                                      resultQueue,
                                      self.config)))
            
        result = self._makeResult()    
        start = time.time()
        
        # dispatch and collect results
        for case in self.next_batch(test):
            tasks.append(case)
            testQueue.put(case)

        for i in tasks:
            batch_result = resultQueue.get(
                block=True,
                timeout=self.config.multiprocess_timeout)
            self.stream.write(batch_result.stream.getvalue())
            self.consolidate(batch_result, result)
        stop = time.time()
        result.printErrors()
        result.printSummary(start, stop)
        self.config.plugins.finalize(result)
        return result

    def next_batch(self, test):
        if (not isinstance(test, ContextSuite)
            or test.hasFixtures()):
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
            
        
class Worker(object):
    """
    Worker called by each process in the process pool. Gets tests from
    incoming queue, executes each using a fresh test result, and returns the
    test result.
    """
    def __init__(self, testQueue, resultQueue, config):
        self.testQueue = testQueue
        self.resultQueue = resultQueue
        self.config = config
        resultQueue.canceljoin() # don't join on exit
        
    def __call__(self):
        for test, resultClass in iter(self._get, 'STOP'):
            result = self._makeResult(resultClass)
            test(result)
            self.resultQueue.put(result)

    def _get(self):
        return self.testQueue.get(
            block=True, timeout=self.config.multiprocess_timeout)
            
    def _makeResult(self, resultClass):
        stream = StringIO()
        return resultClass(stream, descriptions=1,
                           verbosity=self.config.verbosity,
                           config=self.config)

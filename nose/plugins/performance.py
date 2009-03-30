"""Performance test plugin.

Collects, runs and time tests that start with perf.  Any tests starting with perf will be 
run a number of times (default 10).  The number of iterations is set with the '--iters' option.

The time taken for each test is recorded and the min, avg and max times reported.
"""

import logging
import os
import time
from collections import defaultdict

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.performance')


class Performance(Plugin):
    
    iters = 'iters'
    
    def __init__(self):
        Plugin.__init__(self)
        self._startTime = defaultdict(list)
        self._stopTime = defaultdict(list)
        
    def options(self, parser, env=os.environ):
        """Setup plugin options
        """
        parser.add_option("--performance",
                          action="store_true",
                          dest=self.enableOpt,
                          default=False,
                          help="Run performance tests")
        parser.add_option("--iters",
                          dest='iters', 
                          action="store",
                          type='int',
                          default=env.get('NOSE_PERFORMANCE_ITERS', 10),
                          help="Number of times to run a performance test (default 10)"
                          "specified by ITERS [NOSE_PERFORMANCE_ITERS]")

    def configure(self, options, config):
        """Configure plugin
        """
        Plugin.configure(self, options, config)
        self.iters = options.iters

    def wantFunction(self, function):
        """This plugin wants all functions that start with 'perf'
        """
        return function.__name__.startswith('perf')
        
    def wantMethod(self, method):
        """This plugin wants all methods that start with 'perf'
        """
        return method.__name__.startswith('perf')
        
    def startTest(self, test):
        """Record the start time for each test
        """
        self._startTime[str(test)].append(time.time())
    
    def stopTest(self, test):
        """Record the stop time for each test
        """
        self._stopTime[str(test)].append(time.time())

    def loadTestsFromNames(self, names, module=None):
        """Yield tests multiple times
        """
        loader = self.loader
        def iterated():
            for name in names:      
                for test in loader.loadTestsFromName(name, module=module):
                    for iter_ in range(self.iters):
                        yield test
        return (loader.suiteClass(iterated), [])
    
    def prepareTestLoader(self, loader):
        """Get handle on test loader so we can use it in loadTestsFromNames.
        """
        self.loader = loader

    def report(self, stream):
        """Write the performance report to a stream
        """
        stream.write('-' * 70 + '\n')
        stream.write('Test Name\tMin time\tAvg time\tMax time\n')
        
        for test in sorted(self._startTime):
            timeTaken = [(stop-start) for (stop, start) in 
                            zip(self._stopTime[test], self._startTime[test])]
            avgTimeTaken = sum(timeTaken)/len(timeTaken)
            stream.write("%s\t%.3fs\t%.3fs\t%.3fs\n" % (test, 
                        min(timeTaken), avgTimeTaken, max(timeTaken)))
        
        
        # prevent other output
        return 1
    
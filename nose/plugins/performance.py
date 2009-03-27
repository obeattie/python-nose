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

log = logging.getLogger('nose.plugins.attrib')

class Performance(Plugin): 
    
    def __init__(self):
        Plugin.__init__(self)
        self._start_time = defaultdict(list)
        self._stop_time = defaultdict(list)
        self.iters = 10
        self.enableOpt = '--performance'
        
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option("--iters",
                          dest="iters", action="store",
                          default=env.get('NOSE_ITERS', 10),
                          help="Number of times to run a performance test (default 10)"
                          "specified by ITERS [NOSE_ITERS]")

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if hasattr (options, 'iters'):
            self.iters = int(options.iters)

    def wantFunction(self, function):
        return function.__name__.startswith('perf')
        
    def wantMethod(self, method):
        return method.__name__.startswith('perf')
        
    def startTest(self, test):
        self._start_time[str(test)].append(time.time())
    
    def stopTest(self, test):
        self._stop_time[str(test)].append(time.time())

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
        total_time = 0
        no_tests = 0
        stream.write('-' * 70 + '\n')
        stream.write('Test Name\tMin time\tAvg time\tMax time\n')
        
        for test in self._start_time:
            time_taken = [(stop-start) for (stop, start) in 
                            zip(self._stop_time[test], self._start_time[test])]
            avg_time_taken = sum(time_taken)/len(time_taken)
            stream.write("%s\t%.3fs\t%.3fs\t%.3fs\n" % (test, 
                        min(time_taken), avg_time_taken, max(time_taken)))
            no_tests += 1
            total_time += sum(time_taken)
        
        stream.write('.' * 70 + '\n')
        stream.write('Ran %s * %s performance tests in %.3fs\n' % (no_tests, self.iters, total_time))
        
        # prevent other output
        return 1
    
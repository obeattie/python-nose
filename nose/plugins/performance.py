"""Performance test plugin.

Collects, runs and time tests that start with perf.  Any tests starting with perf will be 
run a number of times (default 10).  The number of iterations is set with the '--iters' option.

The time taken for each test is recorded and the min, avg and max times reported.
"""

import logging
import os
import time
import csv
from collections import defaultdict

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.performance')


class Performance(Plugin):
    
    iters = None
    csv = None
    
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
        parser.add_option("--performance-csv",
                        dest='csv', 
                        action="store",
                        type='string',
                        default=env.get('NOSE_PERFORMANCE_CSV', None),
                        help="Output performance statistics to csv file "
                        "specified by CSV [NOSE_PERFORMANCE_CSV]")

    def configure(self, options, config):
        """Configure plugin
        """
        Plugin.configure(self, options, config)
        self.iters = options.iters
        self.csv = options.csv

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

    def _report_data(self):
        """Generate performance report data
        """
        for test in sorted(self._startTime):
            timeTaken = [(stop-start) for (stop, start) in 
                            zip(self._stopTime[test], self._startTime[test])]
            avgTimeTaken = sum(timeTaken)/len(timeTaken)
            yield (test, min(timeTaken), avgTimeTaken, max(timeTaken))
        

    def report(self, stream):
        """Write the performance report to a stream
        """
        stream.write('-' * 70 + '\n')
        stream.write('Test Name\tMin time\tAvg time\tMax time\n')
        
        for data in self._report_data():
            stream.write("%s\t%.3fs\t%.3fs\t%.3fs\n" % (data))

    def finalize(self, stream):
        """Write a csv report if requested
        """
        if not self.csv:
            return
            
        writer = csv.writer(file(self.csv, 'w'))
        writer.writerow('Test Name,Min Time,Avg Time,Max Time'.split(','))
        [writer.writerow(data) for data in self._report_data()]
        
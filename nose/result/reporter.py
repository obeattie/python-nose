from nose.result.text import TextTestResult
from warnings import warn

class Reporter(object):
    """Test reporter.
    
    The default reporter does not compose any output itself. Instead, it calls
    the appropriate plugin methods at each phase of test progress and final
    result, and outputs to the given stream whatever the plugin method
    returns.    
    """

    def __init__(self, stream, verbosity, config, **kw):
        super(Reporter, self).__init__(**kw)
        self.stream = stream
        self.verbosity = verbosity
        self.config = config
        self.ensureReporterPlugin()

    def ensureReporterPlugin(self):
        p = self.config.plugins.isReporter()
        if p:
            return p
        from nose.plugins.unittest_reporter import UnittestReporter
        p = UnittestReporter()
        try:
            self.config.plugins.addPlugin(p)
        except NotImplementedError:
            warn("No output plugin is available. If you want to run "
                 "without using an output plugin, use a TextTestResult "
                 "instead of the default ReporterTestResult",
                 RuntimeWarning)
        else:
            self.config.plugins.sort()
            return p

    def startTest(self, test):
        out = self.config.plugins.reportStartTest(test, self.verbosity)
        self.write(out)

    def stopTest(self, test):
        out = self.config.plugins.reportStopTest(test, self.verbosity)
        self.write(out)
    
    def reportErrorClass(self, test, err, label, cls, isfail):
        out = self.config.plugins.reportErrorClass(
            test, err, label, cls, isfail, self.verbosity)
        self.write(out)
        
    def reportError(self, test, err):
        out = self.config.plugins.reportError(test, err, self.verbosity)
        self.write(out)

    def reportFailure(self, test, err):
        out = self.config.plugins.reportFailure(test, err, self.verbosity)
        self.write(out)
        
    def reportSuccess(self, test):
        out = self.config.plugins.reportSuccess(test, self.verbosity)
        self.write(out)

    def printErrors(self, errs):
        for label, errors in errs:
            self.write(self.errorList(label, errors))

    def errorList(self, label, errors):
        return self.config.plugins.errorList(label, errors, self.verbosity)

    def report(self):
        out = self.config.plugins.report()
        self.write(out)

    def printSummary(self, start, stop, tests_run, successful, err_counts):
        out = self.config.plugins.summary(
            start, stop, tests_run, successful, err_counts, self.verbosity)
        self.write(out)
        
    def writeln(self, out):
        if out is None:
            return
        self.write(out + "\n")

    def write(self, out):
        if out is None or self.stream is None:
            return
        self.stream.write(out)
            

class ReporterTestResult(TextTestResult):
    """
    Result class that uses a `nose.result.reporter.Reporter` (by default) to
    produce output of test run progress and final test run result.
    """
    
    def __init__(self, stream, descriptions, verbosity, config=None,
                 errorClasses=None, reporter=None, **kw):
        super(ReporterTestResult, self).__init__(
            stream, descriptions, verbosity, config=config, **kw)
        if reporter is None:
            reporter = Reporter(stream, verbosity, config)
        self.reporter = reporter

    def startTest(self, test):
        self.testsRun = self.testsRun + 1
        self.reporter.startTest(test)

    def stopTest(self, test):
        self.reporter.stopTest(test)
        
    def addError(self, test, err):
        ec, ev, tb = err
        exc_info = self.excInfo(err, test)
        failed = True
        handled = False
        for cls, (storage, label, isfail) in self.errorClasses.items():
            if self.errorInClass(ec, cls):
                storage.append((test, exc_info))
                self.reporter.reportErrorClass(
                    test, err, label, cls, isfail)
                handled = True
                failed = isfail
                break
        if not handled:
            self.errors.append((test, exc_info))
            self.reporter.reportError(test, err)

    def addFailure(self, test, err):
        self.failures.append((test, self.excInfo(err, test)))
        self.reporter.reportFailure(test, err)

    def addSuccess(self, test):
        self.reporter.reportSuccess(test)

    def printErrors(self):
        errs = [('ERROR', self.errors), ('FAIL', self.failures)]
        for cls in self.errorClasses.keys():
            storage, label, isfail = self.errorClasses[cls]
            if isfail:
                errs.append((label, storage))
        self.reporter.printErrors(errs)
        self.reporter.report()
        
    def printSummary(self, start, stop):
        err_counts = [('failures', len(self.failures)),
                      ('errors', len(self.errors))]
        for cls in self.errorClasses.keys():
            storage, label, isfail = self.errorClasses[cls]
            if isfail:
                err_counts.append((label, len(storage)))
        self.reporter.printSummary(
            start, stop, self.testsRun, self.wasSuccessful(),
            err_counts)

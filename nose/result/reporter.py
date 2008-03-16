from nose.result.text import TextTestResult

class Reporter(object):
    def __init__(self, stream, verbosity, config, **kw):
        super(Reporter, self).__init__(**kw)
        self.stream = stream
        self.verbosity = verbosity
        self.config = config
        self.ensureReporterPlugin()

    def ensureReporterPlugin(self):
        for p in self.config.plugins:
            if hasattr(p, 'isReporter') and p.isReporter():
                return p
        from nose.plugins.unittest_reporter import UnittestReporter
        p = UnittestReporter()        
        self.config.plugins.addPlugin(p)
        self.config.plugins.sort()
        return p
   
    def progressErrorClass(self, test, err, label, cls, isfail):
        out = self.config.plugins.progressErrorClass(
            test, err, label, cls, isfail, self.verbosity)
        self.write(out)
        
    def progressError(self, test, err):
        out = self.config.plugins.progressError(test, err, self.verbosity)
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

    def __init__(self, stream, descriptions, verbosity, config=None,
                 errorClasses=None, reporter=None, **kw):
        super(ReporterTestResult, self).__init__(
            stream, descriptions, verbosity, config=config, **kw)
        if reporter is None:
            reporter = Reporter(stream, verbosity, config)
        self.reporter = reporter

    def addError(self, test, err):
        ec, ev, tb = err
        exc_info = self.excInfo(err, test)
        failed = True
        handled = False
        for cls, (storage, label, isfail) in self.errorClasses.items():
            if self.errorInClass(ec, cls):
                storage.append((test, exc_info))
                self.reporter.progressErrorClass(
                    test, err, label, cls, isfail)
                handled = True
                failed = isfail
                break
        if not handled:
            self.errors.append((test, exc_info))
            self.reporter.progressError(test, err)

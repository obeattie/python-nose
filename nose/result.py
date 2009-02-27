"""
Test Result
-----------

Provides a TextTestResult that extends unittest._TextTestResult to
provide support for error classes (such as the builtin skip and
deprecated classes), and hooks for plugins to take over or extend
reporting.
"""

import logging
from io import StringIO
from unittest import _TextTestResult
from nose.config import Config
from nose.util import isclass, ln as _ln # backwards compat
from nose import case

log = logging.getLogger('nose.result')


def _exception_detail(exc):
    # this is what stdlib module traceback does
    try:
        return str(exc)
    except:
        return '<unprintable %s object>' % type(exc).__name__


class TextTestResult(_TextTestResult):
    """Text test result that extends unittest's default test result
    support for a configurable set of errorClasses (eg, Skip,
    Deprecated, TODO) that extend the errors/failures/success triad.
    """    
    def __init__(self, stream=None, descriptions=0, verbosity=1, config=None,
                 errorClasses=None):
        if stream is None:
            stream = StringIO()
        if errorClasses is None:
            errorClasses = {}
        self.errorClasses = errorClasses
        if config is None:
            config = Config()       
        self.config = config
        _TextTestResult.__init__(self, stream, descriptions, verbosity)

    def afterTest(self, test):
        self.config.plugins.afterTest(self._case(test))

    def beforeTest(self, test):
        self.config.plugins.beforeTest(self._case(test))
                
    def addError(self, test, err):
        """Overrides normal addError to add support for
        errorClasses and plugin hooks.
        
        If the exception is a registered class, the error will be added
        to the list for that class, not errors.
        """
        stream = self.stream
        plugins = self.config.plugins
        _case = self._case(test)
        plugin_handled = plugins.handleError(_case, err)
        if plugin_handled:
            return
        formatted = plugins.formatError(_case, err)
        if formatted is not None:
            err = formatted
        plugins.addError(_case, err)
        ec, ev, tb = err
        try:
            exc_info = self._exc_info_to_string(err, test)
        except TypeError:
            # 2.3 compat
            exc_info = self._exc_info_to_string(err)
        ec_handled = False
        for cls, (storage, label, isfail) in list(self.errorClasses.items()):
            if isclass(ec) and issubclass(ec, cls):
                storage.append((test, exc_info))
                # Might get patched into a streamless result
                if stream is not None:
                    if self.showAll:
                        message = [label]
                        detail = _exception_detail(err[1])
                        if detail:
                            message.append(detail)
                        stream.writeln(": ".join(message))
                    elif self.dots:
                        stream.write(label[:1])
                ec_handled = True
                break
        if not ec_handled:
            self.errors.append((test, exc_info))
            if stream is not None:
                if self.showAll:
                    self.stream.writeln('ERROR')
                elif self.dots:
                    stream.write('E')
        if not self.wasSuccessful() and self.config.stopOnError:
            self.shouldStop = True

    def addFailure(self, test, err):
        plugins = self.config.plugins
        _case = self._case(test)
        plugin_handled = plugins.handleFailure(_case, err)
        if plugin_handled:
            return
        formatted = plugins.formatFailure(_case, err)
        if formatted is not None:
            err = formatted
        plugins.addFailure(_case, err)
        super(TextTestResult, self).addFailure(test, err)
        if self.config.stopOnError:
            self.shouldStop = True
    
    def addSuccess(self, test):
        self.config.plugins.addSuccess(self._case(test))
        super(TextTestResult, self).addSuccess(test)

    def startTest(self, test):
        self.config.plugins.startTest(self._case(test))
        super(TextTestResult, self).startTest(test)
    
    def stopTest(self, test):
        self.config.plugins.stopTest(self._case(test))
        super(TextTestResult, self).stopTest(test)

    def printErrors(self):
        """Overrides to print all errorClasses errors as well.
        """
        _TextTestResult.printErrors(self)
        for cls in list(self.errorClasses.keys()):
            storage, label, isfail = self.errorClasses[cls]
            if isfail:
                self.printErrorList(label, storage)
        # Might get patched into a result with no config
        if hasattr(self, 'config'):
            self.config.plugins.report(self.stream)

    def printSummary(self, start, stop):
        """Called by the test runner to print the final summary of test
        run results.
        """
        write = self.stream.write
        writeln = self.stream.writeln
        taken = float(stop - start)
        run = self.testsRun
        plural = run != 1 and "s" or ""
        
        writeln(self.separator2)
        writeln("Ran %s test%s in %.3fs" % (run, plural, taken))
        writeln()

        summary = {}
        eckeys = list(self.errorClasses.keys())
        eckeys.sort(key=lambda c: c.__name__)
        for cls in eckeys:
            storage, label, isfail = self.errorClasses[cls]
            count = len(storage)
            if not count:
                continue
            summary[label] = count
        if len(self.failures):
            summary['failures'] = len(self.failures)
        if len(self.errors):
            summary['errors'] = len(self.errors)

        if not self.wasSuccessful():
            write("FAILED")
        else:
            write("OK")
        items = list(summary.items())
        if items:
            items.sort()
            write(" (")
            write(", ".join(["%s=%s" % (label, count) for
                             label, count in items]))
            writeln(")")
        else:
            writeln()

    def getDescription(self, test):
        _case = self._case(test)
        if self.descriptions:
            return _case.shortDescription() or str(_case)
        else:
            return str(_case)

    def wasSuccessful(self):
        """Overrides to check that there are no errors in errorClasses
        lists that are marked as errors that should cause a run to
        fail.
        """
        if self.errors or self.failures:
            return False
        for cls in self.errorClasses.keys():
            storage, label, isfail = self.errorClasses[cls]
            if not isfail:
                continue
            if storage:
                return False
        return True
    
    def _case(self, test):
        """
        Return a nose.case.Test wrapper for the given test case.
        """
        if isinstance(test, case.Test):
            return test
        _case = None
        try:
            _case = test._nose_case_()
        except AttributeError:
            pass
        if _case is None:
            _case = case.Test(test)
        return _case

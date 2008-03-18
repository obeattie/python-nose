from nose.plugins.base import Plugin
from nose.util import odict


class UnittestReporter(Plugin):
    """
    Reporter plugin that outputs to the given stream in standard unittest
    format.

    This is the default output plugin. This plugin will be **automatically**
    activated, even when using a static list of plugins that does not include
    it, if no other reporter plugin is in use.
    """
    enabled = True
    score = 10000

    separator1 = '=' * 70
    separator2 = '-' * 70
    
    # FIXME
    def options(self, parser, env=None):
        pass

    def configure(self, options, conf):
        pass

    def isReporter(self):
        return self
    
    def outcome(self, label, err=None, verbosity=None):
        out = label
        if verbosity < 2:
            out = out[:1]
        elif err:            
            out = "%s: %s" % (out, err)
        return out
    
    def reportError(self, test, err, verbosity, out=None):
        return self.outcome('ERROR', verbosity=verbosity)

    def reportErrorClass(self, test, err, label, cls, isfail, verbosity,
                           out=None):
        return self.outcome(label, err=str(err[1]), verbosity=verbosity)

    def reportFailure(self, test, err, verbosity, out=None):
        return self.outcome('FAIL', verbosity=verbosity)
    
    def reportStopTest(self, test, verbosity, out=None):
        if verbosity >= 2:
            return "\n"

    def reportSuccess(self, test, verbosity, out=None):
        if verbosity >= 2:
            return "ok"
        else:
            return "."

    def reportStartTest(self, test, verbosity, out=None):
        if verbosity >= 2:
            return (test.shortDescription() or str(test)) + ' ... '
        
    def errorList(self, label, errors, verbosity=None, out=None):
        if not errors:
            return
        out = []
        for test, err in errors:
            out.append(self.separator1)
            out.append("%s: %s" % (label, test.shortDescription() or
                                   str(test)))
            out.append(self.separator2)
            out.append(str(err))
        return "\n" + "\n".join(out)

    def summary(self, start, stop, tests_run, successful, err_counts, out=None):
        taken = float(stop - start)
        plural = tests_run !=1 and "s" or ""
        out = [self.separator2,
               "Ran %s test%s in %.3fs" % (tests_run, plural, taken)]
        if not successful:
            errs = []
            for label, count in err_counts:
                if count:
                    errs.append("%s=%s" % (label, count))
            out.append(''.join(["\nFAILED (",
                                ", ".join(errs),
                                ")"]))
        else:
            out.append("\nOK")
        return "\n" + "\n".join(out) + "\n"
            
        
            
                         
                         

from nose.plugins.base import Plugin

class UnittestReporter(Plugin):
    enabled = True
    score = 10000
    
    # FIXME
    def options(self, parser, env=None):
        pass

    def configure(self, options, conf):
        pass

    def progress(self, label, err=None, verbosity=None):
        out = label
        if verbosity < 2:
            out = out[:1]
        elif err:            
            out = "%s: %s\n" % (out, err)
        else:
            out += "\n"
        return out
    
    def progressError(self, test, err, verbosity, out=None):
        return self.progress('ERROR', verbosity=verbosity)

    def progressErrorClass(self, test, err, label, cls, isfail, verbosity,
                           out=None):
        return self.progress(label, err=str(err[1]), verbosity=verbosity)

    def isReporter(self):
        return True

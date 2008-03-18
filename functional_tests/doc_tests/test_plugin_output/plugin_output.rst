Controlling or Modifying Test Run Output with a Plugin
------------------------------------------------------

Blah blah.

    >>> import os
    >>> import sys
    >>> support = os.path.join(os.path.dirname(__file__), 'support')
    >>> sys.path.insert(0, support)
  
.. Note ::

   The run() function in `nose.plugins.plugintest`_ reformats test result
   output to remove timings, which will vary from run to run, and
   redirects the output to stdout.

    >>> from nose.plugins.plugintest import run

..

    >>> import todo
    >>> from nose.plugins import skip

The default output.
    
    >>> argv = [__file__, '-v', support]
    >>> run(argv=argv, plugins=[todo.TodoPlugin(), skip.Skip()])
    tests.test_pass ... ok
    tests.test_fail ... FAIL
    tests.test_error ... ERROR
    tests.test_skip ... SKIP: skip me
    tests.test_todo ... TODO: Do something later
    <BLANKLINE>    
    ======================================================================
    ERROR: tests.test_error
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    ZeroDivisionError: integer division or modulo by zero
    <BLANKLINE>
    ======================================================================
    FAIL: tests.test_fail
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    AssertionError: I failed
    <BLANKLINE>
    ======================================================================
    TODO: tests.test_todo
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    Todo: Do something later
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 5 tests in ...s
    <BLANKLINE>
    FAILED (failures=1, errors=1, TODO=1)

An output decorator plugin.

    >>> import re
    >>> from nose.plugins import Plugin
    >>> class TagOutput(Plugin):
    ...     enabled = True
    ...     score = 100
    ...     tb_pat = re.compile(r'(Traceback(?:.|\n)*?)(\n(?:\n|$))')
    ...     def options(self, parser, env=None):
    ...         pass
    ...     def configure(self, config, options):
    ...         pass
    ...     def reportSuccess(self, test, verbosity, out=None):
    ...         return "<g>%s</g>" % out
    ...     def reportFailure(self, test, err, verbosity, out=None):
    ...         return "<y>%s</y>" % out
    ...     def reportError(self, test, err, verbosity, out=None):
    ...         return "<r>%s</r>" % out
    ...     def reportErrorClass(self, test, err, label, err_cls, isfail,
    ...                            verbosity, out=None):
    ...         if isfail:
    ...             return "<o>%s</o>" % out
    ...         else:
    ...             return "<b>%s</b>" % out
    ...     def errorList(self, label, errors, verbosity, out):
    ...         return self.tagTracebacks(out)
    ...     def tagTracebacks(self, out):
    ...         return self.tb_pat.sub(r'<tb>\n\1\n</tb>\2', out)

Output with the output decorator plugin enabled.
    
    >>> argv = [__file__, '-vv', support]
    >>> run(argv=argv, plugins=[todo.TodoPlugin(), skip.Skip(), TagOutput()]) # doctest: +REPORT_NDIFF
    tests.test_pass ... <g>ok</g>
    tests.test_fail ... <y>FAIL</y>
    tests.test_error ... <r>ERROR</r>
    tests.test_skip ... <b>SKIP: skip me</b>
    tests.test_todo ... <o>TODO: Do something later</o>
    <BLANKLINE>
    ======================================================================
    ERROR: tests.test_error
    ----------------------------------------------------------------------
    <tb>
    Traceback (most recent call last):
    ...
    ZeroDivisionError: integer division or modulo by zero
    </tb>
    <BLANKLINE>
    ======================================================================
    FAIL: tests.test_fail
    ----------------------------------------------------------------------
    <tb>
    Traceback (most recent call last):
    ...
    AssertionError: I failed
    </tb>
    <BLANKLINE>
    ======================================================================
    TODO: tests.test_todo
    ----------------------------------------------------------------------
    <tb>
    Traceback (most recent call last):
    ...
    Todo: Do something later
    </tb>
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 5 tests in ...s
    <BLANKLINE>
    FAILED (failures=1, errors=1, TODO=1)

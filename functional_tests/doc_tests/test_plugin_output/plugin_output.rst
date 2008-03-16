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

    >>> from nose.plugins import Plugin
    >>> class TagOutput(Plugin):
    ...     enabled = True
    ...     def progressSuccess(self, test, out, verbosity):
    ...         return "<g>%s</g>" % out
    ...     def progressFailure(self, test, err, out, verbosity):
    ...         return "<y>%s</y>" % out
    ...     def progressError(self, test, err, out, verbosity):
    ...         return "<r>%s</r>" %out
    ...     def progressErrorClass(self, test, err, err_cls, out, verbosity):
    ...         if err_cls.isfailure:
    ...             return "<o>%s</o>" % out
    ...         else:
    ...             return "<b>%s</b>" % out
    ...     def reportFailure(self, test, err, out, verbosity):
    ...         return self.tagTraceback(out)
    ...     def tagTraceback(self, out):
    ...         return "<tb>\n%s\n</tb>" % out

Output with the output decorator plugin enabled.
    
    >>> argv = [__file__, '-v', support]
    >>> run(argv=argv, plugins=[todo.TodoPlugin(), skip.Skip(), TagOutput()])
    tests.test_pass ... <g>ok</g>
    tests.test_fail ... <y>FAIL</y>
    tests.test_error ... <r>ERROR</r>
    tests.test_skip ... <p>SKIP: skip me</p>
    tests.test_todo ... <o>TODO: Do something later</o>
    <BLANKLINE>
    <tb>
    ======================================================================
    ERROR: tests.test_error
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    ZeroDivisionError: integer division or modulo by zero
    </tb>
    <BLANKLINE>
    <tb>
    ======================================================================
    FAIL: tests.test_fail
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    AssertionError: I failed
    </tb>
    <BLANKLINE>
    <tb>
    ======================================================================
    TODO: tests.test_todo
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    Todo: Do something later
    </tb>
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 5 tests in ...s
    <BLANKLINE>
    FAILED (failures=1, errors=1, TODO=1)

Parallel Testing with nose
--------------------------

.. Note ::

   The multiprocess plugin requires the processing module.

..

Using the `nose.plugin.multiprocess` plugin, you can parallelize a
test run across a configurable number of worker processes. This can
speed up CPU-bound test runs (as long as the number of work
processeses is around the number of processors or cores available),
but is mainly useful for IO-bound tests which can benefit from massive
parallelization, since most of the tests spend most of their time
waiting for data to arrive from someplace else.

How tests are distributed
=========================

The ideal case would be to dispatch each test to a worker process
separately. This ideal is not attainable in all cases, however, because many
test suites depend on context (class, module or package) fixtures.

The plugin can't know (unless you tell it -- see below!) whether a given
context fixture is re-entrant (that is, can be called many times
concurrently), or may be shared among tests running in different
processes. Therefore, if a context has fixtures, the default behavior is to
dispatch the entire suite to a worker as a unit.

Controlling distribution
^^^^^^^^^^^^^^^^^^^^^^^^

There are two context-level variables that you can use to control this default
behavior.

If a context's fixtures are re-entrant, set `_multiprocess_can_split_ = True`
in the context, and the plugin will dispatch tests in suites bound to that
context as if the context had no fixtures. This means that the fixtures will
execute multiple times, typically once per test, and concurrently.

If a context's fixtures may be shared by tests running in different processes
-- for instance a package-level fixture that starts an external http server or
initializes a shared database -- then set `_multiprocess_shared_ = True` in
the context. Fixtures for contexts so marked will execute in the primary nose
process, and tests in those contexts will be individually dispatched to run in
parallel.

.. Note ::

   The run() function in `nose.plugins.plugintest`_ reformats test result
   output to remove timings, which will vary from run to run, and
   redirects the output to stdout.

    >>> from nose.plugins.plugintest import run_buffered as run

..

    >>> import os
    >>> import sys
    >>> support = os.path.join(os.path.dirname(__file__), 'support')

For example, consider three versions of the same test suite. One
is marked `_multiprocess_shared_`, another `_multiprocess_can_split_`,
and the third is unmarked. They all define the same fixtures:

    def setup():
        print "setup called"
        called.append('setup')
        
    def teardown():
        print "teardown called"
        called.append('teardown')
    
And each has two tests that just test that `setup()` has been called
once and only once.

When run without the multiprocess plugin, fixtures for the shared,
can-split and not-shared test suites execute at the same times, and
all tests pass.

    >>> argv = [__file__, '-v', os.path.join(support, 'test_shared.py')]
    >>> run(argv=argv) #doctest: +REPORT_NDIFF
    setup called
    test_shared.TestMe.test_one ... ok
    test_shared.test_a ... ok
    test_shared.test_b ... ok
    teardown called
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK

    >>> argv = [__file__, '-v', os.path.join(support, 'test_not_shared.py')]
    >>> run(argv=argv) #doctest: +REPORT_NDIFF
    setup called
    test_not_shared.TestMe.test_one ... ok
    test_not_shared.test_a ... ok
    test_not_shared.test_b ... ok
    teardown called
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK

    >>> argv = [__file__, '-v', os.path.join(support, 'test_can_split.py')]
    >>> run(argv=argv) #doctest: +REPORT_NDIFF
    setup called
    test_can_split.TestMe.test_one ... ok
    test_can_split.test_a ... ok
    test_can_split.test_b ... ok
    teardown called
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK

However, when run with the `--processes=2` switch, each test module
behaves differently.

    >>> from nose.plugins.multiprocess import MultiProcess

The module marked `_multiprocess_shared_` executes correctly.

# FIXME the following examples must be made conditional and only execute
# if processing is available.

    # First we have to reset all of the test modules
    >>> sys.modules['test_shared'].called[:] = []
    >>> sys.modules['test_not_shared'].called[:] = []
    >>> sys.modules['test_can_split'].called[:] = []

    >>> argv = [__file__, '-v', '--processes=2',
    ...         os.path.join(support, 'test_shared.py')]
    >>> run(argv=argv, plugins=[MultiProcess()]) #doctest: +REPORT_NDIFF
    setup called
    test_shared.TestMe.test_one ... ok
    test_shared.test_a ... ok
    test_shared.test_b ... ok
    teardown called
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK

As does the one not marked -- however in this case, `--processes=2`
will do *nothing at all*: since the tests are in a module with
unmarked fixtures, the entire test module will be dispatched to a
single runner process.

However, the module marked `_multiprocess_can_split_` will fail, since
the fixtures *are not reentrant*. A module such as this *must not* be
marked `_multiprocess_can_split_`, or tests will fail in one or more
runner processes as fixtures are re-executed.

    >>> argv = [__file__, '-v', '--processes=2',
    ...         os.path.join(support, 'test_can_split.py')]
    >>> run(argv=argv, plugins=[MultiProcess()]) #doctest: +ELLIPSIS
    test_can_split....
    ...
    FAILED (failures=...)

Doctest Fixtures
----------------

Fixtures for a doctest file may define any or all of the following methods:

setup/setup_module/setupModule/setUpModule (module)
===================================================

teardown/teardown_module/teardownModule/tearDownModule (module)
===============================================================

setup_test(test)
================

    >>> 1
    1

This is another example.

    >>> count
    1

And this is yet another example.

    >>> count
    1

teardown_test(test)
===================


Bottom line: setup_test, teardown_test have access to the *doctest test*,
while setup, setup_module, etc have access to the *fixture* module.

globs(globs)
============

    >>> something
    'Something?'




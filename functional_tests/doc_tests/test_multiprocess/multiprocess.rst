Parallel Testing with nose
--------------------------

Using the `nose.plugin.multiprocess` plugin, you can parallelize a
test run across a configurable number of worker processes.

    >>> import os
    >>> support = os.path.join(os.path.dirname(__file__), 'support')

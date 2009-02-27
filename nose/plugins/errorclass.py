"""
ErrorClass Plugins
------------------

ErrorClass plugins provide an easy way to add support for custom
handling of particular classes of exceptions.

An ErrorClass plugin defines one or more ErrorClasses and how each is
handled and reported on. Each error class is stored in a different
attribute on the result, and reported separately. Each error class must
indicate the exceptions that fall under that class, the label to use
for reporting, and whether exceptions of the class should be
considered as failures for the whole test run.

ErrorClasses use a declarative syntax. Assign an ErrorClass to the
attribute you wish to add to the result object, defining the
exceptions, label and isfailure attributes. For example, to declare an
ErrorClassPlugin that defines TodoErrors (and subclasses of TodoError)
as an error class with the label 'TODO' that is considered a failure,
do this:

    >>> class Todo(Exception):
    ...     pass
    >>> class TodoError(ErrorClassPlugin):
    ...     todo = ErrorClass(Todo, label='TODO', isfailure=True)

The MetaErrorClass metaclass translates the ErrorClass declarations
into the tuples used by the error handling and reporting functions in
the result. This is an internal format and subject to change; you
should always use the declarative syntax for attaching ErrorClasses to
an ErrorClass plugin.
    
    >>> TodoError.errorClasses # doctest: +ELLIPSIS
    ((<class ...Todo...>, ('todo', 'TODO', True)),)

Let's see the plugin in action. First some boilerplate.

    >>> import sys
    >>> import unittest
    >>> import nose.result
    >>> buf = unittest._WritelnDecorator(sys.stdout)

Now define a test case that raises a Todo.

    >>> class TestTodo(unittest.TestCase):
    ...     def runTest(self):
    ...         raise Todo("I need to test something")
    >>> case = TestTodo()

Prepare the result using our plugin. Normally this happens during the
course of test execution within nose -- you won't be doing this
yourself. For the purposes of this testing document, I'm stepping
through the internal process of nose so you can see what happens at
each step.

    >>> plugin = TodoError()
    >>> result = nose.result.TextTestResult(stream=buf,
    ...                                     descriptions=0, verbosity=2)
    >>> plugin.prepareTestResult(result)

Now run the test. TODO is printed.

    >>> case(result) # doctest: +ELLIPSIS
    runTest (....TestTodo) ... TODO: I need to test something

Errors and failures are empty, but todo has our test:

    >>> result.errors
    []
    >>> result.failures
    []
    >>> result.todo # doctest: +ELLIPSIS
    [(<....TestTodo testMethod=runTest>, '...Todo: I need to test something\\n')]
    >>> result.printErrors() # doctest: +ELLIPSIS
    <BLANKLINE>
    ======================================================================
    TODO: runTest (....TestTodo)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    nose.plugins.errorclass.Todo: I need to test something
    <BLANKLINE>

Since we defined a Todo as a failure, the run was not successful.

    >>> result.wasSuccessful()
    False
"""

from types import MethodType as instancemethod
from nose.plugins.base import Plugin
from nose.result import TextTestResult
from nose.util import isclass
import logging

log = logging.getLogger(__name__)


class MetaErrorClass(type):
    """Metaclass for ErrorClassPlugins that allows error classes to be
    set up in a declarative manner.
    """
    def __init__(self, name, bases, attr):
        errorClasses = []
        for name, detail in list(attr.items()):
            if isinstance(detail, ErrorClass):
                attr.pop(name)
                for cls in detail:
                    errorClasses.append(
                        (cls, (name, detail.label, detail.isfailure)))
        super(MetaErrorClass, self).__init__(name, bases, attr)
        self.errorClasses = tuple(errorClasses)


class ErrorClass(object):
    def __init__(self, *errorClasses, **kw):
        self.errorClasses = errorClasses
        try:
            for key in ('label', 'isfailure'):
                setattr(self, key, kw.pop(key))
        except KeyError:
            raise TypeError("%r is a required named argument for ErrorClass"
                            % key)

    def __iter__(self):
        return iter(self.errorClasses)

    
class _ErrorClassPlugin(Plugin):
    score = 1000
    errorClasses = ()

    def addError(self, test, err):
        err_cls, a, b = err
        if not isclass(err_cls):
            return
        classes = [e[0] for e in self.errorClasses]
        if [c for c in classes if issubclass(err_cls, c)]:
            return True

    def prepareTestResult(self, result):
        log.debug("Prepare test result %s for error classes %s",
                  result, self.errorClasses)
        for cls, (storage_attr, label, isfail) in self.errorClasses:
            if cls not in result.errorClasses:
                storage = getattr(result, storage_attr, [])
                setattr(result, storage_attr, storage)
                result.errorClasses[cls] = (storage, label, isfail)

# metaclassing compatible with 2 and 3
ErrorClassPlugin = MetaErrorClass('ErrorClassPlugin', (_ErrorClassPlugin, ), {})
                
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()

import unittest
from nose.loader import TestLoader
from nose.plugins import multiprocess
from nose.suite import ContextSuite

class T_fixt:
    def setupClass(cls):
        pass
    setupClass = classmethod(setupClass)

    def test_a(self):
        pass

    def test_b(self):
        pass
    
class T:

    def test_a(self):
        pass

    def test_b(self):
        pass


class TestMultiProcessTestRunner(unittest.TestCase):

    def test_next_batch(self):
        r = multiprocess.MultiProcessTestRunner()
        l = TestLoader()
        tests = list(r.next_batch(ContextSuite(
                    tests=[l.makeTest(T_fixt), l.makeTest(T)])))
        print tests
        self.assertEqual(len(tests), 3)


if __name__ == '__main__':
    unittest.main()

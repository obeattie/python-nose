import unittest

def perf_function():
    """function that should be run"""
    pass
    

class PerformanceTest(unittest.TestCase):
    
    def perf_method(self):
        """method that should be run"""
        pass
        
def test_normal():
    """normal test shouldn't be run"""
    pass
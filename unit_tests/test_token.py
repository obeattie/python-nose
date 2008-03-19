import unittest
from nose.result.token import Token, TokenStream


class TestToken(unittest.TestCase):

    def test_init(self):
        t = Token('success', '.')
        self.assertEqual(t.name , 'success')
        self.assertEqual(t.value, '.')
        self.assertEqual(str(t), '.')
        self.assertEqual(repr(t), '.')

    def test_add_creates_stream(self):
        t = Token('success', '.')
        t = t + t
        self.assertEqual(str(t), '..')
        self.assertEqual(len(t), 2)
        for name, value in t:
            self.assertEqual(name, 'success')
            self.assertEqual(value, '.')

    def test_token_iadd(self):
        t = Token('success', '.')
        t += Token('failure', 'F')
        self.assertEqual(str(t), '.F')
        expect = [('success', '.'), ('failure', 'F')]
        result = [(name, value) for name, value in t]
        self.assertEqual(result, expect)

    def test_stream_add(self):
        t = Token('success', '.') + Token('error', 'E')
        t = t + Token('failure', 'F')
        self.assertEqual(str(t), '.EF')

    def test_stream_iadd(self):
        t = Token('success', '.') + Token('error', 'E')
        t += Token('failure', 'F')
        self.assertEqual(str(t), '.EF')
        
if __name__ == '__main__':
    unittest.main()

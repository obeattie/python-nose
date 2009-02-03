"""
Copyright (c) 2008 Paul Davis <paul.joseph.davis@gmail.com>

This file is part of nosexml, which is released under the MIT license.
"""

import unittest

from nosexml import XMLFormatter

from cStringIO import StringIO


class TestXMLFormatter(unittest.TestCase):
    def test_all(self):
        fmt = XMLFormatter( 'foo' )
        self.assertEqual( fmt.stream, 'foo' )
        self.assertRaises( NotImplementedError, fmt.setStream, None )
        self.assertRaises( NotImplementedError, fmt.startDocument )
        self.assertRaises( NotImplementedError, fmt.endDocument )
        self.assertRaises( NotImplementedError, fmt.startElement, None, attrs={} )
        self.assertRaises( NotImplementedError, fmt.endElement, None )
        self.assertRaises( NotImplementedError, fmt.characters, None )

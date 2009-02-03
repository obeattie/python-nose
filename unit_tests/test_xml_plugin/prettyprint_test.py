"""
Copyright (c) 2008 Paul Davis <paul.joseph.davis@gmail.com>

This file is part of nosexml, which is released under the MIT license.
"""

import sys
import unittest

from nosexml import PrettyPrintFormatter

from cStringIO import StringIO


class TestXMLFormatter(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.fmt  = PrettyPrintFormatter( self.buffer )
    
    def test_constructor(self):
        fmt = PrettyPrintFormatter( sys.stdout )
        self.assertEqual( fmt.indent, '    ' )
        self.assertEqual( fmt.depth, 0 )
        self.assertEqual( fmt.stream, sys.stdout )
        
    def test_set_stream(self):
        #Setup provides a StringIO for testing
        self.assertEqual( self.fmt.stream, self.buffer )
        strm = StringIO()
        self.fmt.setStream( strm )
        self.assertEqual( self.fmt.stream, strm )
    
    def test_start_document(self):
        self.fmt.startDocument()
        self.assertEqual( self.fmt.stream.getvalue(),'<?xml version="1.0" encoding="UTF-8"?>\n' \
                                                        '<nosetests>\n' )

    def test_end_document(self):
        self.fmt.endDocument()
        self.assertEqual( self.fmt.stream.getvalue(), '</nosetests>\n' )

    def test_start_end_element(self):
        self.fmt.startElement( 'test' )
        self.assertEqual( self.fmt.stream.getvalue(), '' )
        self.fmt.endElement( 'test' )
        self.assertEqual( self.fmt.stream.getvalue(), '    <test />\n' )

    def test_start_element_w_attrs(self):
        self.fmt.startElement( 'test', { 'foo': '2' } )
        self.assertEqual( self.fmt.stream.getvalue(), '' )
        self.fmt.endElement( 'test' )
        self.assertEqual( self.fmt.stream.getvalue(), '    <test foo="2" />\n' )

    def test_end_element(self):
        self.fmt.endElement( 'bar' )
        self.assertEqual( self.fmt.stream.getvalue(), '</bar>\n' )

    def test_characters(self):
        self.fmt.characters( 'test' )
        self.assertEqual( self.fmt.stream.getvalue(), '    test\n' )

    def test_characters_w_lf(self):
        self.fmt.characters( 'test\n' )
        self.assertEqual( self.fmt.stream.getvalue(), '    test\n' )

    def test_attrs(self):
        ret = self.fmt._attrs( args={ 'foo': 'bar', 'baz': 5 } )
        self.assertEqual( ret, ' foo="bar" baz="5"' )
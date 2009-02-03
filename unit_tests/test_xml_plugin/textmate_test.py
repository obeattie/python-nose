"""
Copyright (c) 2008 Paul Davis <paul.joseph.davis@gmail.com>

This file is part of nosexml, which is released under the MIT license.
"""

import sys
import unittest

from cStringIO import StringIO

from nosexml import TextMateFormatter

#This is obviously poor testing, but I'm not that concerned about
#thoroughly testing formatters other than to make sure they don't throw.
class TestTextMateFormatter(unittest.TestCase):
    def test_basic(self):
        buf = StringIO()
        tm = TextMateFormatter( buf )
        tm.setStream( buf ) #I'm a coverage whore
        tm.startDocument()
        tm.startElement( 'test', attrs={ 'id': 'class_name.function_name', 'status': 'success' } )
        tm.endElement( 'test' )
        tm.startElement( 'test', attrs={ 'id': 'class_name.other_function_name', 'status': 'failure', 'text': 'bar' } )
        tm.startElement( 'frame', attrs={ 'file': 'foo.py', 'line': '20', 'function': 'bar', 'text': 'baz' } )
        tm.characters( "This is some stuff" )
        tm.endElement( 'frame' )
        tm.startElement( 'frame', attrs={ 'file': 'bar.py', 'line': '20', 'function': 'bar', 'text': 'foo' } )
        tm.characters( "Next frame's data" )
        tm.endElement( 'frame' )
        tm.startElement( 'cause', attrs={ 'type': 'ValueError' } )
        tm.characters( 'Cause here' )
        tm.endElement( 'cause' )
        tm.endElement('test')
        tm.startElement( 'test', attrs={ 'id': 'class_name.yet_another_func_name', 'status': 'success' } )
        tm.startElement( 'stdout', attrs={} )
        tm.characters( 'Hi mom!' )
        tm.endElement( 'stdout' )
        tm.startElement( 'stderr', attrs={} )
        tm.characters( 'Hi again!' )
        tm.endElement( 'stderr' )
        tm.endElement( 'test' )
        self.assertRaises( AttributeError, tm.startElement, 'foo', attrs={} )
        tm.endDocument()

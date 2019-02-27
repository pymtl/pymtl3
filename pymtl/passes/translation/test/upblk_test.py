#=========================================================================
# upblk_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL models with complicated expressions insdie
# one upblk.
# 
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from pymtl.passes.test                import run_translation_test
from pymtl.passes.rast.test.rast_test import *

def local_do_test( m ):
  run_translation_test( m, m._test_vector )

# Reuse tests from passes/rast/test/rast_test.py
[ pytest.mark.skipif( True, reason='Array index out of range' )(x) for x in [
  test_for_basic
] ]

#-------------------------------------------------------------------------
# test_struct_inport
#-------------------------------------------------------------------------

def test_struct_inport( do_test ):
  class struct_fields( object ):
    def __init__( s, n_foo, n_bar ):
      s.foo = mk_bits( n_foo )
      s.bar = mk_bits( n_bar )

    def __call__( s, foo = 0, bar = 0 ):
      msg = struct_fields( s.foo.nbits, s.bar.nbits )
      msg.foo = msg.foo( foo )
      msg.bar = msg.bar( bar )
      return msg

  class struct_inport( RTLComponent ):
    def construct( s, n_foo, n_bar ):
      s.in_ = InVPort( struct_fields( n_foo, n_bar ) )
      s.out = OutVPort( mk_bits( n_foo + n_bar ) )

      @s.update
      def struct_inport():
        s.out[ 0:n_foo ] = s.in_.foo
        s.out[ n_foo:n_foo+n_bar ] = s.in_.bar

  a = struct_inport( 4, 8 )

  tmplt = struct_fields( 4, 8 )

  a._test_vector = [
                    'in_             *out',
    [            Bits12,          Bits12 ],

    [   Bits12( 0xF00 ), Bits12( 0x00F ) ],
    [   Bits12( 0x0F0 ), Bits12( 0xF00 ) ],
    [   Bits12( 0x00F ), Bits12( 0x0F0 ) ],
    [   Bits12( 0xBCA ), Bits12( 0xCAB ) ],
    [   Bits12( 0xADF ), Bits12( 0xDFA ) ],
    [   Bits12( 0x001 ), Bits12( 0x010 ) ],
    [   Bits12( 0x702 ), Bits12( 0x027 ) ],
    [   Bits12( 0xF05 ), Bits12( 0x05F ) ],
    [   Bits12( 0x0FC ), Bits12( 0xFC0 ) ],
  ]

  do_test( a )

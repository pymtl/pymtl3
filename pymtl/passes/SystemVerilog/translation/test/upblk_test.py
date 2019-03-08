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

from pymtl.passes.rast.test.rast_test import *
from pymtl.passes.SystemVerilog import TranslationPass, SimpleImportPass
from pymtl.passes.utility       import do_test, run_translation_test

def local_do_test( m ):

  def run_sv_translation_test( m, test_vector ):
    run_translation_test( m, test_vector, TranslationPass, SimpleImportPass )

  run_sv_translation_test( m, m._test_vector )

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

      s._pack_order = [ 'foo', 'bar' ]

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

#-------------------------------------------------------------------------
# test_composite_port
#-------------------------------------------------------------------------

def test_composite_port( do_test ):
  class val_bundle( object ):
    def __init__( s ):
      s.val0 = Bits1
      s.val1 = Bits1
      
      s._pack_order = [ 'val0', 'val1' ]

    def __call__( s, val0 = 0, val1 = 0 ):
      bundle = val_bundle()
      bundle.val0 = bundle.val0( 0 )
      bundle.val1 = bundle.val1( 0 )
      return bundle

  class composite_port( RTLComponent ):
    def construct( s, num_port ):
      s.in_ = [ InVPort( val_bundle() ) for _ in xrange( num_port ) ]
      s.out = [ OutVPort( Bits32 ) for _ in xrange( num_port ) ]

      @s.update
      def composite_port_out():
        for i in xrange( num_port ):
          if s.in_[ i ].val0 and s.in_[ i ].val1:
            s.out[ i ] = Bits32(0xac)
          else:
            s.out[ i ] = Bits32(0xff)

  m = composite_port( 2 )
  m._test_vector = [
    '    in_[0]    in_[1]       *out[0]      *out[1] ',
    [    Bits2,    Bits2,       Bits32,       Bits32 ],

    [ Bits2(3), Bits2(3), Bits32(0xac), Bits32(0xac) ],
    [ Bits2(1), Bits2(1), Bits32(0xff), Bits32(0xff) ],
    [ Bits2(3), Bits2(1), Bits32(0xac), Bits32(0xff) ],
    [ Bits2(1), Bits2(3), Bits32(0xff), Bits32(0xac) ],
  ]
  do_test( m )

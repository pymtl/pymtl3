#=========================================================================
# hierarchy_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL hierarchical designs.
# 
# Author : Shunning Jiang, Peitian Pan
# Date   : Feb 21, 2019

from pymtl                import *
from pymtl.passes.utility import expected_failure
from pymtl.dsl.errors     import SignalTypeError

def test_deep_connection():
  class Deep( RTLComponent ):
    def construct( s ):
      s.out = OutVPort( Bits1 )
      s.deep = Wire( Bits1 )

      @s.update
      def out_blk():
        s.out = s.deep

  class Bar( RTLComponent ):
    def construct( s ):
      s.deep = Deep()

  class Foo( RTLComponent ):
    def construct( s ):
      s.bar = Bar()
      s.foo = InVPort( Bits1 )
      s.connect( s.foo, s.bar.deep.deep )

  with expected_failure( SignalTypeError ):
    foo = Foo()
    foo.elaborate() # Should fail because the connection is too deep

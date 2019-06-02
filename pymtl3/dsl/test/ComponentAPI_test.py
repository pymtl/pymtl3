"""
========================================================================
ComponentAPI_test.py
========================================================================

Author : Shunning Jiang
Date   : June 2, 2019
"""
from pymtl3.datatypes import *
from pymtl3.dsl import InPort, OutPort, Component
from pymtl3.dsl.errors import InvalidAPICallError

def test_api_not_elaborated():

  class X( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      @s.update
      def up_x():
        s.out = s.in_ + 1

  class Y( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.x = X()( in_ = s.in_, out = s.out )

  a = Y()
  a.elaborate()
  try:
    a.x.get_all_update_blocks()
  except InvalidAPICallError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidAPICallError.")

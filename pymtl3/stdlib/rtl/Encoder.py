"""
========================================================================
Encoder.py
========================================================================
A priority encoder for arbitration

Author : Yanghui Ou, Cheng Tan
  Date : Mar 1, 2019
"""
from pymtl3 import *


class Encoder( Component ):
  def construct( s, in_nbits, out_nbits ):

    # Interface

    InType  = mk_bits(in_nbits)
    OutType = mk_bits(out_nbits)

    s.in_ =  InPort( InType )
    s.out = OutPort( OutType )

    # Constants

    s.in_nbits  = in_nbits
    s.out_nbits = out_nbits

    # Logic

    @s.update
    def encode():
      s.out = OutType( 0 )
      for i in range( s.in_nbits ):
        if s.in_[i]:
          s.out = OutType( i )

  def line_trace( s ):
    return "in:{:0>{n}b} | out:{}".format(
      int( s.in_ ), s.out, n=s.in_nbits
    )

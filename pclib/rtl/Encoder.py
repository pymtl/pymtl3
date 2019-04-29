#=========================================================================
# Encoder.py
#=========================================================================
# A priority encoder for arbitration
#
# Author : Yanghui Ou, Cheng Tan
#   Date : Mar 1, 2019

from builtins import range
from pymtl import *

class Encoder( Component ):
  def construct( s, in_nbits, out_nbits ):

    # Interface

    s.in_ =  InPort( mk_bits( in_nbits  ) )
    s.out = OutPort( mk_bits( out_nbits ) )
    
    # Constants

    s.in_nbits  = in_nbits
    s.out_nbits = out_nbits

    # Logic

    @s.update
    def encode():
      s.out = 0
      for i in range( s.in_nbits ):
        s.out = i if s.in_[i] else s.out
  
  def line_trace( s ):
    return "in:{:0>{n}b} | out:{}".format( 
      int( s.in_ ), s.out, n=s.in_nbits 
    )

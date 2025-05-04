"""
==========================================================================
ChecksumRTL.py
==========================================================================
Register-transfer-level implementation of a single-cycle checksum unit.
The checksum unit is implemented by chaining together eight step units.
Each step unit basically does one iteration of the algorithm (i.e.,
calculates both sum1 and sum2).

Author : Yanghui Ou
  Date : June 6, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.stream import StreamPipeQueue

#-------------------------------------------------------------------------
# Step unit
#-------------------------------------------------------------------------

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the checksum RTL step component
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

class StepUnit( Component ):
  def construct( s ):

    # Interface

    s.word_in  = InPort ( Bits16 )
    s.sum1_in  = InPort ( Bits32 )
    s.sum2_in  = InPort ( Bits32 )
    s.sum1_out = OutPort( Bits32 )
    s.sum2_out = OutPort( Bits32 )

    # Logic

    @update
    def up_step():
      temp1 = zext(s.word_in, 32) + s.sum1_in
      s.sum1_out @= temp1 & 0xffff

      temp2 = s.sum1_out + s.sum2_in
      s.sum2_out @= temp2 & 0xffff

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

#-------------------------------------------------------------------------
# ChecksumRTL
#-------------------------------------------------------------------------

class ChecksumRTL( Component ):

  def construct( s ):

    # Interface

    s.istream = IStreamIfc( Bits128 )
    s.ostream = OStreamIfc( Bits32  )

    # Component

    s.words = [ Wire( Bits16 ) for _ in range( 8 ) ]
    s.sum1  = Wire( Bits32 )
    s.sum2  = Wire( Bits32 )

    s.in_q  = StreamPipeQueue( Bits128, num_entries=1 )
    s.steps = [ StepUnit() for _ in range( 8 ) ]

    # Register input

    connect( s.istream, s.in_q.istream )

    # Decompose input message into 8 words

    for i in range( 8 ):
      s.words[i] //= s.in_q.ostream.msg[i*16:(i+1)*16]

    # Connect step units

    for i in range( 8 ):
      s.steps[i].word_in //= s.words[i]
      if i == 0:
        s.steps[i].sum1_in //= 0
        s.steps[i].sum2_in //= 0
      else:
        s.steps[i].sum1_in //= s.steps[i-1].sum1_out
        s.steps[i].sum2_in //= s.steps[i-1].sum2_out

    s.sum1 //= s.steps[-1].sum1_out
    s.sum2 //= s.steps[-1].sum2_out

    @update
    def up_rtl_ostream():
      go = s.in_q.ostream.val & s.ostream.rdy
      s.ostream.val @= go
      s.in_q.ostream.rdy @= go

    @update
    def up_rtl_sum():
      s.ostream.msg @= ( s.sum2 << 16 ) | s.sum1

  def line_trace( s ):
    return "{}(){}".format( s.istream, s.ostream )

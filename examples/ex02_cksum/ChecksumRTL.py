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
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.queues import PipeQueueRTL

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

    s.recv  = RecvIfcRTL( Bits128 )
    s.send  = SendIfcRTL( Bits32  )

    # Component

    s.words = [ Wire( Bits16 ) for _ in range( 8 ) ]
    s.sum1  = Wire( Bits32 )
    s.sum2  = Wire( Bits32 )

    s.in_q  = PipeQueueRTL( Bits128, num_entries=1 )
    s.steps = [ StepUnit() for _ in range( 8 ) ]

    # Register input

    connect( s.recv, s.in_q.enq )

    # Decompose input message into 8 words

    for i in range( 8 ):
      s.words[i] //= s.in_q.deq.ret[i*16:(i+1)*16]

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
    def up_rtl_send():
      go = s.in_q.deq.rdy & s.send.rdy
      s.send.en     @= go
      s.in_q.deq.en @= go

    @update
    def up_rtl_sum():
      s.send.msg @= ( s.sum2 << 16 ) | s.sum1

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

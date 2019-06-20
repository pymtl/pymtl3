"""
==========================================================================
 ChecksumCL.py
==========================================================================
Cycle level implementation of a checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.cl.DelayPipeCL import DelayPipeDeqCL
from pymtl3.stdlib.cl.queues import NormalQueueCL

from .ChecksumFL import checksum
from .utils import b128_to_words

#-------------------------------------------------------------------------
# ChecksumCL
#-------------------------------------------------------------------------

class ChecksumCL( Component ):

  def construct( s ):

    # Interface

    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.send = NonBlockingCallerIfc( Bits32  )

    # Component

    s.in_q = NormalQueueCL( num_entries=2 )
    s.connect( s.recv, s.in_q.enq )

    @s.update
    def up_checksum_cl():
      if s.in_q.deq.rdy() and s.send.rdy():
        bits = s.in_q.deq()
        words = b128_to_words( bits )
        # Inject a bug and let hypothesis catch it. For example, you can
        # add the following statement:
        # words[5] = b16(0)
        result = checksum( words )
        s.send( result )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# ChecksumCL
#-------------------------------------------------------------------------

class ChecksumMcycleCL( Component ):

  def construct( s, nstages=1 ):

    # Interface

    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.send = NonBlockingCallerIfc( Bits32 )

    # Component

    s.in_q = NormalQueueCL( num_entries=2 )
    s.pipeline = DelayPipeDeqCL( delay = nstages+1 )
    s.connect( s.recv, s.in_q.enq )

    @s.update
    def up_cl_send():
      if s.send.rdy() and s.pipeline.deq.rdy():
        bits = s.pipeline.deq()
        result = checksum( b128_to_words( bits ) )
        s.send( result )

      if s.in_q.deq.rdy() and s.pipeline.enq.rdy():
        s.pipeline.enq( s.in_q.deq() )

  def line_trace( s ):
    return "{}({}){}".format( s.recv, s.pipeline.line_trace(), s.send )

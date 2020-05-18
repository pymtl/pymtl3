"""
==========================================================================
ChecksumCL.py
==========================================================================
Cycle-level implementation of a checksum unit which implements a
simplified version of Fletcher's algorithm. A cycle-level model often
involves an input queue connected to the recv interface to buffer up the
input message and an update block to process each message and send it out
the send interface. In this case, we will simply reuse the checksum
function we developed in ChecksumFL to implement the desired
functionality. To model a latency greater than one, we can add a
DelayPipeDeqCL at the send interface. So instead of sending the result
directly out the send interface we enq the result into the DelayPipeDeqCL
and then wait for the result to appear on the other end of the
DelayPipeDeqCL before sending it out the send interface.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.delays import DelayPipeDeqCL
from pymtl3.stdlib.queues import PipeQueueCL

from .ChecksumFL import checksum
from .utils import b128_to_words

#-------------------------------------------------------------------------
# ChecksumCL
#-------------------------------------------------------------------------

class ChecksumCL( Component ):

  def construct( s ):

    s.recv = CalleeIfcCL( Type=Bits128 )
    s.send = CallerIfcCL( Type=Bits32  )

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Implement the checksum CL component
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; Instantiate a PipeQueueCL with one entry and connect it to the
    #; recv interface. Then create an update block which will check if
    #; the deq interface is ready and the send interface is ready. If
    #; both of these conditions are try, then deq the message, calculate
    #; the checksum using the checksum function from ChecksumFL, and
    #; send the result through the send interface.

    s.in_q = PipeQueueCL( num_entries=2 )
    s.in_q.enq //= s.recv

    @update_once
    def up_checksum_cl():
      if s.in_q.deq.rdy() and s.send.rdy():
        bits = s.in_q.deq()
        words = b128_to_words( bits )

        # Try injecting a bug and let hypothesis catch it. For example,
        # you can add the following to zero out the sixth word before
        # calculating the checksum.
        #
        #  words[5] = b16(0)
        #

        result = checksum( words )
        s.send( result )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

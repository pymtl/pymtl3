"""
========================================================================
Test sources
========================================================================
Test sources with CL or RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""
from collections import deque
from copy import deepcopy

from pymtl3 import *
from pymtl3.stdlib.ifcs import OutValRdyIfc


class TestSrcRTL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0 ):

    # Interface

    s.out = OutValRdyIfc( Type )

    # Data

    s.msgs = deepcopy(msgs)

    # TODO: use wires and ROM to make it translatable
    s.idx = 0
    s.num_msgs = len(s.msgs)
    s.count = 0

    @update_ff
    def up_src():
      if s.reset:
        s.idx   = 0
        s.count = initial_delay
        s.out.val <<= 0

      else:
        if s.out.val & s.out.rdy:
          s.idx += 1
          s.count = interval_delay

        if s.count > 0:
          s.count -= 1
          s.out.val <<= 0

        else: # s.count == 0
          if s.idx < s.num_msgs:
            s.out.val <<= 1
            s.out.msg <<= s.msgs[s.idx]
          else:
            s.out.val <<= 0


  def done( s ):
    return s.idx >= s.num_msgs

  # Line trace

  def line_trace( s ):
    return f"{s.out}"

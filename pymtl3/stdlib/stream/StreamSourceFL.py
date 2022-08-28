"""
========================================================================
StreamSourceFL
========================================================================
Test sources with port interfaces.

Author : Shunning Jiang, Peitian Pan
  Date : Aug 26, 2022
"""
from collections import deque
from copy import deepcopy

from pymtl3 import *
from .ifcs import OStreamIfc


class StreamSourceFL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0 ):

    # Interface

    s.ostream = OStreamIfc( Type )

    # Data

    s.msgs = deepcopy(msgs)

    # TODO: use wires and ROM to make it translatable
    s.idx = 0
    s.count = 0

    @update_ff
    def up_src():
      if s.reset:
        s.idx   = 0
        s.count = initial_delay
        s.ostream.val <<= 0

      else:
        if s.ostream.val & s.ostream.rdy:
          s.idx += 1
          s.count = interval_delay

        if s.count > 0:
          s.count -= 1
          s.ostream.val <<= 0

        else: # s.count == 0
          if s.idx < len(s.msgs):
            s.ostream.val <<= 1
            s.ostream.msg <<= s.msgs[s.idx]
          else:
            s.ostream.val <<= 0


  def done( s ):
    return s.idx >= len(s.msgs)

  # Line trace

  def line_trace( s ):
    return f"{s.ostream}"

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
from random import randint

from pymtl3 import *
from .ifcs import OStreamIfc


class StreamSourceFL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 interval_delay_mode='fixed' ):

    # Interface

    s.ostream = OStreamIfc( Type )

    # Data

    s.msgs = deepcopy(msgs)

    # TODO: use wires and ROM to make it translatable
    s.idx = 0
    s.count = 0
    s.prev_is_none = False

    @update_ff
    def up_src():
      if s.reset:
        s.idx   = 0
        s.count = initial_delay
        s.ostream.val <<= 0

      else:
        if (s.ostream.val & s.ostream.rdy) or s.prev_is_none:
          s.idx += 1
          if ( interval_delay_mode == 'random' ):
            s.count = randint(0,interval_delay)
          else:
            s.count = interval_delay

        if s.count > 0:
          s.count -= 1
          s.ostream.val <<= 0

        else: # s.count == 0
          if s.idx < len(s.msgs):
            if s.msgs[s.idx] is None:
              s.ostream.val <<= 0
              s.prev_is_none = True
            else:
              s.ostream.val <<= 1
              s.ostream.msg <<= s.msgs[s.idx]
              s.prev_is_none = False
          else:
            s.ostream.val <<= 0


  def done( s ):
    return s.idx >= len(s.msgs)

  # Line trace

  def line_trace( s ):
    return f"{s.ostream}"

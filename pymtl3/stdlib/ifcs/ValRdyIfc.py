"""
========================================================================
ValRdyIfc
========================================================================
RTL val/rdy interface.

Author : Shunning Jiang
  Date : Apr 5, 2019
"""
from pymtl3 import *

from .ifcs_utils import valrdy_to_str


class InValRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg = InPort( Type )
    s.val = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

class OutValRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.val = OutPort( int if Type is int else Bits1 )
    s.rdy = InPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

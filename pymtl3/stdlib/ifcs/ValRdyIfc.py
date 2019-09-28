"""
========================================================================
ValRdyIfc
========================================================================
RTL val/rdy interface.

Author : Shunning Jiang
  Date : Apr 5, 2019
"""
from typing import Generic, TypeVar

from pymtl3 import *

from .ifcs_utils import valrdy_to_str


T_InValRdyIfc = TypeVar("T_InValRdyIfc")

class InValRdyIfc( Interface, Generic[T_InValRdyIfc] ):

  def construct( s, Type ):

    s.msg = InPort( Type )
    s.val = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

T_OutValRdyIfc = TypeVar("T_OutValRdyIfc")

class OutValRdyIfc( Interface, Generic[T_OutValRdyIfc] ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.val = OutPort( int if Type is int else Bits1 )
    s.rdy = InPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

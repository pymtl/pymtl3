"""
========================================================================
SendRecvIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou
  Date: Feb 21, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl import *

from .ifcs_utils import enrdy_to_str

#-------------------------------------------------------------------------
# RecvIfcRTL
#-------------------------------------------------------------------------

class RecvIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg =  InPort( Type )
    s.en  =  InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# SendIfcRTL
#-------------------------------------------------------------------------

class SendIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.en  = OutPort( int if Type is int else Bits1 )
    s.rdy =  InPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()

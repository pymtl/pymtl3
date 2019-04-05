#=========================================================================
# EnqDeqIfc.py
#=========================================================================
# RTL implementation of deq and enq interface.
#
# Author: Yanghui Ou
#   Date: Mar 21, 2019

from pymtl import *
from ifcs_utils import enrdy_to_str

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

class EnqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = InPort ( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

class DeqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()

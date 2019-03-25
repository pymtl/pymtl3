#=========================================================================
# SendRecvIfc.py 
#=========================================================================
# RTL implementation of en/rdy micro-protocol.
#
# Author: Yanghui Ou
#   Date: Feb 21, 2019

from pymtl import *

#-------------------------------------------------------------------------
# enrdy_to_str
#-------------------------------------------------------------------------
# A heler function that convert en/rdy interface into string.

def enrdy_to_str( msg, en, rdy ):

  _str   = "{}".format( msg )
  nchars = max( len( _str ), 15 ) 
  
  if en and not rdy:
    _str = "X".ljust( nchars ) # Not allowed
  elif not en and rdy:
    _str = "#".ljust( nchars )
  elif not en and not rdy:
    _str = ".".ljust( nchars )

  return _str.ljust( nchars )
     

#-------------------------------------------------------------------------
# SendRecvIfc
#-------------------------------------------------------------------------

class EnqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg =  InVPort( Type )
    s.en  =  InVPort( int if Type is int else Bits1 )
    s.rdy = OutVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy ) 
  
  def __str__( s ):
    return s.line_trace()

class DeqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutVPort( Type )
    s.en  =  InVPort( int if Type is int else Bits1 )
    s.rdy = OutVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy ) 

  def __str__( s ):
    return s.line_trace()

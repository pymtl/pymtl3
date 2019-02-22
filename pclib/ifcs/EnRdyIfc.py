#=========================================================================
# EnRdyIfc
#=========================================================================
# RTL implementation of enable/rdy interface.
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
  nchars = max( len( str_ ), 15 ) 
  
  if en and not rdy:
    _str = "X".ljust( nchars ) # Not allowed
  elif not en and rdy:
    _str = "#".ljust( nchars )
  elif not en and not rdy:
    _str = ".".ljust( nchars )

  return _str.ljust( nchars )
     

#-------------------------------------------------------------------------
# EnRdyIfc
#-------------------------------------------------------------------------

class InEnRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg =  InVPort( Type )
    s.en  =  InVPort( int if Type is int else Bits1 )
    s.rdy = OutVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.msg ) 

class OutEnRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg = OutVPort( Type )
    s.en  = OutVPort( int if Type is int else Bits1 )
    s.rdy =  InVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.msg ) 

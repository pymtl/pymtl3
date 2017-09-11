from pymtl import *
from pclib.valrdy import valrdy_to_str

class InValRdyIfc( Interface ):

  def __init__( s, Type=int ):
    s.Type = Type

    s.msg = InVPort( Type )
    s.val = InVPort( int if Type is int else Bits1 )
    s.rdy = OutVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

class OutValRdyIfc( Interface ):

  def __init__( s, Type=int ):
    s.Type = Type

    s.msg = OutVPort( Type )
    s.val = OutVPort( int if Type is int else Bits1 )
    s.rdy = InVPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

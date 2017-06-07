from pymtl import *
from pclib.valrdy import valrdy_to_str

class EnRdyBundle( Interface ):

  def __init__( s, Type=int ):
    s.Type = Type

    s.msg = ValuePort( Type )
    s.en  = ValuePort( Bits1 )
    s.rdy = ValuePort( Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.en, s.rdy )

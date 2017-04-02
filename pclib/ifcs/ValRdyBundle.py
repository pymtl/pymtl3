from pymtl import *
from pclib.valrdy import valrdy_to_str

class ValRdyBundle( PortBundle ):

  def __init__( s, type_=int ):
    s.msg_type = type_

    s.msg = ValuePort( type_ )
    s.val = ValuePort( Bits1 )
    s.rdy = ValuePort( Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

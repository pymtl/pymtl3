from pymtl import *
from pclib.valrdy import valrdy_to_str

class EnRdyBundle( PortBundle ):

  def __init__( s, type_=int ):
    s.msg_type = type_

    s.msg = ValuePort( type_ )
    s.en  = ValuePort( Bits1 )
    s.rdy = ValuePort( Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.en, s.rdy )

from pymtl import *
from pclib.valrdy import valrdy_to_str

class ValRdyBundle( PortBundle ):

  def __init__( s, nmsgs = 1 ):
    s.msg = [ ValuePort(int) for _ in xrange(nmsgs) ]
    s.val = ValuePort(int)
    s.rdy = ValuePort(int)

  def line_trace( s ):
    return valrdy_to_str( ",".join([str(x) for x in s.msg]), s.val, s.rdy )

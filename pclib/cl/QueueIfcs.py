from pymtl import *

class EnqIfc( PortBundle ):

  def __init__( s, enq = None, rdy = None ):
    s.enq = MethodPort()
    s.rdy = MethodPort()

    if enq: s.enq |= enq
    if rdy: s.rdy |= rdy


class DeqIfc( PortBundle ):

  def __init__( s, deq = None, rdy = None ):
    s.deq = MethodPort()
    s.rdy = MethodPort()

    if deq: s.deq |= deq
    if rdy: s.rdy |= rdy

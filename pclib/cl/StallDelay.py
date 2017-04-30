from pymtl import *
from random import Random

class RandomStall( MethodsConnection ):

  def __init__( s, stall_prob=0.5, seed=0x3 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    # We keep our own internal random number generator to keep the state
    # of this generator completely separate from other generators. This
    # ensure that any delays are reproducable.

    s.rgen = Random()
    s.rgen.seed(seed)
    s.stall_prob = stall_prob

  def recv( s, msg ):
    s.send( msg )

  def recv_rdy( s ):
    return s.send_rdy() and ( s.rgen.random() > s.stall_prob )

class FixDelay( MethodsConnection ):

  def __init__( s, delay=5 ):
    s.send     = MethodPort()
    s.recv_rdy = MethodPort()

    s.delay = deque( [None] * delay )
    s.rgen = Random()
    s.rgen.seed(seed)
    s.stall_prob = stall_prob

    # @s.update
    # def up_delay():
      

  # def recv( s, msg ):

  # def send_rdy( s ):
    # return s.

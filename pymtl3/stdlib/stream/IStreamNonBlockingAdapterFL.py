from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from .ifcs.ifcs import IStreamIfc

class IStreamNonBlockingAdapterFL( Component ):

  @non_blocking( lambda s: s.entry is not None )
  def deq( s ):
    ret = s.entry
    s.entry = None
    return ret

  def construct( s, Type ):
    s.istream = IStreamIfc( Type )
    s.entry = None

    @update_once
    def up_recv_rdy():
      s.istream.rdy @= (s.entry is None)

    @update_once
    def up_recv_msg():
      if (s.entry is None) & s.istream.val:
        s.entry = clone_deepcopy( s.istream.msg )

    s.add_constraints( M( s.deq )     < U( up_recv_rdy ), # deq before recv in a cycle -- pipe behavior
                       M( s.deq.rdy ) < U( up_recv_rdy ),
                       U( up_recv_rdy ) < U( up_recv_msg ) )

  def line_trace( s ):
    return f"{s.istream}({s.entry})"

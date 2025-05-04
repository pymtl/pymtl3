from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from .ifcs.ifcs import OStreamIfc

class OStreamEnqAdapterFL( Component ):
  # TODO (PP): remove this file during the future clean up to ensure consistent
  # naming across adapters. This adapter is now deprecated and we should use
  # OStreamNonBlockingAdapterFL instead.

  @non_blocking( lambda s: s.entry is None )
  def enq( s, msg ):
    s.entry = clone_deepcopy( msg )

  def construct( s, Type ):
    s.ostream = OStreamIfc( Type )

    s.entry = None
    s.sent  = Wire()

    @update_once
    def up_send():
      if s.entry is None:
        s.ostream.val @= 0
      else:
        s.ostream.val @= 1
        s.ostream.msg @= s.entry

    @update_ff
    def up_sent():
      s.sent <<= s.ostream.val & s.ostream.rdy

    @update_once
    def up_clear():
      if s.sent: # constraints reverse this
        s.entry = None

    s.add_constraints(
      U( up_clear )  < M( s.enq ),
      U( up_clear )  < M( s.enq.rdy ),
      M( s.enq )     < U( up_send ),
      M( s.enq.rdy ) < U( up_send )
    )

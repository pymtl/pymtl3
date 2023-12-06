import greenlet
from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from .ifcs.ifcs import OStreamIfc

class OStreamBlockingAdapterFL( Component ):

  @blocking
  def enq( s, msg ):
    while s.entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.entry = clone_deepcopy(msg)

  def construct( s, Type ):
    s.ostream = OStreamIfc( Type )
    s.entry = None

    s.sent = Wire()

    @update
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

    s.add_constraints( U( up_clear ) < M( s.enq ),
                       M( s.enq )    < U( up_send ) )

  def line_trace( s ):
    return f"{s.ostream}({s.entry})"

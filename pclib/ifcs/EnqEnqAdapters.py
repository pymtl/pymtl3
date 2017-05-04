from pymtl import *
from EnqIfcs import EnqIfcRTL, EnqIfcCL

class EnqIfcRTL_EnqIfcCL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = EnqIfcRTL( Type )
    s.send = EnqIfcCL( Type )

    @s.update
    def up_rdyblk():
      s.recv.rdy = s.send.rdy()

    @s.update
    def up_enblk():
      if s.recv.en:
        s.send.enq( s.recv.msg )

class EnqIfcCL_EnqIfcRTL( MethodsConnection ):

  def __init__( s, Type ):

    s.msg = Wire( Type )
    s.en  = Wire( Bits1 )
    s.rdy = Wire( Bits1 )

    s.recv = EnqIfcCL ( Type )
    s.send = EnqIfcRTL( Type )

    s.recv.enq |= s.recv_
    s.recv.rdy |= s.recv_rdy_

    @s.update
    def up_rdyblk():
      s.rdy = s.send.rdy
      # I put it here because up_rdy < s.send
      s.en  = Bits1( False )
      s.msg = Type()

    @s.update
    def up_enblk():
      s.send.en  = s.en
      s.send.msg = s.msg

    s.add_constraints(
      U(up_rdyblk) < M(s.recv_rdy_),
      M(s.recv_  ) < U(up_enblk),
    )

  def recv_( s, msg ):
    s.msg = msg
    s.en  = Bits1( True )

  def recv_rdy_( s ):
    return s.rdy

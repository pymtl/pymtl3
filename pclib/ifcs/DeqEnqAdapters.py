from pymtl import *
from DeqIfcs import DeqIfcRTL, DeqIfcCL
from EnqIfcs import EnqIfcRTL, EnqIfcCL

class DeqIfcRTL_EnqIfcRTL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = DeqIfcRTL( Type )
    s.send = EnqIfcRTL( Type )

    @s.update
    def up_DeqIfcRTL_EnqIfcRTL():
      s.recv.en  = Bits1( False )
      s.send.en  = Bits1( False )
      s.send.msg = Type()

      if s.send.rdy & s.recv.rdy:
        s.recv.en = Bits1( True )
        s.send.en = Bits1( True )
        s.send.msg = s.recv.msg

class DeqIfcRTL_EnqIfcCL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = DeqIfcRTL( Type )
    s.send = EnqIfcCL ( Type )

    @s.update
    def up_DeqIfcRTL_EnqIfcCL():
      s.recv.en  = Bits1( False )

      if s.send.rdy() & s.recv.rdy:
        s.recv.en = Bits1( True )
        s.send.enq( s.recv.msg )


class DeqIfcCL_EnqIfcRTL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = DeqIfcCL ( Type )
    s.send = EnqIfcRTL( Type )

    @s.update
    def up_DeqIfcCL_EnqIfcRTL():
      s.send.en = Bits1( False )

      if s.send.rdy & s.recv.rdy():
        s.send.en  = Bits1( True )
        s.send.msg = s.recv.deq()

class DeqIfcCL_EnqIfcCL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = DeqIfcCL( Type )
    s.send = EnqIfcCL( Type )

    @s.update
    def up_DeqIfcCL_EnqIfcCL():
      if s.send.rdy() & s.recv.rdy():
        s.send.enq( s.recv.deq() )

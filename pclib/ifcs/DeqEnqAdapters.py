from pymtl import *
from DeqIfcs import DeqIfcRTL, DeqIfcCL
from EnqIfcs import EnqIfcRTL, EnqIfcCL

class BaseDeqEnqAdapter( MethodsConnection ):
  # in order
  ifcs   = 'recv', 'send'
  types  = 'Deq' , 'Enq'

class DeqIfcRTL_EnqIfcRTL( BaseDeqEnqAdapter ):
  levels = 'rtl', 'rtl'

  def __init__( s, Type1, Type2 ):

    s.recv = DeqIfcRTL( Type1 )
    s.send = EnqIfcRTL( Type2 )

    @s.update
    def up_DeqIfcRTL_EnqIfcRTL():
      s.recv.en  = Bits1( False )
      s.send.en  = Bits1( False )
      s.send.msg = Type2()

      if s.send.rdy & s.recv.rdy:
        s.recv.en = Bits1( True )
        s.send.en = Bits1( True )
        s.send.msg = s.recv.msg

class DeqIfcRTL_EnqIfcCL( BaseDeqEnqAdapter ):
  levels = 'rtl', 'cl'

  def __init__( s, Type1, Type2 ):

    s.recv = DeqIfcRTL( Type1 )
    s.send = EnqIfcCL ( Type2 )

    @s.update
    def up_DeqIfcRTL_EnqIfcCL():
      s.recv.en  = Bits1( False )

      if s.send.rdy() & s.recv.rdy:
        s.recv.en = Bits1( True )
        s.send.enq( s.recv.msg )


class DeqIfcCL_EnqIfcRTL( BaseDeqEnqAdapter ):
  levels = 'cl', 'rtl'

  def __init__( s, Type1, Type2 ):

    s.recv = DeqIfcCL ( Type1 )
    s.send = EnqIfcRTL( Type2 )

    @s.update
    def up_DeqIfcCL_EnqIfcRTL():
      s.send.en  = Bits1( False )
      s.send.msg = Type2()

      if s.send.rdy & s.recv.rdy():
        s.send.en  = Bits1( True )
        s.send.msg = s.recv.deq()

class DeqIfcCL_EnqIfcCL( BaseDeqEnqAdapter ):
  levels = 'cl', 'cl'

  def __init__( s, Type1, Type2 ):

    s.recv = DeqIfcCL( Type1 )
    s.send = EnqIfcCL( Type2 )

    @s.update
    def up_DeqIfcCL_EnqIfcCL():
      if s.send.rdy() & s.recv.rdy():
        s.send.enq( s.recv.deq() )

register_adapter( DeqIfcRTL_EnqIfcRTL )
register_adapter( DeqIfcRTL_EnqIfcCL  )
register_adapter( DeqIfcCL_EnqIfcRTL  )
register_adapter( DeqIfcCL_EnqIfcCL   )

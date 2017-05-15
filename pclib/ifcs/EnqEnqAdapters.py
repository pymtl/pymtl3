from pymtl import *
from EnqIfcs import EnqIfcRTL, EnqIfcCL

class EnqIfc_CLtoRTL_Adapter( MethodsConnection ):
  ifcs  = 'recv', 'send'
  types = 'Enq', 'Enq'

  def __init__( s, Type1, level1, Type2, level2 ):

    assert level1 =='cl' and level2 == 'rtl'

    s.recv = EnqIfcCL( Type1 )
    s.recv.enq |= s.recv_
    s.recv.rdy |= s.recv_rdy_

    s.send = EnqIfcRTL( Type2 )

    s.msg = Wire( Type1 )
    s.en  = Wire( Bits1 )
    s.rdy = Wire( Bits1 )

    @s.update
    def up_rdyblk_cl_rtl(): # from RTL side to CL side, write s.rdy
      s.rdy = s.send.rdy

    @s.update
    def up_clear_en():
      s.en  = Bits1( False )
      s.msg = Type1()

    @s.update
    def up_enblk_cl_rtl(): # copy the CL msg to RTL side, read s.msg
      s.send.en  = s.en
      s.send.msg = s.msg

    s.add_constraints(
      U(up_clear_en) < M(s.recv_), # clear en/msg before recv_

      M(s.recv_rdy_) < U(up_rdyblk_cl_rtl), # comb behavior, RAW s.rdy
      M(s.recv_    ) < U(up_enblk_cl_rtl),  # comb behavior, RAW s.msg
    )

  def recv_( s, msg ): # write msg
   s.msg = msg
   s.en  = Bits1( True )

  def recv_rdy_( s ): # read s.rdy
    return s.rdy

class EnqIfc_RTLtoCL_Adapter( MethodsConnection ):
  ifcs  = 'recv', 'send'
  types = 'Enq', 'Enq'

  def __init__( s, Type1, level1, Type2, level2 ):

    assert level1 == 'rtl' and level2 == 'cl'

    s.recv = EnqIfcRTL( Type1 )
    s.send = EnqIfcCL( Type2 )

    @s.update
    def up_rdyblk_rtl_cl():
      s.recv.rdy = s.send.rdy()

    @s.update
    def up_enblk_rtl_cl():
      if s.recv.en:
        s.send.enq( s.recv.msg )

class EnqIfc_CLtoFL_Adapter( MethodsConnection ):
  pass

class EnqIfc_FLtoCL_Adapter( MethodsConnection ):
  ifcs  = 'recv', 'send'
  types = 'Enq', 'Enq'

  def __init__( s, Type1, level1, Type2, level2 ):

    assert level1 == 'fl' and level2 == 'cl'

    s.recv = EnqIfcFL()
    s.send = EnqIfcCL( Type2 )

  # @pausable
  def enq( s, msg ):
    while not s.send.rdy():
      greenlet.getcurrent().parent.switch(0)
    s.send.enq( msg )

register_adapter( EnqIfc_CLtoRTL_Adapter, 'cl', 'rtl' )
register_adapter( EnqIfc_RTLtoCL_Adapter, 'rtl', 'cl' )
register_adapter( EnqIfc_FLtoCL_Adapter,  'fl', 'cl' )
# register_adapter( EnqIfc_CLtoFL_Adapter,  'cl', 'fl' )

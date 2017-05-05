from pymtl import *
from EnqIfcs import EnqIfcRTL, EnqIfcCL

class EnqIfc_EnqIfc_Adapter( MethodsConnection ):
  ifcs  = 'recv', 'send'
  types = 'Enq', 'Enq'

  def __init__( s, Type1, level1, Type2, level2 ):

    if level1 == 'rtl':
      s.recv = EnqIfcRTL( Type1 )
    else:
      s.recv = EnqIfcCL ( Type1 )
      s.recv.enq |= s.recv_
      s.recv.rdy |= s.recv_rdy_

    if level2 == 'rtl':
      s.send = EnqIfcRTL( Type2 )
    else:
      s.send = EnqIfcCL( Type2 )

    if   level1 == level2:
      assert Type1 == Type2 # this adapter cannot convert types
      s.recv |= s.send

    elif level1 == 'cl' and level2 == 'rtl':
      s.msg = Wire( Type1 )
      s.en  = Wire( Bits1 )
      s.rdy = Wire( Bits1 )

      @s.update
      def up_rdyblk_cl_rtl(): # different names
        s.rdy = s.send.rdy
        # I put it here because up_rdy < s.send
        s.en  = Bits1( False )
        s.msg = Type1()

      @s.update
      def up_enblk_cl_rtl():
        s.send.en  = s.en
        s.send.msg = s.msg

      s.add_constraints(
        U(up_rdyblk_cl_rtl) < M(s.recv_rdy_),
        M(s.recv_  ) < U(up_enblk_cl_rtl),
      )
    elif level1 == 'rtl' and level2 == 'cl':

      @s.update
      def up_rdyblk_rtl_cl():
        s.recv.rdy = s.send.rdy()

      @s.update
      def up_enblk_rtl_cl():
        if s.recv.en:
          s.send.enq( s.recv.msg )

  def recv_( s, msg ):
   s.msg = msg
   s.en  = Bits1( True )

  def recv_rdy_( s ):
    return s.rdy


for l1 in [ 'rtl', 'cl' ]:
  for l2 in [ 'rtl', 'cl' ]:
    register_adapter( EnqIfc_EnqIfc_Adapter, l1, l2 )

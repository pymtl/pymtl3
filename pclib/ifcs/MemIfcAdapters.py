from pymtl import *
from pclib.cl import ValidEntry
from MemIfcs import MemIfcRTL, MemIfcCL, MemIfcFL
from greenlet import greenlet

class MemIfcAdapter( MethodsAdapt ):
  ifcs  = 'left', 'right'
  types = 'Mem', 'Mem'

  def __init__( s, Type1, level1, Type2, level2 ):
    if Type1: s.req_type1, s.resp_type1 = Type1[0], Type1[1]
    if Type2: s.req_type2, s.resp_type2 = Type2[0], Type2[1]

    assert level1 != level2, "This is when we need adapters"
    # only support these right now

    if   level1 == 'fl' and level2 == 'cl':

      s.buf  = ValidEntry( val=False, msg = None )

      s.left  = MemIfcFL()
      s.left.read  |= s.read_
      s.left.write |= s.write_
      s.left.amo   |= s.amo_

      s.right = MemIfcCL( Type2 )
      s.right.resp.enq |= s.recv_
      s.right.resp.rdy |= s.recv_rdy_

    elif level1 == 'cl' and level2 == 'fl': # needs adapter

      s.left  = MemIfcCL( Type1 )
      s.left.req.enq |= s.recv_
      s.left.req.rdy |= s.recv_rdy_

      s.right = MemIfcFL()

      s.buf  = ValidEntry( val=False, msg = None )

      @s.update
      def up_memifc_cl_fl_blk():

        if s.left.resp.rdy() and s.buf.valid:
          req = s.buf.msg
          len = req.len if req.len else ( s.req_type1.data.nbits >> 3 )

          if   req.type_ == s.req_type1.TYPE_READ:
            resp = s.resp_type1.mk_rd( req.opaque, len, s.right.read( req.addr, len ) )

          elif req.type_ == s.req_type1.TYPE_WRITE:
            s.right.write( req.addr, len, req.data )
            resp = s.resp_type1.mk_wr( req.opaque )

          else: # AMOS
            resp = s.resp_type1.mk_msg( req.type_, req.opaque, 0, len, \
                                 s.right.amo( req.type_, req.addr, len, req.data ) )

          s.left.resp.enq( resp )
          s.buf = ValidEntry( val=False, msg = None )

      s.add_constraints(
        U(up_memifc_cl_fl_blk) < M(s.left.req.enq), # pipe behavior, send < recv
        U(up_memifc_cl_fl_blk) < M(s.left.req.rdy),
      )

    elif level1 == 'fl' and level2 == 'rtl':
      pass

    elif level1 == 'rtl' and level2 == 'fl':

      s.left  = MemIfcRTL( Type1 )
      s.right = MemIfcFL()

      @s.update
      def up_memifc_req_rdy_rtl_fl():
        s.left.req.rdy = Bits1( 1 )

      @s.update
      def up_memifc_req_en_rtl_fl():
        if s.left.req.en & s.left.resp.rdy:
          req = s.left.req.msg

          len = req.len if req.len else ( s.req_type1.data.nbits >> 3 )

          if   req.type_ == s.req_type1.TYPE_READ:
            resp = s.resp_type1.mk_rd( req.opaque, len, s.right.read( req.addr, len ) )

          elif req.type_ == s.req_type1.TYPE_WRITE:
            s.right.write( req.addr, len, req.data )
            resp = s.resp_type1.mk_wr( req.opaque )

          else: # AMOS
            resp = s.resp_type1.mk_msg( req.type_, req.opaque, 0, len, \
                                 s.right.amo( req.type_, req.addr, len, req.data ) )

          s.left.resp.en  = Bits1( 1 )
          s.left.resp.msg = resp

    elif level1 == 'cl' and level2 == 'rtl':
      s.left  = MemIfcCL ( Type1 )
      s.right = MemIfcRTL( Type2 )

      s.connect( s.left.req, s.right.req )
      s.connect( s.right.resp, s.left.resp )

    elif level1 == 'rtl' and level2 == 'cl':
      s.left  = MemIfcRTL( Type1 )
      s.right = MemIfcCL ( Type2 )

      s.connect( s.left.req, s.right.req )
      s.connect( s.right.resp, s.left.resp )

  def recv_( s, msg ): # Recv can be used for left's req, or right's resp
    s.buf = ValidEntry( val=True, msg=msg )

  def recv_rdy_( s ):
    return not s.buf.val

  # @pausable
  def read_( s, addr, nbytes ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_rd( 0, addr, nbytes ) )

    while not s.buf.val:
      greenlet.getcurrent().parent.switch(0)

    ret = s.buf.msg.data
    s.buf = ValidEntry( False, None )
    return ret

  # @pausable
  def write_( s, addr, nbytes, data ):
    
    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_wr( 0, addr, nbytes, data ) )

    while not s.buf.val:
      greenlet.getcurrent().parent.switch(0)

    s.buf = ValidEntry( False, None )

  # @pausable
  def amo_( s, amo, addr, nbytes, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_msg( amo, 0, addr, nbytes ) )

    while not s.buf.val:
      greenlet.getcurrent().parent.switch(0)

    ret = s.buf.msg.data
    s.buf = ValidEntry( False, None )
    return ret

for l1 in [ 'fl','cl','rtl' ]:
  for l2 in [ 'fl','cl','rtl' ]:
    if l1 != l2:
      register_adapter( MemIfcAdapter, l1, l2 )

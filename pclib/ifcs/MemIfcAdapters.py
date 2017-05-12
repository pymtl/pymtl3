from pymtl import *
from MemIfcs import MemIfcRTL, MemIfcCL, MemIfcFL
from greenlet import greenlet

class MemIfcAdapter( MethodsAdapt ):
  ifcs  = 'left', 'right'
  types = 'Mem', 'Mem'

  def __init__( s, Type1, level1, Type2, level2 ):
    if Type1: s.req_type1, s.resp_type1 = Type1[0], Type1[1]
    if Type2: s.req_type2, s.resp_type2 = Type2[0], Type2[1]

    # only support these right now

    if   level1 == 'cl' and level2 == 'fl': # needs adapter

      s.left  = MemIfcCL( Type1 )
      s.left.req.enq |= s.recv_
      s.left.req.rdy |= s.recv_rdy_

      s.right = MemIfcFL()

      s.msg = None

      @s.update
      def up_memifc_fl_cl_adapter():

        if s.left.resp.rdy() and s.msg:
          req = s.msg

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
          s.msg = None

      s.add_constraints(
        U(up_memifc_fl_cl_adapter) < M(s.left.req.enq), # bypass behavior, send < recv
        U(up_memifc_fl_cl_adapter) < M(s.left.req.rdy),
      )

    elif level1 == 'fl' and level2 == 'cl':

      s.msg = None

      s.left  = MemIfcFL()
      s.left.read  |= s.read_
      s.left.write |= s.write_
      s.left.amo   |= s.amo_

      s.right = MemIfcCL( Type2 )
      s.right.resp.enq |= s.recv_
      s.right.resp.rdy |= s.recv_rdy_

    else:
      if   level1 == 'fl':  s.left  = MemIfcFL ()
      elif level1 == 'cl':  s.left  = MemIfcCL ( Type1 )
      else:                 s.left  = MemIfcRTL( Type1 )

      if   level1 == 'fl':  s.right = MemIfcFL ()
      elif level1 == 'cl':  s.right = MemIfcCL ( Type2 )
      else:                 s.right = MemIfcRTL( Type2 )

      s.connect( s.left, s.right )

  def recv_( s, msg ): # Recv can be used for left's req, or right's resp
    s.msg = msg

  def recv_rdy_( s ):
    return not s.msg

  # @pausable
  def read_( s, addr, nbytes ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_rd( 0, addr, nbytes ) )

    while not s.msg:
      greenlet.getcurrent().parent.switch(0)

    ret = s.msg.data
    s.msg = None
    return ret

  # @pausable
  def write_( s, addr, nbytes, data ):
    
    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_wr( 0, addr, nbytes, data ) )

    while not s.msg:
      greenlet.getcurrent().parent.switch(0)

    s.msg = None

  # @pausable
  def amo_( s, amo, addr, nbytes, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    while not s.msg:
      greenlet.getcurrent().parent.switch(0)

    s.right.req.enq( s.req_type2.mk_msg( amo, 0, addr, nbytes ) )

    ret = s.msg.data
    s.msg = None
    return ret

for l1 in [ 'rtl', 'cl', 'fl' ]:
  for l2 in [ 'rtl', 'cl', 'fl' ]:
    register_adapter( MemIfcAdapter, l1, l2 )

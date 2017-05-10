from pymtl import *
from MemIfcs import MemIfcRTL, MemIfcCL, MemIfcFL

class MemIfcAdapter( MethodsConnection ):
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

      s.req = None
      
      @s.update
      def up_memifc_fl_cl_adapter():

        if s.left.resp.rdy() and s.req:
          req = s.req

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
          s.req = None

      s.add_constraints(
        U(up_memifc_fl_cl_adapter) < M(s.left.req.enq), # bypass behavior, send < recv
        U(up_memifc_fl_cl_adapter) < M(s.left.req.rdy),
      )

    else:
      if   level1 == 'fl':  s.left  = MemIfcFL ()
      elif level1 == 'cl':  s.left  = MemIfcCL ( Type1 )
      else:                 s.left  = MemIfcRTL( Type1 )

      if   level1 == 'fl':  s.right = MemIfcFL ()
      elif level1 == 'cl':  s.right = MemIfcCL ( Type2 )
      else:                 s.right = MemIfcRTL( Type2 )

      s.connect( s.left, s.right )

  def recv_( s, msg ):
    s.req = msg

  def recv_rdy_( s ):
    return not s.req

for l1 in [ 'rtl', 'cl', 'fl' ]:
  for l2 in [ 'rtl', 'cl', 'fl' ]:
    register_adapter( MemIfcAdapter, l1, l2 )

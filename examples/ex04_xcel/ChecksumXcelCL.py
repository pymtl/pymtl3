"""
==========================================================================
ChecksumXcelCL.py
==========================================================================
Cycle level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.cl.queues import NormalQueueCL, BypassQueueCL
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMsgType
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMinionIfcCL

from examples.ex02_cksum.ChecksumCL import ChecksumCL
from examples.ex02_cksum.ChecksumRTL import ChecksumRTL
from examples.ex02_cksum.utils import words_to_b128

#-------------------------------------------------------------------------
# A piece of CL logic that converts Bits32 to a response message
#-------------------------------------------------------------------------

class CombLogicCL( Component ):

  def construct( s ):
    _, Resp = mk_xcel_msg( 5, 32 )
    s.Resp = Resp
    s.data = None 

    s.add_constraints( M(s.write) < M(s.read) )
  
  @method_port
  def write( data ):
    s.data = b32(data)

  @method_port
  def read( type_ ):
    return s.Resp( b1(type_), s.data ) 

#-------------------------------------------------------------------------
# A piece of CL logic that converts Bits32 to a response message
#-------------------------------------------------------------------------

class ChecksumXcelCL( Component ):

  def construct( s ):

    # Interface

    ReqType, RespType = mk_xcel_msg( 5, 32 )
    s.RespType = RespType

    s.xcel = XcelMinionIfcCL( ReqType, RespType )

    # State encoding

    s.XCFG = 0
    s.WAIT = 1
    s.BUSY = 2

    # Local paramters

    RD = XcelMsgType.READ
    WR = XcelMsgType.WRITE

    # Components

    s.in_q = NormalQueueCL( num_entries=2 )
    s.reg_file = [ b32(0) for _ in range(6) ]
    s.checksum_unit = ChecksumCL()

    s.busy = False
    s.state = s.XCFG

    s.connect( s.xcel.req, s.in_q.enq )
    
    # TODO: replace out_q with a combinational adapter
    s.out_q = BypassQueueCL( num_entries=1 )
    s.connect( s.checksum_unit.send, s.out_q.enq )

    @s.update
    def up_tick():
      if s.state == s.XCFG:
        # Dequeue a request message from input queue and send response.
        if s.in_q.deq.rdy() and s.xcel.resp.rdy():
          req = s.in_q.deq()
          if req.type_ == RD:
            s.xcel.resp( s.RespType( RD, s.reg_file[ int(req.addr) ] ) )
          elif req.type_ == XcelMsgType.WRITE:
            s.reg_file[ int(req.addr) ] = req.data
            s.xcel.resp( s.RespType( WR, 0 ) )
            
            # If the go bit is written
            if req.addr == 4: 
              if s.checksum_unit.recv.rdy():
                s.state = s.BUSY
                words = []
                for i in range( 4 ):
                  words.append( s.reg_file[i][0 :16] )
                  words.append( s.reg_file[i][16:32] )
                s.checksum_unit.recv( words_to_b128( words ) )
              else:
                s.state = s.WAIT

      elif s.state == s.WAIT:
        if s.checksum_unit.recv.rdy():
          s.state == s.BUSY
          words = []
          for i in range( 4 ):
            words.append( s.reg_file[i][0 :16] )
            words.append( s.reg_file[i][16:32] )
          s.checksum_unit.recv( words_to_b128( words ) )
          s.state = s.BUSY

      else: # s.state == s.BUSY
        if s.out_q.deq.rdy():
          s.reg_file[5] = s.out_q.deq()
          s.state = s.XCFG

  def line_trace( s ):
    state_str = (
      "XCFG" if s.state == s.XCFG else
      "WAIT" if s.state == s.WAIT else
      "BUSY" if s.state == s.BUSY else
      "XXXX"
    )
    return "{}({}){}".format( s.xcel.req, state_str, s.xcel.resp )

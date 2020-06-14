"""
#=========================================================================
# MemIfcs
#=========================================================================
#
# Author: Shunning Jiang
# Date  : May 19, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim

from ..mem_ifcs import MemMasterIfcFL, MemMinionIfcCL
from ..MemMsg import MemMsgType, mk_mem_msg


def test_mem_fl_cl_adapter():

  class SomeMasterFL( Component ):
    def construct( s, base, has_loop=0 ):
      s.mem = MemMasterIfcFL()

      s.addr = 0x1000 + base
      s.end  = 0x1000 + base + 0x10

      s.trace = "                   "

      if has_loop == 1:
        @update_once
        def up_master_while():
          s.trace = "                  "
          while s.addr < s.end:
            s.mem.write( s.addr, 4, 0xdead0000 | s.addr )
            s.trace = "wr 0x{:x}         ".format( s.addr )
            x = s.mem.read( s.addr, 4 )
            s.trace = "rd 0x{:x} {}".format( s.addr, x )
            s.addr += 4
      else:
        @update_once
        def up_master_noloop():
          s.trace = "#                 "
          s.mem.write( s.addr, 4, 0xdead0000 | s.addr )
          s.trace = "wr 0x{:x}         ".format( s.addr )
          x = s.mem.read( s.addr, 4 )
          s.trace = "rd 0x{:x} {}".format( s.addr, x )
          s.addr += 4

    def done( s ):
      return s.addr >= s.end

    def line_trace( s ):
      return s.trace

  class SomeMinionCL( Component ):

    def recv( s, msg ):
      assert s.entry is None
      s.entry = msg

    def recv_rdy( s ):
      return s.entry is None

    def read( s, addr, nbytes ):
      nbytes = int(nbytes)
      nbits = nbytes << 3
      ret, shamt = Bits( nbits, 0 ), Bits( nbits, 0 )
      addr = int(addr)
      end  = addr + nbytes
      for j in range( addr, end ):
        ret += Bits( nbits, s.memory[j] ) << shamt
        shamt += 8
      return ret

    def write( s, addr, nbytes, data ):
      tmp  = int(data)
      addr = int(addr)
      end  = addr + int(nbytes)
      for j in range( addr, end ):
        s.memory[j] = tmp & 255
        tmp >>= 8

    def construct( s, req_class, resp_class ):
      s.mem = MemMinionIfcCL( req_class, resp_class, s.recv, s.recv_rdy )
      s.entry = None

      s.memory = bytearray( 2**20 )

      @update_once
      def up_process():

        if s.entry is not None and s.mem.resp.rdy():

          # Dequeue memory request message

          req     = s.entry
          s.entry = None

          len_ = int(req.len)
          if not len_: len_ = req_class.data_nbits >> 3

          if   req.type_ == MemMsgType.READ:
            resp = resp_class( req.type_, req.opaque, 0, req.len,
                               s.read( req.addr, len_ ) )

          elif req.type_ == MemMsgType.WRITE:
            s.write( req.addr, len_, req.data )
            resp = resp_class( req.type_, req.opaque, 0, 0, 0 )

          s.mem.resp( resp )

      s.add_constraints( U(up_process) < M(s.mem.req) ) # definite pipe behavior

    def line_trace( s ):
      return str(s.mem)

  class TestHarness( Component ):
    def construct( s ):
      s.master = [ SomeMasterFL( i*0x222, i ) for i in range(2) ]
      s.minion = [ SomeMinionCL( *mk_mem_msg(8,32,32) ) for _ in range(2) ]
      for i in range(2):
        s.minion[i].mem //= s.master[i].mem

    def line_trace( s ):
      return "|".join( [ x.line_trace() for x in s.master ] ) + " >>> " + \
             "|".join( [ x.line_trace() for x in s.minion ] )

    def done( s ):
      return all( [ x.done() for x in s.master ] )

  # Run simulation

  run_sim( TestHarness() )

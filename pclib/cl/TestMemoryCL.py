"""
========================================================================
TestMemory
========================================================================
A behavioral Test Memory which is parameterized based on the number of
memory request/response ports. This version is a little different from
the one in pclib because we actually use the memory messages correctly
in the interface.

Author : Shunning Jiang
Date   : Mar 12, 2018
"""

from __future__ import absolute_import, division, print_function

from pclib.ifcs import MemMsgType, mk_mem_msg
from pymtl import *

from .DelayPipeCL import DelayPipeDeqCL

# BRGTC2 custom MemMsg modified for RISC-V 32


#- - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - -
#-------------------------------------------------------------------------
# BRGTC2
#-------------------------------------------------------------------------
# The AMO implementations (and MemMsg) has been updated to match RISC-V.
#
# There is also a small fix to the AMO ops to handle signed ops. The AMO
# operations act on the bitwidth of the processor architecture, so the
# read_data from the TestMemory used with AMOs cannot just be the memory
# request message size (e.g., 128b):
#
#         read_data = Bits( s.field_nbits( 'data' ) )
#
# It must instead be the number of bytes matching the bitwidth in the
# processor (e.g., 32b):
#
#         read_data = Bits( nbytes*8 )
#
# Otherwise for example we would be reading 128b from the memory and
# comparing that to the 32b value from the request message.
#
#-------------------------------------------------------------------------
#- - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - -

READ       = 0
WRITE      = 1
# write no-refill
WRITE_INIT = 2
AMO_ADD    = 3
AMO_AND    = 4
AMO_OR     = 5
AMO_SWAP   = 6
AMO_MIN    = 7
AMO_MINU   = 8
AMO_MAX    = 9
AMO_MAXU   = 10
AMO_XOR    = 11

AMO_FUNS = { AMO_ADD  : lambda m,a : m+a,
             AMO_AND  : lambda m,a : m&a,
             AMO_OR   : lambda m,a : m|a,
             AMO_SWAP : lambda m,a : a,
             AMO_MIN  : lambda m,a : m if m.int() < a.int() else a,
             AMO_MINU : min,
             AMO_MAX  : lambda m,a : m if m.int() > a.int() else a,
             AMO_MAXU : max,
             AMO_XOR  : lambda m,a : m^a,
           }

#-------------------------------------------------------------------------
# TestMemory
#-------------------------------------------------------------------------


class TestMemory( object ):
  def __init__( s, mem_nbytes=1<<20 ):
    s.mem       = bytearray( mem_nbytes )

  def read( s, addr, nbytes ):
    nbytes = int(nbytes)
    nbits = nbytes << 3
    ret, shamt = Bits( nbits, 0 ), Bits( nbits, 0 )
    addr = int(addr)
    end  = addr + nbytes
    for j in xrange( addr, end ):
      ret += Bits( nbits, s.mem[j] ) << shamt
      shamt += Bits4(8)
    return ret

  def write( s, addr, nbytes, data ):
    tmp  = int(data)
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in xrange( addr, end ):
      s.mem[j] = tmp & 255
      tmp >>= 8

  def amo( s, amo, addr, nbytes, data ):
    ret = s.read( addr, nbytes )
    s.write( addr, nbytes, AMO_FUNS[ int(amo) ]( ret, data ) )
    return ret

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]

  def write_mem( s, addr, data ):
    assert len(s.mem) > (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  def __getitem__( s, idx ):
    return s.mem[ idx ]

  def __setitem__( s, idx, data ):
    s.mem[ idx ] = data

class TestMemoryCL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)], latency=1, mem_nbytes=2**20 ):

    # Local constants

    s.nports = nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]

    s.mem = TestMemory( mem_nbytes )

    # Interface

    s.recv = [ NonBlockingCalleeIfc() for i in range(nports) ]
    s.send = [ NonBlockingCallerIfc() for i in range(nports) ]

    # Queues

    s.req_qs = [ DelayPipeDeqCL( latency )( enq = s.recv[i] ) for i in range(nports) ]

    @s.update
    def up_mem():

      for i in range(s.nports):

        if s.req_qs[i].deq.rdy() and s.send[i].rdy():

          # Dequeue memory request message

          req = s.req_qs[i].deq()
          len_ = int(req.len)
          if not len_: len_ = req_classes[i].field_nbits( 'data' ) >> 3

          if   req.type_ == MemMsgType.READ:
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                    s.mem.read( req.addr, len_ ) )

          elif req.type_ == MemMsgType.WRITE:
            s.mem.write( req.addr, len_, req.data )
            # FIXME do we really set len=0 in response when doing subword wr?
            # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0 )
            resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0 )

          else: # AMOS
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
               s.mem.amo( req.type_, req.addr, len_, req.data ) )

          s.send[i]( resp )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "|".join( [ x.line_trace() for x in s.req_qs ] )

#=========================================================================
# TestMemory
#=========================================================================
# A behavioral Test Memory which is parameterized based on the number of
# memory request/response ports. This version is a little different from
# the one in pclib because we actually use the memory messages correctly
# in the interface.
#
# Author : Shunning Jiang
# Date   : Mar 12, 2018

from builtins import range
from builtins import object
from pymtl       import *
from collections import deque

# BRGTC2 custom MemMsg modified for RISC-V 32

from pclib.ifcs import mk_mem_msg

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
#         read_data = Bits( s.data_nbits )
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

TYPE_READ       = 0
TYPE_WRITE      = 1
# write no-refill
TYPE_WRITE_INIT = 2
TYPE_AMO_ADD    = 3
TYPE_AMO_AND    = 4
TYPE_AMO_OR     = 5
TYPE_AMO_SWAP   = 6
TYPE_AMO_MIN    = 7
TYPE_AMO_MINU   = 8
TYPE_AMO_MAX    = 9
TYPE_AMO_MAXU   = 10
TYPE_AMO_XOR    = 11

AMO_FUNS = { TYPE_AMO_ADD  : lambda m,a : m+a,
             TYPE_AMO_AND  : lambda m,a : m&a,
             TYPE_AMO_OR   : lambda m,a : m|a,
             TYPE_AMO_SWAP : lambda m,a : a,
             TYPE_AMO_MIN  : lambda m,a : m if m.int() < a.int() else a,
             TYPE_AMO_MINU : min,
             TYPE_AMO_MAX  : lambda m,a : m if m.int() > a.int() else a,
             TYPE_AMO_MAXU : max,
             TYPE_AMO_XOR  : lambda m,a : m^a,
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
    for j in range( addr, end ):
      ret += Bits( nbits, s.mem[j] ) << shamt
      shamt += 8
    return ret

  def write( s, addr, nbytes, data ):
    tmp  = int(data)
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in range( addr, end ):
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

class TwoPortTestMemoryCL( ComponentLevel6 ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual method

  def req0_( s, msg ):
    s.req_qs[0].appendleft( msg )

  def req0_rdy_( s ):
    return len(s.req_qs[0]) < s.req_qs[0].maxlen

  def resp0_( s ):
    return s.resp_qs[0].pop()

  def resp0_rdy_( s ):
    return len(s.resp_qs[0]) > 0

  def req1_( s, msg ):
    s.req_qs[1].appendleft( msg )

  def req1_rdy_( s ):
    return len(s.req_qs[1]) < s.req_qs[1].maxlen

  def resp1_( s ):
    return s.resp_qs[1].pop()

  def resp1_rdy_( s ):
    return len(s.resp_qs[1]) > 0

  # Actual stuff
  def construct( s, mem_ifc_dtypes=mk_mem_msg(8,32,32), mem_nbytes=2**20 ):
    req_class, resp_class = mem_ifc_dtypes

    s.mem = TestMemory( mem_nbytes )

    # Interface

    s.req0      = CalleePort( s.req0_ )
    s.req0_rdy  = CalleePort( s.req0_rdy_ )
    s.resp0     = CalleePort( s.resp0_ )
    s.resp0_rdy = CalleePort( s.resp0_rdy_ )

    s.req1      = CalleePort( s.req1_ )
    s.req1_rdy  = CalleePort( s.req1_rdy_ )
    s.resp1     = CalleePort( s.resp1_ )
    s.resp1_rdy = CalleePort( s.resp1_rdy_ )

    # Queues

    s.req_qs  = [ deque(maxlen=3) for i in range(2) ]
    s.resp_qs = [ deque(maxlen=3) for i in range(2) ]

    # Local constants

    s.nports = 2

    @s.update
    def up_mem():

      for i in range(s.nports):

        if s.req_qs[i] and len(s.resp_qs[i]) < s.resp_qs[i].maxlen:

          # Dequeue memory request message
          req = s.req_qs[i].pop()
          len_ = int(req.len_)
          if not len_: len_ = 4

          if   req.type_ == resp_class.TYPE_READ:
            resp = resp_class( resp_class.TYPE_READ,
                               req.opaque, 0, req.len_,
                               s.mem.read( req.addr, len_ ) )

          elif req.type_ == resp_class.TYPE_WRITE:
            s.mem.write( req.addr, len_, req.data )
            resp = resp_class( resp_class.TYPE_WRITE,
                               req.opaque, 0, req.len_,
                               0 )

          else: # AMOS
            s.mem.write( req.type, req.addr, len_, req.data )
            resp = resp_class( req.type, req.opaque, 0, req.len_,
               s.mem.amo( req.type_, req.addr, len_, req.data ) )

          s.resp_qs[i].appendleft( resp )

    s.add_constraints(
      U(up_mem) < M(s.req0_)    , # execute mem block before receiving request
      U(up_mem) < M(s.req0_rdy_), # for pipe behavior
      U(up_mem) < M(s.req1_)    ,
      U(up_mem) < M(s.req1_rdy_),

      M(s.resp0_)     < U(up_mem), # execute resp before mem block for
      M(s.resp0_rdy_) < U(up_mem), # pipe behavior
      M(s.resp1_)     < U(up_mem),
      M(s.resp1_rdy_) < U(up_mem),
    )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return ""

    #  trace_str = ""
    #  for req, resp_q, resp in zip( s.reqs, s.resps_q, s.resps ):
      #  trace_str += "{}({}){} ".format( req, resp_q, resp )

    #  return trace_str


"""
==========================================================================
ChecksumXcelFL.py
==========================================================================
Functional level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from examples.ex02_cksum.ChecksumFL import checksum
from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMinionIfcFL


# Address space: 0~3: checksum input, 4: go bit, 5: result
class ChecksumXcelFL( Component ):

  def construct( s ):

    # Interface

    ReqType, RespType = mk_xcel_msg( 5, 32 )

    s.xcel = XcelMinionIfcFL( read=s.read, write=s.write )

    # Components

    s.reg_file = [ b32(0) for _ in range(6) ]

    s.trace = "            "
    @update
    def up_clear_trace():
      s.trace = "            "

    s.add_constraints( U(up_clear_trace) < M(s.read) )
    s.add_constraints( U(up_clear_trace) < M(s.write) )

  def read( s, addr ):
    s.trace = "fl:<rd xr{:02}>".format(int(addr))
    return s.reg_file[ int(addr) ]

  def write( s, addr, data ):
    s.trace = "fl:<wr xr{:02}>".format(int(addr))
    s.reg_file[ int(addr) ] = b32(data)

    # If go bit is written
    if s.reg_file[4]:
      words = []
      for i in range( 4 ):
        words.append( s.reg_file[i][0 :16] )
        words.append( s.reg_file[i][16:32] )
      s.reg_file[5] = checksum( words )

  def line_trace( s ):
    return s.trace

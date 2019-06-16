"""
==========================================================================
ChecksumXcelFL.py
==========================================================================
Functional level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMinionIfcFL
from examples.ex02_cksum.ChecksumFL import checksum


# Address space: 0~3: checksum input, 4: go bit, 5: result
class ChecksumXcelFL( Component ):

  def construct( s ):

    # Interface

    ReqType, RespType = mk_xcel_msg( 3, 32 )

    s.xcel = XcelMinionIfcFL( ReqType, RespType, 
                              read=s.read, write=s.write)

    # Components

    s.reg_file = [ b32(0) for _ in range(6) ]
  
  def read( s, addr ):
    return s.reg_file[ int(addr) ]

  def write( s, addr, data ):
    s.reg_file[ int(addr) ] = b32(data)

    # If go bit is written
    if s.reg_file[4]:
      words = []
      for i in range( 4 ):
        words.append( s.reg_file[i][0 :16] )
        words.append( s.reg_file[i][16:32] )
      s.reg_file[5] = checksum( words )

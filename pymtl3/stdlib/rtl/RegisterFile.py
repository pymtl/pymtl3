
from copy import deepcopy
from typing import TypeVar, Generic

from pymtl3 import *
from pymtl3.dsl import Const


T_RFDpath = TypeVar('T_RFDpath')
T_RFAddr  = TypeVar('T_RFAddr ')

class RegisterFile( Component, Generic[T_RFDpath, T_RFAddr] ):

  def construct( s, nregs=32, rd_ports=1, wr_ports=1,
                const_zero=False ):

    addr_type = mk_bits( clog2( nregs ) )

    s.raddr = [ InPort[T_RFAddr]() for i in range( rd_ports ) ]
    s.rdata = [ OutPort[T_RFDpath]() for i in range( rd_ports ) ]

    s.waddr = [ InPort[T_RFAddr]() for i in range( wr_ports ) ]
    s.wdata = [ InPort[T_RFDpath]() for i in range( wr_ports ) ]
    s.wen   = [ InPort[Bits1]() for i in range( wr_ports ) ]

    s.regs      = [ Wire[T_RFDpath]() for i in range(nregs) ]
    s.next_regs = [ Wire[T_RFDpath]() for i in range(nregs) ]

    @s.update_on_edge
    def up_rfile():
      for i in range( nregs ):
        s.regs[i] = s.next_regs[i]

    @s.update
    def up_rf_read():
      for i in range( rd_ports ):
        s.rdata[i] = s.regs[ s.raddr[i] ]

    if const_zero:
      @s.update
      def up_rf_write_constzero():
        for i in range( nregs ):
          s.next_regs[i] = deepcopy( s.regs[i] )
        for i in range( wr_ports ):
          if s.wen[i] & (s.waddr[i] != Const[T_RFAddr](0)):
            s.next_regs[ s.waddr[i] ] = deepcopy( s.wdata[i] )

    else:
      @s.update
      def up_rf_write():
        for i in range( nregs ):
          s.next_regs[i] = deepcopy( s.regs[i] )
        for i in range( wr_ports ):
          if s.wen[i]:
            s.next_regs[ s.waddr[i] ] = deepcopy( s.wdata[i] )

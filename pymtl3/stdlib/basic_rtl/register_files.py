from pymtl3 import *

from typing import *


T_RF = TypeVar("T_RF", bound=HWDataType)
class RegisterFile( Component, Generic[T_RF] ):

  def construct( s, Type: Type[T_RF], nregs:int=32, rd_ports:int=1, wr_ports:int=1,
                 const_zero:int=False ) -> None:

    addr_type = mk_bits( clog2( nregs ) )

    s.raddr = [ InPort( addr_type ) for i in range( rd_ports ) ]
    s.rdata = [ OutPort( Type ) for i in range( rd_ports ) ]

    s.waddr = [ InPort( addr_type ) for i in range( wr_ports ) ]
    s.wdata = [ InPort( Type ) for i in range( wr_ports ) ]
    s.wen   = [ InPort( Bits1 ) for i in range( wr_ports ) ]

    s.regs = [ Wire( Type ) for i in range(nregs) ]

    @update
    def up_rf_read():
      for i in range( rd_ports ):
        s.rdata[i] @= s.regs[ s.raddr[i] ]

    if const_zero:
      @update_ff
      def up_rf_write_constzero():
        for i in range( wr_ports ):
          if s.wen[i] & (s.waddr[i] != 0):
            s.regs[ s.waddr[i] ] <<= s.wdata[i]
    else:
      @update_ff
      def up_rf_write():
        for i in range( wr_ports ):
          if s.wen[i]:
            s.regs[ s.waddr[i] ] <<= s.wdata[i]

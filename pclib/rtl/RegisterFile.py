from pymtl import *

class RegisterFile( RTLComponent ):

  def __init__( s, Type, nregs=32, rd_ports=1, wr_ports=1,
                const_zero=False ):

    addr_type = mk_bits( clog2( nregs ) )

    s.raddr = [ InVPort( addr_type ) for i in xrange( rd_ports ) ]
    s.rdata = [ OutVPort( Type ) for i in xrange( rd_ports ) ]

    s.waddr = [ InVPort( addr_type ) for i in xrange( wr_ports ) ]
    s.wdata = [ InVPort( Type ) for i in xrange( wr_ports ) ]
    s.wen   = [ InVPort( Bits1 ) for i in xrange( wr_ports ) ]

    s.regs      = [ Wire( Type ) for i in xrange(nregs) ]
    s.next_regs = [ Wire( Type ) for i in xrange(nregs) ]

    @s.update_on_edge
    def up_rfile():
      for i in xrange( nregs ):
        s.regs[i] = s.next_regs[i]

    @s.update
    def up_rf_read():
      for i in xrange( rd_ports ):
        s.rdata[i] = s.regs[ s.raddr[i] ]

    if const_zero:
      @s.update
      def up_rf_write_constzero():
        for i in xrange( wr_ports ):
          if s.wen[i] & (s.waddr[i] != addr_type(0)):
            s.next_regs[ s.waddr[i] ] = s.wdata[i]

    else:
      @s.update
      def up_rf_write():
        for i in xrange( wr_ports ):
          if s.wen[i]:
            s.next_regs[ s.waddr[i] ] = s.wdata[i]

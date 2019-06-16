from __future__ import absolute_import, division, print_function

from copy import deepcopy

from pymtl3 import *


class RegisterFile( Component ):

  def construct( s, Type, nregs=32, rd_ports=1, wr_ports=1,
                const_zero=False ):

    addr_type = mk_bits( clog2( nregs ) )

    s.raddr = [ InPort( addr_type ) for i in xrange( rd_ports ) ]
    s.rdata = [ OutPort( Type ) for i in xrange( rd_ports ) ]

    s.waddr = [ InPort( addr_type ) for i in xrange( wr_ports ) ]
    s.wdata = [ InPort( Type ) for i in xrange( wr_ports ) ]
    s.wen   = [ InPort( Bits1 ) for i in xrange( wr_ports ) ]

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
        for i in xrange( nregs ):
          s.next_regs[i] = deepcopy( s.regs[i] )
        for i in xrange( wr_ports ):
          if s.wen[i] & (s.waddr[i] != addr_type(0)):
            s.next_regs[ s.waddr[i] ] = deepcopy( s.wdata[i] )

    else:
      @s.update
      def up_rf_write():
        for i in xrange( nregs ):
          s.next_regs[i] = deepcopy( s.regs[i] )
        for i in xrange( wr_ports ):
          if s.wen[i]:
            s.next_regs[ s.waddr[i] ] = deepcopy( s.wdata[i] )

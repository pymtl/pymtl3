"""
========================================================================
ROMRTL.py
========================================================================
Multiported ROM

Author : Shunning Jiang
Date   : June 18, 2020
"""

from pymtl3 import *


class SRAM1rwRTL( Component ):

  def construct( s, nbits, num_entries ):

    # port 0
    s.ren   = InPort()
    s.wen   = InPort()
    s.rdata = OutPort( nbits )
    s.wdata = InPort( nbits )
    s.addr  = InPort( clog2(num_entries) )

    s.mem = [ Wire(nbits) for _ in range(num_entries) ]

    # output

    # wen overrides ren

    @update_ff
    def up_1rw():
      s.rdata <<= 0

      if s.wen:
        s.mem[ s.addr ] <<= s.wdata
      elif s.ren:
        s.rdata <<= s.mem[ s.addr ]

  def line_trace( s ):
    return f"[{s.addr}] ren={s.ren} wen={s.wen} rdata={s.rdata} wdata={s.wdata}"

class SRAM1r1wRTL( Component ):

  def construct( s, nbits, num_entries ):

    # port 0
    s.ren   = InPort()
    s.rdata = OutPort( nbits )
    s.raddr = InPort( clog2(num_entries) )

    # port 1
    s.wen   = InPort()
    s.wdata = InPort( nbits )
    s.waddr = InPort( clog2(num_entries) )

    s.mem = [ Wire(nbits) for _ in range(num_entries) ]

    @update_ff
    def up_1r1w():

      if s.ren:
        s.rdata <<= s.mem[ s.raddr ]
      else:
        s.rdata <<= 0

      if s.wen:
        s.mem[ s.waddr ] <<= s.wdata

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return f"ren={s.ren} [{s.raddr}] rdata={s.rdata} wen={s.wen} [{s.waddr}] wdata={s.wdata}"

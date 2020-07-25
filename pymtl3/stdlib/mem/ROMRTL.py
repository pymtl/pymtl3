"""
========================================================================
ROMRTL.py
========================================================================
Multiported ROM

Author : Shunning Jiang
Date   : June 18, 2020
"""

from pymtl3 import *


class CombinationalROMRTL( Component ):

  def construct( s, Type, num_entries, data, num_ports=1 ):
    assert len(data) == num_entries

    s.raddr = [ InPort( clog2(num_entries) ) for _ in range(num_ports) ]
    s.rdata = [ OutPort( Type )              for _ in range(num_ports) ]

    s.mem = [ Wire(Type) for _ in range(num_entries) ]
    for i in range(num_entries):
      s.mem[i] //= data[i]

    @update
    def up_read_rom():
      for i in range(num_ports):
        s.rdata[i] @= s.mem[ s.raddr[i] ]

class SequentialROMRTL( Component ):

  def construct( s, Type, num_entries, data, num_ports=1 ):
    assert len(data) == num_entries

    s.raddr = [ InPort( clog2(num_entries) ) for _ in range(num_ports) ]
    s.rdata = [ OutPort( Type )              for _ in range(num_ports) ]

    s.mem = [ Wire(Type) for _ in range(num_entries) ]
    for i in range(num_entries):
      s.mem[i] //= data[i]

    @update_ff
    def up_read_rom():
      for i in range(num_ports):
        s.rdata[i] <<= s.mem[ s.raddr[i] ]
  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "|".join( [ f"[{s.raddr[i]}]->{s.rdata[i]}" for i in range(len(s.raddr)) ] )

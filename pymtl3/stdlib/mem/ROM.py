"""
========================================================================
ROM.py
========================================================================
LUT-based ROM

Author : Shunning Jiang
Date   : June 18, 2020
"""

from pymtl3 import *
from pymtl3.extra.pypy import custom_exec

class ROM( Component ):

  def construct( s, Type, num_entries, data ):
    assert len(data) == num_entries

    s.addr = InPort( clog2(num_entries) )
    s.out  = OutPort( Type )

    # @update
    # def up_read_rom():
    #   if   s.addr == 0: s.out @= 8
    #   elif s.addr == 1: s.out @= 7
    #   elif s.addr == 2: s.out @= 6
    #   elif s.addr == 3: s.out @= 5
    #   elif s.addr == 4: s.out @= 4
    #   elif s.addr == 5: s.out @= 3
    #   elif s.addr == 6: s.out @= 2
    #   elif s.addr == 7: s.out @= 1
    #   else: s.out @= 0

    import py
    strs = '\n      elif '.join( [ f's.addr == {i}: s.out @= {x}' for i, x in enumerate(data) ] )
    custom_exec( py.code.Source(f'''
    @update
    def up_rom_read():
      if {strs}
      else: s.out @= 0
    ''').compile(), {**globals(), **locals()} )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return f"[{s.addr}] >>> {s.out}"
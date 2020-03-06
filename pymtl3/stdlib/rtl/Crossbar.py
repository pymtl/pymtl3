"""
======================================================================
Crossbar.py
======================================================================
"""

from pymtl3 import *


class Crossbar( Component ):

  def construct( s, nports, dtype ):

    s.in_ = [ InPort  ( dtype )     for _ in range( nports ) ]
    s.out = [ OutPort ( dtype )     for _ in range( nports ) ]
    s.sel = [ InPort  ( clog2( nports ) ) for _ in range( nports ) ]

    @update
    def comb_logic():
      for i in range( nports ):
        s.out[i] @= s.in_[ s.sel[ i ] ]

  def line_trace( s ):
    in_str  = ' '.join( [ str(x) for x in s.in_ ] )
    sel_str = ' '.join( [ str(x) for x in s.sel ] )
    out_str = ' '.join( [ str(x) for x in s.out ] )
    return f"{in_str} ( {sel_str} ) {out_str}"

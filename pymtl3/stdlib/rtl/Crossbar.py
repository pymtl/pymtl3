"""
======================================================================
Crossbar.py
======================================================================
"""

from pymtl3 import *


class Crossbar( Component ):

  def construct( s, nports, dtype ):

    sel_nbits = clog2( nports )

    s.in_ = [ InPort  ( dtype )     for _ in range( nports ) ]
    s.out = [ OutPort ( dtype )     for _ in range( nports ) ]
    s.sel = [ InPort  ( mk_bits( sel_nbits ) ) for _ in range( nports ) ]

    @s.update
    def comb_logic():

      for i in range( nports ):
        s.out[i] = s.in_[ s.sel[ i ] ]

  def line_trace( s ):
    in_str  = ' '.join( [ str(x) for x in s.in_ ] )
    sel_str = ' '.join( [ str(x) for x in s.sel ] )
    out_str = ' '.join( [ str(x) for x in s.out ] )
    return '{} ( {} ) {}'.format( in_str, sel_str, out_str )

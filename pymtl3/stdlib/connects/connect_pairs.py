"""
==========================================================================
 connect_pairs.py
==========================================================================
Advanced connect functions for different patterns

 Author: Shunning
   Date: July 13, 2019
"""

from pymtl3 import *


def connect_pairs( *args ):

  if len(args) & 1 != 0:
     raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

  for i in range(len(args)>>1) :
    try:
      connect( args[ i<<1 ], args[ (i<<1)+1 ] )
    except Exception as e:
      args = list(e.args[::])
      args[0] = "[connect_pair] connecting {}-th argument to {}-th argument\n" \
                .format( i<<1, (i<<1)+1 ) + \
                "--------------------\n" + args[0]
      e.args = tuple(args)
      raise

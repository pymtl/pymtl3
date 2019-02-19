#=========================================================================
# Helpers.py
#=========================================================================
# This file includes the helper functions that are common to more than
# one passes.
# 
# Author : Peitian Pan
# Date   : Feb 13, 2019

def freeze( obj ):
  """Convert potentially mutable objects into immutable objects."""
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj

def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '

  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

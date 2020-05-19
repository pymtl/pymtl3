#=========================================================================
# MetadataKey.py
#=========================================================================
# Provides MetadataKey class.
#
# Author : Peitian Pan
# Date   : Mar 16, 2020

class MetadataKey:
  def __init__( self, T=None ):
    assert T is None or isinstance( T, type ), f"The given parameter {T} is not a type."
    self.type = T

  def check_value( self, value ):
    if self.type is not None and not isinstance( value, self.type ):
      raise TypeError( f"Value {value} is of type {type(value)} and cannot be assigned "
                       f"to this MetadataKey that enforces type {self.type}." )

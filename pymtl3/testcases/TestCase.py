"""
=========================================================================
TestCase.py
=========================================================================
Implement the base TestCase class.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from pymtl3 import Component


class AliasOf:
  def __init__( s, alias_name = 'A' ):
    s.alias_name = alias_name

  def __get__( s, instance, owner ):
    return getattr( owner, s.alias_name )

  def __set__( s, instance, value ):
    s.alias_name = value

class TestCase:
  DUT    = AliasOf( 'A' )
  TV_IN  = AliasOf( 'tv_in' )
  TV_OUT = AliasOf( 'tv_out' )
  TV     = AliasOf( 'test_vector' )

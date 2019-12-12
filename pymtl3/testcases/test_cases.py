"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from pymtl3 import *

from .TestCase import TestCase

#-------------------------------------------------------------------------
# Commonly used BitStructs
#-------------------------------------------------------------------------

@bitstruct
class Bits32Foo:
  foo: Bits32

@bitstruct
class Bits32x5Foo:
  foo: [ Bits32 ] * 5

#-------------------------------------------------------------------------
# Test Components
#-------------------------------------------------------------------------

class CaseBits32PortOnly( TestCase ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )

class CaseStructPortOnly( TestCase ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )

class CasePackedArrayStructPortOnly( TestCase ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )

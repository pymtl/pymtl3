
from copy import deepcopy
from typing import Generic, TypeVar

from pymtl3 import *


T_RegDataType = TypeVar("T_RegDataType")

class Reg( Component, Generic[T_RegDataType] ):

  def construct( s ):
    s.out = OutPort[T_RegDataType]()
    s.in_ = InPort[T_RegDataType]()

    @s.update_on_edge
    def up_reg():
      # s.out = Type( s.in_ )
      s.out = s.in_

  def line_trace( s ):
    return "[{} > {}]".format(s.in_, s.out)

T_RegEnDataType = TypeVar("T_RegEnDataType")

class RegEn( Component, Generic[T_RegEnDataType] ):

  def construct( s ):
    s.out = OutPort[T_RegEnDataType]()
    s.in_ = InPort[T_RegEnDataType]()

    # s.en  = InPort( int if Type is int else Bits1 )
    s.en  = InPort[Bits1]()

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = deepcopy( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

class RegRst( Component ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    s.reset = InPort( int if Type is int else Bits1 )

    @s.update_on_edge
    def up_regrst():
      if s.reset: s.out = Type( reset_value )
      else:       s.out = s.in_

  def line_trace( s ):
    return "[rst:{}|{} > {}]".format(s.rst, s.in_, s.out)

class RegEnRst( Component ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    s.reset = InPort( int if Type is int else Bits1 )
    s.en    = InPort( int if Type is int else Bits1 )

    @s.update_on_edge
    def up_regenrst():
      if s.reset: s.out = Type( reset_value )
      elif s.en:  s.out = deepcopy( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

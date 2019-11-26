
from copy import deepcopy
from typing import Generic, TypeVar

from pymtl3 import *
from pymtl3.dsl import Const


T_RegDataType = TypeVar("T_RegDataType")

class Reg( Component, Generic[T_RegDataType] ):

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type ):
  #   s.in_ = InPort[T_RegDataType](Type)
  #   s.out = OutPort[T_RegDataType](Type)

  # def reg_upblk( s ):
  #   s.out = s.in_

  # def c_tick( s ):
  #   s.reg_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

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

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type ):
  #   s.in_ = InPort[T_RegEnDataType](Type)
  #   s.out = OutPort[T_RegEnDataType](Type)
  #   s.en = InPort[Bits1](Bits1)

  # def regen_upblk( s ):
  #   if s.en:
  #     s.out = deepcopy( s.in_ )

  # def c_tick( s ):
  #   s.regen_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

  def construct( s ):
    s.out = OutPort[T_RegEnDataType]()
    s.in_ = InPort[T_RegEnDataType]()
    s.en  = InPort[Bits1]()

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = deepcopy( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

T_RegRstDataType = TypeVar("T_RegRstDataType")

class RegRst( Component, Generic[T_RegRstDataType] ):

  def construct( s, reset_value=0 ):
    s.out = OutPort[T_RegRstDataType]()
    s.in_ = InPort [T_RegRstDataType]()

    s.reset = InPort[Bits1]()

    @s.update_on_edge
    def up_regrst():
      if s.reset: s.out = Const[T_RegRstDataType]( reset_value )
      else:       s.out = s.in_

  def line_trace( s ):
    return "[rst:{}|{} > {}]".format(s.rst, s.in_, s.out)

T_RegEnRstDataType = TypeVar("T_RegEnRstDataType")

class RegEnRst( Component, Generic[T_RegEnRstDataType] ):

  def construct( s, reset_value=0 ):
    s.out = OutPort[T_RegEnRstDataType]()
    s.in_ = InPort [T_RegEnRstDataType]()

    s.reset = InPort[Bits1]()
    s.en    = InPort[Bits1]()

    @s.update_on_edge
    def up_regenrst():
      if s.reset: s.out = Const[T_RegEnRstDataType]( reset_value )
      elif s.en:  s.out = deepcopy( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

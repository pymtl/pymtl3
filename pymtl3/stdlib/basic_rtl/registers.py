from pymtl3 import *
from pymtl3.dsl import Const
from typing import Generic, TypeVar


T_RegDataType = TypeVar("T_RegDataType")

class Reg( Component, Generic[T_RegDataType] ):

  def construct( s ):
    s.out = OutPort[T_RegDataType]()
    s.in_ = InPort[T_RegDataType]()

    @update_ff
    def up_reg():
      s.out <<= s.in_

  def line_trace( s ):
    return f"[{s.in_} > {s.out}]"


T_RegEnDataType = TypeVar("T_RegEnDataType")

class RegEn( Component, Generic[T_RegEnDataType] ):

  def construct( s ):
    s.out = OutPort[T_RegEnDataType]()
    s.in_ = InPort[T_RegEnDataType]()

    s.en  = InPort[Bits1]()

    @update_ff
    def up_regen():
      if s.en:
        s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

T_RegRstDataType = TypeVar("T_RegRstDataType")

class RegRst( Component, Generic[T_RegRstDataType] ):

  def construct( s, reset_value=0 ):
    s.out = OutPort[T_RegRstDataType]()
    s.in_ = InPort[T_RegRstDataType]()

    s.reset = InPort[Bits1]()

    @update_ff
    def up_regrst():
      if s.reset: s.out <<= T_RegRstDataType( reset_value )
      else:       s.out <<= s.in_

  def line_trace( s ):
    return f"[{'rst' if s.reset else '   '}|{s.in_} > {s.out}]"

T_RegEnRstDataType = TypeVar("T_RegEnRstDataType")

class RegEnRst( Component, Generic[T_RegEnRstDataType] ):

  def construct( s, reset_value=0 ):
    s.out = OutPort[T_RegEnRstDataType]()
    s.in_ = InPort[T_RegEnRstDataType]()

    s.en    = InPort[Bits1]()
    s.reset = InPort[Bits1]()

    @update_ff
    def up_regenrst():
      if s.reset: s.out <<= T_RegEnRstDataType( reset_value )
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

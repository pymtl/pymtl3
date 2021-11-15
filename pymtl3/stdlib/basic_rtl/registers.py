from pymtl3 import *

from typing import *


T_Reg = TypeVar("T_Reg", bound=HWDataType)
class Reg( Component, Generic[T_Reg] ):

  def construct( s, Width: Type[T_Reg] ) -> None:
    s.out = OutPort( Width )
    s.in_ = InPort( Width )

    @update_ff
    def up_reg():
      s.out <<= s.in_

  def line_trace( s ):
    return f"[{s.in_} > {s.out}]"

T_RegEn = TypeVar("T_RegEn", bound=HWDataType)
class RegEn( Component, Generic[T_RegEn] ):

  def construct( s, Width: Type[T_RegEn] ) -> None:
    s.out = OutPort( Width )
    s.in_ = InPort( Width )

    s.en  = InPort()

    @update_ff
    def up_regen():
      if s.en:
        s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

T_RegRst = TypeVar("T_RegRst", bound=HWDataType)
class RegRst( Component, Generic[T_RegRst] ):

  def construct( s, Width: Type[T_RegRst], reset_value:int=0 ) -> None:
    s.out = OutPort( Width )
    s.in_ = InPort( Width )

    @update_ff
    def up_regrst():
      if s.reset: s.out <<= reset_value
      else:       s.out <<= s.in_

  def line_trace( s ):
    return f"[{'rst' if s.reset else '   '}|{s.in_} > {s.out}]"

T_RegEnRst = TypeVar("T_RegEnRst", bound=HWDataType)
class RegEnRst( Component, Generic[T_RegEnRst] ):

  def construct( s, Width: Type[T_RegEnRst], reset_value:int=0 ) -> None:
    s.out = OutPort( Width )
    s.in_ = InPort( Width )

    s.en  = InPort()

    @update_ff
    def up_regenrst():
      if s.reset: s.out <<= reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

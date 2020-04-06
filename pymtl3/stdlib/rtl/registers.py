from pymtl3 import *


class Reg( Component ):

  def construct( s, Type ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    @update_ff
    def up_reg():
      s.out <<= s.in_

  def line_trace( s ):
    return f"[{s.in_} > {s.out}]"

class RegEn( Component ):

  def construct( s, Type ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    s.en  = InPort()

    @update_ff
    def up_regen():
      if s.en:
        s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

class RegRst( Component ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    @update_ff
    def up_regrst():
      if s.reset: s.out <<= reset_value
      else:       s.out <<= s.in_

  def line_trace( s ):
    return f"[{'rst' if s.reset else '   '}|{s.in_} > {s.out}]"

class RegEnRst( Component ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    s.en    = InPort()

    @update_ff
    def up_regenrst():
      if s.reset: s.out <<= reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

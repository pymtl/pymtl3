from pymtl import *

# Register

class Reg(Updates):

  def __init__( s, type_ ):
    s.in_ = ValuePort( type_ )
    s.out = ValuePort( type_ )

    @s.update_on_edge
    def up_reg():
      s.out = s.in_

  def line_trace( s ):
    return "[%8x > %8x]" % (s.in_, s.out)

# Register with enable signal

class RegEn(Updates):

  def __init__( s, type_ ):
    s.in_ = ValuePort( type_ )
    s.out = ValuePort( type_ )
    s.en  = ValuePort( type_ )

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = s.in_

  def line_trace( s ):
    return "[en:%1d|%8x > %8x]" % (s.en, s.in_, s.out)

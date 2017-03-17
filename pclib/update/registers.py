from pymtl import *

# Register

class Reg(Updates):

  def __init__( s, nbits = 32 ):
    s.in_ = ValuePort(int)
    s.out = ValuePort(int)

    @s.update_on_edge
    def up_reg():
      s.out = s.in_

  def line_trace( s ):
    return "[%6d > %6d]" % (s.in_, s.out)

# Register with enable signal

class RegEn(Updates):

  def __init__( s, nbits = 32 ):
    s.in_ = ValuePort(int)
    s.out = ValuePort(int)
    s.en  = ValuePort(int)

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = s.in_

  def line_trace( s ):
    return "[en:%1d|%6d > %6d]" % (s.en, s.in_, s.out)

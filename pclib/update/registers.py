from pymtl import *

# Register

class Reg(UpdatesImpl):

  def __init__( s ):
    s.in_ = 0
    s.out = 0

    @s.update_on_edge
    def up_reg():
      s.out = s.in_

  def line_trace( s ):
    return "[%4d > %4d]" % (s.in_, s.out)

# Register with enable signal

class RegEn(UpdatesImpl):

  def __init__( s ):
    s.in_ = 0
    s.out = 0
    s.en  = 0

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = s.in_

  def line_trace( s ):
    return "[en:%4d|%4d > %4d]" % (s.en, s.in_, s.out)

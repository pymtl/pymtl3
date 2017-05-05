from pymtl import *

# Register

class Reg( UpdatesCall ):

  def __init__( s, Type ):
    s.in_ = ValuePort( Type )
    s.out = ValuePort( Type )

    @s.update_on_edge
    def up_reg():
      s.out = s.in_

  def line_trace( s ):
    return "[{} > {}]".format(s.in_, s.out)

# Register with enable signal

class RegEn( UpdatesCall ):

  def __init__( s, Type ):
    s.in_ = ValuePort( Type )
    s.out = ValuePort( Type )
    s.en  = ValuePort( Type )

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = s.in_

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

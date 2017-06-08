from pymtl import *

# Register

class Reg( UpdateVarNet ):

  def __init__( s, Type ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    @s.update_on_edge
    def up_reg():
      s.out = s.in_

  def line_trace( s ):
    return "[{} > {}]".format(s.in_, s.out)

  def __int__( s ):
    return int(s.out)

# Register with enable signal

class RegEn( UpdateVarNet ):

  def __init__( s, Type ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )
    s.en  = InVPort( int if Type == int else Bits1 )

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = s.in_

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

from pymtl import *

class Reg( RTLComponent ):

  def construct( s, Type ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    @s.update_on_edge
    def up_reg():
      s.out = Type( s.in_ )

  def line_trace( s ):
    return "[{} > {}]".format(s.in_, s.out)

class RegEn( RTLComponent ):

  def construct( s, Type ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    s.en  = InVPort( int if Type is int else Bits1 )

    @s.update_on_edge
    def up_regen():
      if s.en:
        s.out = Type( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

class RegRst( RTLComponent ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    s.reset = InVPort( int if Type is int else Bits1 )

    @s.update_on_edge
    def up_regrst():
      if s.reset: s.out = Type( reset_value )
      else:       s.out = Type( s.in_ )

  def line_trace( s ):
    return "[rst:{}|{} > {}]".format(s.rst, s.in_, s.out)

class RegEnRst( RTLComponent ):

  def construct( s, Type, reset_value=0 ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    s.reset = InVPort( int if Type is int else Bits1 )
    s.en    = InVPort( int if Type is int else Bits1 )

    @s.update_on_edge
    def up_regenrst():
      if s.reset: s.out = Type( reset_value )
      elif s.en:  s.out = Type( s.in_ )

  def line_trace( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

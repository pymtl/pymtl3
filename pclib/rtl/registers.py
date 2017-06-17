from pymtl import *

# Register with parametrizable types

class Reg( UpdateVarNet ):

  def __init__( s, Type, en=False, rst=False, reset_value=None ):
    s.out = OutVPort( Type )
    s.in_ = InVPort( Type )

    if en:
      s.en  = InVPort( int if Type == int else Bits1 )

    if rst:
      s.rst = InVPort( int if Type == int else Bits1 )
      s.reset_value = reset_value

    if not en and not rst: # Normal Reg
      s.line_trace = s.line_trace_normal

      @s.update_on_edge
      def up_reg():
        s.out = s.in_

    if not en and rst: # RegRst
      s.line_trace = s.line_trace_rst

      @s.update_on_edge
      def up_regrst():
        if s.rst: s.out = reset_value
        else:     s.out = s.in_

    if en and not rst: # RegEn
      s.line_trace = s.line_trace_en

      @s.update_on_edge
      def up_regen():
        if s.en:  s.out = s.in_

    if en and rst: # RegEn
      s.line_trace = s.line_trace_enrst

      @s.update_on_edge
      def up_regenrst():
        if   s.rst: s.out = reset_value
        elif s.en:  s.out = s.in_

  def line_trace_normal( s ):
    return "[{} > {}]".format(s.in_, s.out)

  def line_trace_en( s ):
    return "[en:{}|{} > {}]".format(s.en, s.in_, s.out)

  def line_trace_rst( s ):
    return "[rst:{}|{} > {}]".format(s.rst, s.in_, s.out)

  def line_trace_enrst( s ):
    return "[en:{}|rst:{}|{} > {}]".format(s.en, s.rst, s.in_, s.out)

#=========================================================================
# YosysBehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L3 behavioral translator."""

from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.translation.behavioral.VBehavioralTranslatorL3 import (
    BehavioralRTLIRToVVisitorL3,
    VBehavioralTranslatorL3,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

from .YosysBehavioralTranslatorL2 import (
    YosysBehavioralRTLIRToVVisitorL2,
    YosysBehavioralTranslatorL2,
)


class YosysBehavioralTranslatorL3(
    YosysBehavioralTranslatorL2, VBehavioralTranslatorL3 ):

  def _get_rtlir2v_visitor( s ):
    return YosysBehavioralRTLIRToVVisitorL3

class YosysBehavioralRTLIRToVVisitorL3(
    YosysBehavioralRTLIRToVVisitorL2, BehavioralRTLIRToVVisitorL3 ):
  """IR visitor that generates yosys-compatible SystemVerilog code.

  This visitor differs from the canonical SystemVerilog visitor in that
  it name-mangles each struct signal into multiple signals for all fields
  in the struct. We don't use SystemVerilog struct here because yosys
  does not support that yet.
  """

  def _literal_number( s, nbits, value ):
    value = int( value )
    return f"{nbits}'d{value}"

  def _struct_instance( s, dtype, struct ):
    def _gen_packed_array( dtype, n_dim, array ):
      if not n_dim:
        if isinstance( dtype, rdt.Vector ):
          return s._literal_number( dtype.nbits, array )
        elif isinstance( dtype, rdt.Struct ):
          return s._struct_instance( dtype, array )
        else:
          assert False, f"unrecognized data type {Type}!"
      else:
        ret = []
        for i in reversed( range( n_dim[0]) ):
          ret.append( _gen_packed_array( dtype, n_dim[1:], array[i] ) )
        if n_dim[0] > 1:
          cat_str = "{" + ", ".join( ret ) + "}"
        else:
          cat_str = ", ".join( ret )
        return cat_str
    fields = []
    for name, Type in dtype.get_all_properties().items():
      field = getattr( struct, name )
      if isinstance( Type, rdt.Vector ):
        _field = s._literal_number( Type.nbits, field )
      elif isinstance( Type, rdt.Struct ):
        _field = s._struct_instance( Type, field )
      elif isinstance( Type, rdt.PackedArray ):
        n_dim = Type.get_dim_sizes()
        sub_dtype = Type.get_sub_dtype()
        _field = _gen_packed_array( sub_dtype, n_dim, field )
      else:
        assert False, f"unrecognized data type {Type}!"
      fields.append( _field )
    if len( fields ) == 1:
      struct_str = fields[0]
    else:
      struct_str = "{" + ", ".join( fields ) + "}"
    return struct_str

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.

    Add support for accessing struct attribute in L3.
    """
    if isinstance( node.value.Type, rt.Signal ):
      if isinstance( node.value.Type, rt.Const ):
        try:
          obj = node.Type.get_object()
        except AttributeError:
          obj = None
        if obj is None:
          raise VerilogTranslationError( s.blk, node,
            f"attribute ({node.attr}) of constant struct instance ({node.value}) is not supported!" )
        else:
          if isinstance( obj, Bits ):
            s.signal_expr_prologue( node )
            node.sexpr['s_attr'] = \
                s._literal_number(obj.nbits, int(obj))
            node.sexpr["s_index"] = ""
            attr = node.attr
            return s.signal_expr_epilogue(node, f"{attr}")
          elif is_bitstruct_inst( obj ):
            s.signal_expr_prologue( node )
            node.sexpr['s_attr'] = \
                s._struct_instance(node.Type.get_dtype(), obj)
            node.sexpr["s_index"] = ""
            attr = node.attr
            return s.signal_expr_epilogue(node, f"{attr}")
          else:
            raise VerilogTranslationError( s.blk, node,
              f"attribute ({node.attr}) of constant struct instance ({node.value}) is not supported!" )

      elif isinstance( node.value.Type.get_dtype(), rdt.Struct ):
        value = s.visit( node.value )
        s.signal_expr_prologue( node )
        attr = node.attr
        s.check_res( node, attr )
        node.sexpr['s_attr'] += "__{}"
        node.sexpr['attr'].append( attr )
        return s.signal_expr_epilogue(node, f"{value}.{attr}")

    return super().visit_Attribute( node )

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):
    for value in node.values:
      value._top_expr = 1
    return super().visit_StructInst( node )

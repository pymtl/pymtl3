#=========================================================================
# BehavioralRTLIRGenL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L3 behavioral RTLIR generation pass."""

from pymtl3.datatypes import Bits, is_bitstruct_class, is_bitstruct_inst
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError

from . import BehavioralRTLIR as bir
from .BehavioralRTLIRGenL2Pass import (
    BehavioralRTLIRGeneratorL2,
    BehavioralRTLIRGenL2Pass,
)


class BehavioralRTLIRGenL3Pass( BehavioralRTLIRGenL2Pass ):
  def get_rtlir_generator_class( s ):
    return BehavioralRTLIRGeneratorL3

class BehavioralRTLIRGeneratorL3( BehavioralRTLIRGeneratorL2 ):

  def visit_Call( s, node ):
    """Return behavioral RTLIR of a method call.

    At L3 we need to support the syntax of struct instantiation in upblks.
    This is achieved by function calls like `struct( 1, 2, 0 )`.
    """
    obj = s.get_call_obj( node )
    if is_bitstruct_class( obj ):
      fields = obj.__bitstruct_fields__
      nargs = len(node.args)
      nfields = len(fields.keys())
      if nargs == 0:
        # Infer the values of each field by inspecting the object constructed
        # with default arguments
        inst = obj()
        values = [s._datatype_to_bir(getattr(inst, field)) for field in fields.keys()]
      else:
        # Otherwise all fields of the struct must be present in the arguments
        if nargs != nfields:
          raise PyMTLSyntaxError( s.blk, node,
            f'BitStruct {obj.__name__} has {nfields} fields but {nargs} arguments are given!' )
        values = [s.visit(arg) for arg in node.args]

      ret = bir.StructInst( obj, values )
      ret.ast = node
      return ret

    else:
      return super().visit_Call( node )

  def _datatype_to_bir( s, instance ):
    if isinstance( instance, Bits ):
      return s._bits_to_bir( instance )
    elif is_bitstruct_inst( instance ):
      return s._struct_to_bir( instance )
    else:
      assert False, f"unrecognized datatype instance {instance}"

  def _struct_to_bir( s, instance ):
    struct_cls = instance.__class__
    fields = struct_cls.__bitstruct_fields__.keys()
    values = [s._datatype_to_bir(getattr(instance, field)) for field in fields]
    return bir.StructInst( struct_cls, values )

  def _bits_to_bir( s, instance ):
    nbits = instance.nbits
    value = int(instance)
    return bir.SizeCast( nbits, bir.Number( value ) )

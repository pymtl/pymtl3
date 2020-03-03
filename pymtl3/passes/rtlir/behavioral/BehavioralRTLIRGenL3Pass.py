#=========================================================================
# BehavioralRTLIRGenL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L3 behavioral RTLIR generation pass."""

from pymtl3.datatypes import Bits, is_bitstruct_class, is_bitstruct_inst
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError
from pymtl3.passes.rtlir.util.utility import get_ordered_upblks, get_ordered_update_ff

from . import BehavioralRTLIR as bir
from .BehavioralRTLIRGenL2Pass import BehavioralRTLIRGeneratorL2


class BehavioralRTLIRGenL3Pass( BasePass ):
  def __call__( s, m ):
    """ generate RTLIR for all upblks of m """
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()
    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL3( m )

    upblks = {
      'CombUpblk' : get_ordered_upblks(m),
      'SeqUpblk'  : get_ordered_update_ff(m),
    }
    # Sort the upblks by their name
    upblks['CombUpblk'].sort( key = lambda x: x.__name__ )
    upblks['SeqUpblk'].sort( key = lambda x: x.__name__ )

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        upblk_info = m.get_update_block_info( blk )
        upblk = visitor.enter( blk, upblk_info[-1] )
        upblk.is_lambda = upblk_info[0]
        upblk.src       = upblk_info[1]
        upblk.lino      = upblk_info[2]
        upblk.filename  = upblk_info[3]
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = upblk

class BehavioralRTLIRGeneratorL3( BehavioralRTLIRGeneratorL2 ):
  def __init__( s, component ):
    super().__init__( component )

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

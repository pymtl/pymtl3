#=========================================================================
# SVTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 15, 2019
"""Provide SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.translator import RTLIRTranslator

from .behavioral import SVBehavioralTranslator as SV_BTranslator
from .structural import SVStructuralTranslator as SV_STranslator


def mk_SVTranslator( _RTLIRTranslator, _STranslator, _BTranslator ):

  def get_pretty( namespace, attr, newline=True ):
    ret = getattr(namespace, attr, "")
    if newline and (ret and ret[-1] != '\n'):
      ret += "\n"
    return ret

  class _SVTranslator( _RTLIRTranslator, _STranslator, _BTranslator ):

    def rtlir_tr_src_layout( s, hierarchy ):
      ret = ""
      # Add struct definitions
      for struct_dtype, tplt in hierarchy.decl_type_struct:
        ret += tplt['def'] + '\n'

      # Add component sources
      ret += hierarchy.component_src
      return ret

    def rtlir_tr_components( s, components ):
      return "\n\n".join( components )

    def rtlir_tr_component( s, behavioral, structural ):

      template =\
"""\
module {module_name}
(
{ports});
{body}
endmodule
"""
      ports_template = "{port_decls}{ifc_decls}"
      module_name = getattr( structural, "component_unique_name" )

      port_decls = get_pretty(structural, 'decl_ports', False)
      ifc_decls = get_pretty(structural, 'decl_ifcs', False)
      if port_decls or ifc_decls:
        if port_decls and ifc_decls:
          port_decls += ',\n'
        ifc_decls += '\n'
      ports = ports_template.format(**locals())

      const_decls = get_pretty(structural, "decl_consts")
      fvar_decls = get_pretty(behavioral, "decl_freevars")
      wire_decls = get_pretty(structural, "decl_wires")
      tmpvar_decls = get_pretty(behavioral, "decl_tmpvars")
      subcomp_decls = get_pretty(structural, "decl_subcomps")
      upblk_srcs = get_pretty(behavioral, "upblk_srcs")
      body = const_decls + fvar_decls + wire_decls + subcomp_decls \
           + tmpvar_decls + upblk_srcs
      connections = get_pretty(structural, "connections")
      if (body and connections) or (not body and connections):
        connections = '\n' + connections
      body += connections

      s._top_module_name = getattr( structural, "component_name", module_name )
      s._top_module_full_name = module_name
      return template.format( **locals() )

  return _SVTranslator

SVTranslator = mk_SVTranslator( RTLIRTranslator, SV_STranslator, SV_BTranslator )

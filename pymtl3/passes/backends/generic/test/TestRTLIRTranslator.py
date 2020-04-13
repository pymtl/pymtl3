#=========================================================================
# TestRTLIRTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Provide an RTLIR translator that fits testing purposes."""

from ..behavioral.test.TestBehavioralTranslator import TestBehavioralTranslator
from ..RTLIRTranslator import RTLIRTranslator
from ..structural.test.TestStructuralTranslator import TestStructuralTranslator


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_pretty( namespace, attr, newline=True ):
  ret = getattr(namespace, attr, "")
  if newline and (ret and ret[-1] != '\n'):
    ret += "\n"
  return ret

class TestRTLIRTranslator( RTLIRTranslator,
    TestStructuralTranslator, TestBehavioralTranslator ):

  def rtlir_tr_initialize( s ):
    pass

  def rtlir_tr_src_layout( s, hierarchy ):
    # struct definitions
    struct_defs = \
      "".join( f"struct {x}\n" for x in hierarchy.decl_type_struct.values() )
    component_src = hierarchy.component_src
    return struct_defs + component_src

  def rtlir_tr_components( s, components ):
    return "\n".join(components.values())

  def rtlir_tr_component( s, behavioral, structural ):
    template = \
"""\
component {component_name}
(
{ports});
{body}
endcomponent
"""
    ports_template = "{port_decls}{ifc_decls}"
    component_name = structural.component_unique_name

    port_decls = get_pretty(structural, "decl_ports", False)
    ifc_decls = get_pretty(structural, "decl_ifcs", False)
    ports = ports_template.format( **locals() )

    const_decls = get_pretty(structural, "decl_consts")
    fvar_decls = get_pretty(behavioral, "decl_freevars")
    wire_decls = get_pretty(structural, "decl_wires")
    tmpvar_decls = get_pretty(behavioral, "decl_tmpvars")
    subcomp_decls = get_pretty(structural, "decl_subcomps")
    upblk_srcs = get_pretty(behavioral, "upblk_srcs")
    connections = get_pretty(structural, "connections")
    body = const_decls + fvar_decls + wire_decls + subcomp_decls \
         + tmpvar_decls + upblk_srcs + connections

    return template.format( **locals() )

#=========================================================================
# RTLIRTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 15, 2019
"""Provide translators that convert RTLIR to backend representation."""

from .BaseRTLIRTranslator import TranslatorMetadata
from .behavioral import BehavioralTranslator
from .errors import RTLIRTranslationError
from .structural import StructuralTranslator


def mk_RTLIRTranslator( _StructuralTranslator, _BehavioralTranslator ):
  """Return an RTLIRTranslator from the two given translators."""
  class _RTLIRTranslator( _StructuralTranslator, _BehavioralTranslator ):
    """Template translator class parameterized by behavioral/structural translator.

    Components are assembled here because they have both behavioral
    and structural parts. This translator also generates the overall
    code layout of the backend representation.
    """

    # Override
    def clear( s, tr_top, tr_cfgs ):
      s.tr_cfgs = tr_cfgs
      s.hierarchy = TranslatorMetadata()
      super().clear( tr_top )

    def _gen_hierarchy_metadata( s, structural_ns, hierarchy_ns ):
      metadata = getattr( s.structural, structural_ns, {} )
      result = getattr( s.hierarchy, hierarchy_ns )

      for Type, data in metadata.items():
        if Type not in result:
          result[ Type ] = data

    # Override
    def translate( s, tr_top, tr_cfgs = None ):

      def get_component_nspace( namespace, m ):
        ns = TranslatorMetadata()
        for name, metadata_d in vars(namespace).items():
          # Hierarchical metadata will not be added
          if m in metadata_d:
            setattr( ns, name, metadata_d[m] )
        return ns

      def translate_component( m, components ):
        for child in m.get_child_components(repr):
          translate_component( child, components )

        name = s.structural.component_unique_name[m]
        if name not in components:
          components[name] = s.rtlir_tr_component(
              get_component_nspace( s.behavioral, m ),
              get_component_nspace( s.structural, m ),
          )
        s._gen_hierarchy_metadata( 'decl_type_vector', 'decl_type_vector' )
        s._gen_hierarchy_metadata( 'decl_type_array', 'decl_type_array'   )
        s._gen_hierarchy_metadata( 'decl_type_struct', 'decl_type_struct' )

      # Clear all translator metadata
      s.clear( tr_top, tr_cfgs )

      s.component = {}
      # Generate backend representation for each component
      s.hierarchy.components = {}
      s.hierarchy.decl_type_vector = {}
      s.hierarchy.decl_type_array = {}
      s.hierarchy.decl_type_struct = {}

      try:
        s.rtlir_tr_initialize()
        s.translate_behavioral( s.tr_top )
        s.translate_structural( s.tr_top )
        translate_component( s.tr_top, s.hierarchy.components )
      except AssertionError as e:
        msg = '' if e.args[0] is None else e.args[0]
        raise RTLIRTranslationError( s.tr_top, msg )

      # Generate the representation for all components
      s.hierarchy.component_src = s.rtlir_tr_components(s.hierarchy.components)

      # Generate the final backend code layout
      s.hierarchy.src = s.rtlir_tr_src_layout( s.hierarchy )

    #---------------------------------------------------------------------
    # Methods to be implemented by the backend translator
    #---------------------------------------------------------------------

    def rtlir_tr_initialize( s ):
      raise NotImplementedError()

    def rtlir_tr_src_layout( s, hierarchy ):
      raise NotImplementedError()

    def rtlir_tr_components( s, components ):
      raise NotImplementedError()

    def rtlir_tr_component( s, behavioral, structural ):
      raise NotImplementedError()

  return _RTLIRTranslator

RTLIRTranslator = mk_RTLIRTranslator( BehavioralTranslator, StructuralTranslator )

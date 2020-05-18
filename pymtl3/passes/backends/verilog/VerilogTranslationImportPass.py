#=========================================================================
# VerilogTranslationImportPass.py
#=========================================================================
# Translate and import components in the given hierarhcy.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.dsl import MetadataKey
from pymtl3.passes.BasePass import BasePass

from .import_.VerilogVerilatorImportConfigs import VerilogVerilatorImportConfigs
from .import_.VerilogVerilatorImportPass import VerilogVerilatorImportPass
from .translation.VerilogTranslationConfigs import VerilogTranslationConfigs
from .translation.VerilogTranslationPass import VerilogTranslationPass
from .VerilogPlaceholder import VerilogPlaceholder
from .VerilogPlaceholderConfigs import VerilogPlaceholderConfigs
from .VerilogPlaceholderPass import VerilogPlaceholderPass


class VerilogTranslationImportPass( BasePass ):

  #: Enable translation-import on the component.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  enable = MetadataKey(bool)

  def __call__( s, top ):
    """Translate-import the PyMTL component hierarhcy rooted at ``top``."""
    c = s.__class__
    s.top = top
    s.traverse_hierarchy( top )
    top.apply( c.get_translation_pass()() )
    s.add_placeholder_marks( top )
    return c.get_import_pass()()( top )

  def traverse_hierarchy( s, m ):
    c = s.__class__

    # Found a subtree that is marked as to be translated and imported
    if ( m.has_metadata( c.enable ) and m.get_metadata( c.enable ) ) or \
      isinstance( m, VerilogPlaceholder ):

      # Make sure the translation pass is enabled
      m.set_metadata( c.get_translation_pass().enable, True )

      # Make sure the import pass is enabled
      m.set_metadata( c.get_import_pass().enable, True )

    else:
      for child in m.get_child_components(repr):
        s.traverse_hierarchy( child )

  def add_placeholder_marks( s, m ):
    c = s.__class__

    # TODO: what we really want is to generate placeholders for components
    # to be translated and imported.
    if ( m.has_metadata( c.enable ) and m.get_metadata( c.enable ) ) or \
      isinstance( m, VerilogPlaceholder ):

      # Component m will look as if it has applied the Placeholder pass.
      # It will have the output pass data placeholder_config

      placeholder_pass = c.get_placeholder_pass()
      translation_pass = c.get_translation_pass()
      m.set_metadata( placeholder_pass.enable, True )

      if m.has_metadata( placeholder_pass.placeholder_config ):
        placeholder_config = m.get_metadata( placeholder_pass.placeholder_config )
      else:
        placeholder_config = c.get_placeholder_config()( m )

        if not isinstance( m, VerilogPlaceholder ):
          # If m is not a placeholder, we need to populate the v_include
          # placeholder config from all submodules into m.
          placeholder_config.v_include = list(c.get_hierarchy_v_include(m))

      placeholder_config.pickled_source_file = \
          m.get_metadata( translation_pass.translated_filename )
      placeholder_config.pickled_top_module = \
          m.get_metadata( translation_pass.translated_top_module )
      m.set_metadata( placeholder_pass.placeholder_config, placeholder_config )

    else:
      for child in m.get_child_components(repr):
        s.add_placeholder_marks( child )

  @staticmethod
  def get_translation_pass():
    return VerilogTranslationPass

  @staticmethod
  def get_import_pass():
    return VerilogVerilatorImportPass

  @staticmethod
  def get_placeholder_pass():
    return VerilogPlaceholderPass

  @staticmethod
  def get_placeholder_config():
    return VerilogPlaceholderConfigs

  # This recursive method needs to be a class method
  @classmethod
  def get_hierarchy_v_include( c, m ):
    all_v_includes = set()
    ph_config_key = c.get_placeholder_pass().placeholder_config
    if isinstance( m, VerilogPlaceholder ) and m.has_metadata( ph_config_key ):
      ph_config = m.get_metadata( ph_config_key )
      for v_include in ph_config.v_include:
        all_v_includes.add( v_include )
    else:
      for child in m.get_child_components(repr):
        all_v_includes |= c.get_hierarchy_v_include( child )
    return all_v_includes

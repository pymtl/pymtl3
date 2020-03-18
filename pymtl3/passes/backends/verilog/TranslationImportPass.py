#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components in the given hierarhcy.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.PassDataName import PassDataName

from .import_.VerilatorImportConfigs import VerilatorImportConfigs
from .import_.VerilatorImportPass import VerilatorImportPass
from .translation.TranslationConfigs import TranslationConfigs
from .translation.TranslationPass import TranslationPass
from .VerilogPlaceholderConfigs import VerilogPlaceholderConfigs
from .VerilogPlaceholderPass import VerilogPlaceholderPass


class TranslationImportPass( BasePass ):

  enable = PassDataName()

  def __call__( s, top ):
    c = s.__class__
    s.top = top
    s.traverse_hierarchy( top )
    top.apply( c.get_translation_pass()() )
    s.add_placeholder_marks( top )
    return c.get_import_pass()()( top )

  def traverse_hierarchy( s, m ):
    c = s.__class__

    # Found a subtree that is marked as to be translated and imported
    if m.has_pass_data( c.enable ) and m.get_pass_data( c.enable ):

      # Make sure the translation pass is enabled
      m.set_pass_data( c.get_translation_pass().enable, True )

      # Make sure the import pass is enabled
      m.set_pass_data( c.get_import_pass().enable, True )

    else:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  def add_placeholder_marks( s, m ):
    c = s.__class__

    # TODO: what we really want is to generate placeholders for components
    # to be translated and imported.
    if m.has_pass_data( c.enable ) and m.get_pass_data( c.enable ):

      # Component m will look as if it has applied the Placeholder pass.
      # It will have the output pass data placeholder_config

      placeholder_pass = c.get_placeholder_pass()
      translation_pass = c.get_translation_pass()
      m.set_pass_data( placeholder_pass.enable, True )

      if m.has_pass_data( placeholder_pass.placeholder_config ):
        placeholder_config = m.get_pass_data( placeholder_pass.placeholder_config )
      else:
        placeholder_config = c.get_placeholder_config()( m )

      placeholder_config.pickled_source_file = \
          m.get_pass_data( translation_pass.translated_filename )
      placeholder_config.pickled_top_module = \
          m.get_pass_data( translation_pass.translated_top_module )
      m.set_pass_data( placeholder_pass.placeholder_config, placeholder_config )

    else:
      for child in m.get_child_components():
        s.add_placeholder_marks( child )

  @staticmethod
  def get_translation_pass():
    return TranslationPass

  @staticmethod
  def get_import_pass():
    return VerilatorImportPass

  @staticmethod
  def get_placeholder_pass():
    return VerilogPlaceholderPass

  @staticmethod
  def get_placeholder_config():
    return VerilogPlaceholderConfigs

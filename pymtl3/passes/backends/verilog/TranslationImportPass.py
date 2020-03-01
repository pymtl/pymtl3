#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components having the `verilog_translate_import`
# attribute.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.BasePass import BasePass

from .import_.VerilatorImportConfigs import VerilatorImportConfigs
from .import_.VerilatorImportPass import VerilatorImportPass
from .translation.TranslationConfigs import TranslationConfigs
from .translation.TranslationPass import TranslationPass
from .VerilogPlaceholderConfigs import VerilogPlaceholderConfigs


class TranslationImportPass( BasePass ):

  def __call__( s, top ):
    s.top = top
    s.traverse_hierarchy( top )
    top.apply( s.get_translation_pass() )
    s.add_placeholder_marks( top )
    return s.get_import_pass()( top )

  def traverse_hierarchy( s, m ):
    search_subtree = True

    # Found a subtree that is marked as to be translated and imported
    if hasattr(m, s.get_flag_name()) and getattr(m, s.get_flag_name()):

      # Use default translation config if it is missing
      if not hasattr(m, s.get_translation_flag_name()):
        setattr(m, s.get_translation_flag_name(), s.get_translation_configs())

      # Assert that this instance should be translated
      getattr(m, s.get_translation_flag_name()).translate = True

      if not hasattr(m, s.get_import_flag_name()):
        setattr(m, s.get_import_flag_name(), s.get_import_configs())

      search_subtree = False

    if search_subtree:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  def add_placeholder_marks( s, m ):
    # TODO: what we really want is to generate placeholders for components
    # to be translated and imported. Right now we simply attach the placeholder
    # and import configs to the components.
    if hasattr( m, s.get_flag_name() ) and getattr( m, s.get_flag_name() ):

      if not hasattr( m, 'config_placeholder' ):
        m.config_placeholder = VerilogPlaceholderConfigs()
      if not hasattr( m, s.get_import_flag_name() ):
        m.config_verilog_import = VerilatorImportConfigs()

      m.config_placeholder.pickled_source_file = \
          getattr(m, s.get_translation_pass_namespace()).translated_filename
      m.config_placeholder.pickled_top_module = \
          getattr(m, s.get_translation_pass_namespace()).translated_top_module

    else:
      for child in m.get_child_components():
        s.add_placeholder_marks( child )

  def get_translation_pass( s ):
    return TranslationPass()

  def get_import_pass( s ):
    return VerilatorImportPass()

  def get_flag_name( s ):
    return "verilog_translate_import"

  def get_translation_flag_name( s ):
    return "config_verilog_translate"

  def get_translation_pass_namespace( s ):
    return "_pass_verilog_translation"

  def get_import_flag_name( s ):
    return "config_verilog_import"

  def get_translation_configs( s ):
    return TranslationConfigs()

  def get_import_configs( s ):
    return VerilatorImportConfigs(vl_Wno_list=['UNOPTFLAT', 'UNSIGNED', 'WIDTH'])

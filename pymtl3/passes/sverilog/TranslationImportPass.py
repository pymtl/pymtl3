#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components having the `sverilog_translate_import`
# attribute.
# 
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.dsl import Placeholder
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir.rtype.RTLIRType import get_rtlir
from pymtl3.passes.sverilog.util.utility import get_component_unique_name
from pymtl3.passes.sverilog.import_.ImportConfigs import ImportConfigs
from pymtl3.passes.sverilog.import_.ImportPass import ImportPass
from pymtl3.passes.sverilog.translation.TranslationConfigs import TranslationConfigs
from pymtl3.passes.sverilog.translation.TranslationPass import TranslationPass


class TranslationImportPass( BasePass ):

  def __call__( s, top ):
    s.top = top
    s.traverse_hierarchy( top )
    top.apply( s.get_translation_pass() )
    return s.get_import_pass()( top )

  def traverse_hierarchy( s, m ):
    if hasattr(m, s.get_flag_name()):
      if not hasattr(m, s.get_translation_flag_name()):
        setattr(m, s.get_translation_flag_name(), s.get_translation_configs())
      if not hasattr(m, s.get_import_flag_name()):
        setattr(m, s.get_import_flag_name(), s.get_import_configs())

      # If a Placeholder is to be translated and imported, the translation-import
      # pass should explicitly mark the file name of the Verilog source and the
      # top level module name in import configs.
      if isinstance(m, Placeholder):
        v_src = getattr(m, s.get_translation_flag_name()).get_v_src()
        assert v_src
        import_config = getattr(m, s.get_import_flag_name())
        rtype = get_rtlir(m)
        import_config.set_option('vl_src', v_src)

    for child in m.get_child_components():
      s.traverse_hierarchy( child )

  def get_translation_pass( s ):
    return TranslationPass()

  def get_import_pass( s ):
    return ImportPass()

  def get_flag_name( s ):
    return "sverilog_translate_import"

  def get_translation_flag_name( s ):
    return "sverilog_translate"

  def get_import_flag_name( s ):
    return "sverilog_import"

  def get_translation_configs( s ):
    return TranslationConfigs()

  def get_import_configs( s ):
    return ImportConfigs(vl_Wno_list=['UNOPTFLAT', 'UNSIGNED'])

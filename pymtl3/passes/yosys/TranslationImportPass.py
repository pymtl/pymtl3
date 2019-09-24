#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components having the `yosys_translate_import`
# attribute.
# 
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.sverilog.TranslationImportPass import (
    TranslationImportPass as SVerilogTranslationImportPass,
)
from pymtl3.passes.yosys.import_.ImportPass import ImportPass
from pymtl3.passes.yosys.translation.TranslationPass import TranslationPass


class TranslationImportPass( SVerilogTranslationImportPass ):

  def get_translation_pass( s ):
    return TranslationPass()

  def get_import_pass( s ):
    return ImportPass()

  def get_flag_name( s ):
    return "yosys_translate_import"

  def get_translation_flag_name( s ):
    return "yosys_translate"

  def get_import_flag_name( s ):
    return "yosys_import"

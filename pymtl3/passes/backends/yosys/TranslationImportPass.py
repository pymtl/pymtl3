#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components having the `yosys_translate_import`
# attribute.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.backends.sverilog.TranslationImportPass import (
    TranslationImportPass as SVerilogTranslationImportPass,
)

from .import_.ImportPass import ImportPass
from .translation.TranslationPass import TranslationPass


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
    return "config_yosys_import"

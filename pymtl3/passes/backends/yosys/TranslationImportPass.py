#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components having the `yosys_translate_import`
# attribute.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.backends.verilog.TranslationImportPass import (
    TranslationImportPass as VerilogTranslationImportPass,
)

from .import_.VerilatorImportPass import VerilatorImportPass
from .translation.TranslationPass import TranslationPass


class TranslationImportPass( VerilogTranslationImportPass ):

  def get_translation_pass( s ):
    return TranslationPass()

  def get_import_pass( s ):
    return VerilatorImportPass()

  def get_flag_name( s ):
    return "yosys_translate_import"

  def get_translation_flag_name( s ):
    return "yosys_translate"

  def get_import_flag_name( s ):
    return "config_yosys_import"

  def get_translation_pass_namespace( s ):
    return "_pass_yosys_translation"

#=========================================================================
# TranslationImportPass.py
#=========================================================================
# Translate and import components in the given hierarchy.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.backends.verilog.TranslationImportPass import (
    TranslationImportPass as VerilogTranslationImportPass,
)

from .import_.VerilatorImportPass import VerilatorImportPass
from .translation.TranslationPass import TranslationPass


class TranslationImportPass( VerilogTranslationImportPass ):

  @staticmethod
  def get_translation_pass():
    return TranslationPass

  @staticmethod
  def get_import_pass():
    return VerilatorImportPass

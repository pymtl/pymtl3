#=========================================================================
# YosysTranslationImportPass.py
#=========================================================================
# Translate and import components in the given hierarchy.
#
# Author : Peitian Pan
# Date   : Aug 6, 2019

from pymtl3.passes.backends.verilog.VerilogTranslationImportPass import (
    VerilogTranslationImportPass,
)

from .import_.YosysVerilatorImportPass import YosysVerilatorImportPass
from .translation.YosysTranslationPass import YosysTranslationPass


class YosysTranslationImportPass( VerilogTranslationImportPass ):

  @staticmethod
  def get_translation_pass():
    return YosysTranslationPass

  @staticmethod
  def get_import_pass():
    return YosysVerilatorImportPass

#=========================================================================
# TranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 8, 2019
"""Translate a PyMTL component hierarhcy into yosys-verilog source code."""

from pymtl3.passes.backends.verilog import TranslationPass

from .YosysTranslator import YosysTranslator


class TranslationPass( TranslationPass ):

  def __call__( s, top ):
    s.top = top
    s.translator = YosysTranslator( s.top )
    s.traverse_hierarchy( top )

#=========================================================================
# TranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 12, 2019
"""Translate a PyMTL component hierarhcy into SystemVerilog source code."""

from __future__ import absolute_import, division, print_function

import os

from pymtl3.passes.BasePass import BasePass, PassMetadata

from .SVTranslator import SVTranslator


def mk_TranslationPass( _SVTranslator ):

  class _TranslationPass( BasePass ):

    def __call__( s, top ):

      if not hasattr( top, '_pass_sverilog_translation' ):
        top._pass_sverilog_translation = PassMetadata()

      translator = _SVTranslator( top )
      translator.translate()

      module_name = translator._top_module_name
      output_file = module_name + '.sv'

      with open( output_file, 'w', 0 ) as output:
        output.write( translator.hierarchy.src )
        output.flush()
        os.fsync( output )
        output.close()

      top._translator = translator
      top._pass_sverilog_translation.translated = True

  return _TranslationPass

TranslationPass = mk_TranslationPass( SVTranslator )

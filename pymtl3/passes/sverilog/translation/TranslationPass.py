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

      s.top = top
      s.translator = _SVTranslator( s.top )
      s.traverse_hierarchy( top )

    def traverse_hierarchy( s, m ):
      if hasattr(m, "sverilog_translate") and m.sverilog_translate:
        if not hasattr( m, '_pass_sverilog_translation' ):
          m._pass_sverilog_translation = PassMetadata()

        s.translator.translate( m )

        module_name = s.translator._top_module_full_name
        output_file = module_name + '.sv'

        with open( output_file, 'w' ) as output:
          output.write( s.translator.hierarchy.src )
          output.flush()
          os.fsync( output )
          output.close()

        m._translator = s.translator
        m._pass_sverilog_translation.translated = True
      else:
        for child in m.get_child_components():
          s.traverse_hierarchy( child )

  return _TranslationPass

TranslationPass = mk_TranslationPass( SVTranslator )

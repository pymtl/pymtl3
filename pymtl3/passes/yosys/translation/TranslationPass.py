#=========================================================================
# TranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 8, 2019
"""Translate a PyMTL component hierarhcy into yosys-sverilog source code."""

from __future__ import absolute_import, division, print_function

import os

from pymtl3.passes.BasePass import BasePass, PassMetadata

from .YosysTranslator import YosysTranslator


class TranslationPass( BasePass ):

  def __call__( s, top ):

    s.top = top
    s.translator = YosysTranslator( s.top )
    s.traverse_hierarchy( top )

  def traverse_hierarchy( s, m ):

    if hasattr( m, "yosys_translate" ) and m.yosys_translate:

      if not hasattr( m, '_pass_yosys_translation' ):
        m._pass_yosys_translation = PassMetadata()

      s.translator.translate( m )

      module_name = s.translator._top_module_full_name
      output_file = module_name + '.sv'

      with open( output_file, 'w' ) as output:
        output.write( s.translator.hierarchy.src )
        output.flush()
        os.fsync( output )
        output.close()

      m._translator = s.translator
      m._pass_yosys_translation.translated = True

    else:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

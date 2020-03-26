#=========================================================================
# TranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 8, 2019
"""Translate a PyMTL component hierarhcy into yosys-verilog source code."""

import filecmp
import os

from pymtl3.passes.backends.verilog import TranslationConfigs
from pymtl3.passes.BasePass import BasePass, PassMetadata

from .YosysTranslator import YosysTranslator


class TranslationPass( BasePass ):

  def __call__( s, top ):

    s.top = top
    s.translator = YosysTranslator( s.top )
    s.traverse_hierarchy( top )

  def gen_tr_cfgs( s, m ):
    tr_cfgs = {}

    def traverse( m ):
      nonlocal tr_cfgs

      if not hasattr( m, 'config_yosys_translate' ) or \
         isinstance( m.config_yosys_translate, bool ):
        tr_cfgs[m] = TranslationConfigs()
      else:
        tr_cfgs[m] = m.config_yosys_translate

      for _m in m.get_child_components(repr):
        traverse( _m )

    traverse( m )
    return tr_cfgs

  def traverse_hierarchy( s, m ):

    if hasattr( m, "yosys_translate" ) and m.yosys_translate:

      if not hasattr( m, '_pass_yosys_translation' ):
        m._pass_yosys_translation = PassMetadata()

      s.translator.translate( m, s.gen_tr_cfgs(m) )

      module_name = s.translator._top_module_full_name
      output_file = module_name + '.v'
      temporary_file = module_name + '.v.tmp'

      # First write the file to a temporary file
      m._pass_yosys_translation.is_same = False
      with open( temporary_file, 'w' ) as output:
        output.write( s.translator.hierarchy.src )
        output.flush()
        os.fsync( output )
        output.close()

      # `is_same` is set if there exists a file that has the same filename as
      # `output_file`, and that file is the same as the temporary file
      if ( os.path.exists(output_file) ):
        m._pass_yosys_translation.is_same = \
            filecmp.cmp( temporary_file, output_file )

      # Rename the temporary file to the output file
      os.rename( temporary_file, output_file )

      # Expose some attributes about the translation process
      m.translated_top_module_name = module_name
      m._translator = s.translator
      m._pass_yosys_translation.translated = True

      m._pass_yosys_translation.translated_filename = output_file
      m._pass_yosys_translation.translated_top_module = module_name

    else:
      for child in m.get_child_components(repr):
        s.traverse_hierarchy( child )

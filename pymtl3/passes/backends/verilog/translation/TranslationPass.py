#=========================================================================
# TranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 12, 2019
"""Translate a PyMTL component hierarhcy into SystemVerilog source code."""

import filecmp
import os

from pymtl3.passes.backends.verilog import TranslationConfigs
from pymtl3.passes.BasePass import BasePass, PassMetadata

from .VTranslator import VTranslator


def mk_TranslationPass( _VTranslator ):

  class _TranslationPass( BasePass ):

    def __call__( s, top ):

      s.top = top
      s.translator = _VTranslator( s.top )
      s.traverse_hierarchy( top )

    def gen_tr_cfgs( s, m ):
      tr_cfgs = {}

      def traverse( m ):
        nonlocal tr_cfgs

        if not hasattr( m, 'config_verilog_translate' ) or \
           isinstance( m.config_verilog_translate, bool ):
          tr_cfgs[m] = TranslationConfigs()
        else:
          tr_cfgs[m] = m.config_verilog_translate

        for _m in m.get_child_components(repr):
          traverse( _m )

      traverse( m )
      return tr_cfgs

    def traverse_hierarchy( s, m ):

      if hasattr(m, "config_verilog_translate") and m.config_verilog_translate and \
         m.config_verilog_translate.translate:

        if not hasattr( m, '_pass_verilog_translation' ):
          m._pass_verilog_translation = PassMetadata()

        s.translator.translate( m, s.gen_tr_cfgs(m) )

        module_name = s.translator._top_module_full_name

        if m.config_verilog_translate.explicit_file_name:
          fname = m.config_verilog_translate.explicit_file_name
          if '.v' in fname:
            filename = fname.split('.v')[0]
          elif '.sv' in fname:
            filename = fname.split('.sv')[0]
          else:
            filename = fname
        else:
          filename = module_name

        output_file = filename + '.v'
        temporary_file = filename + '.v.tmp'

        # First write the file to a temporary file
        m._pass_verilog_translation.is_same = False
        with open( temporary_file, 'w' ) as output:
          output.write( s.translator.hierarchy.src )
          output.flush()
          os.fsync( output )
          output.close()

        # `is_same` is set if there exists a file that has the same filename as
        # `output_file`, and that file is the same as the temporary file
        if ( os.path.exists(output_file) ):
          m._pass_verilog_translation.is_same = \
              filecmp.cmp( temporary_file, output_file )

        # Rename the temporary file to the output file
        os.rename( temporary_file, output_file )

        # Expose some attributes about the translation process
        m.translated_top_module_name = module_name
        m._translator = s.translator
        m._pass_verilog_translation.translated = True

        m._pass_verilog_translation.translated_filename = output_file
        m._pass_verilog_translation.translated_top_module = module_name

      else:
        for child in m.get_child_components(repr):
          s.traverse_hierarchy( child )

  return _TranslationPass

TranslationPass = mk_TranslationPass( VTranslator )

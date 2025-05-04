#=========================================================================
# VerilogTranslationPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 12, 2019
"""Translate a PyMTL component hierarhcy into SystemVerilog source code."""
import os, tempfile

from pymtl3 import MetadataKey
from pymtl3.passes.BasePass import BasePass

from ..util.utility import verilog_cmp
from .VTranslator import VTranslator


class VerilogTranslationPass( BasePass ):
  """Translate a PyMTL component hierarchy into Verilog."""

  # Translation pass input pass data

  #: Enable translation on a component.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  enable                = MetadataKey(bool)

  #: Specify the filename of the translated source file.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: value of ``explicit_module_name`` of the top level
  explicit_file_name    = MetadataKey(str)

  #: Specify the translated name of the component.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: component class name concatenated with parameters
  explicit_module_name  = MetadataKey(str)

  #: Wrap component translation result within \`ifndef SYNTHESIS
  #: Enabling this option effectively removes the component from
  #: the hierarchy during logic synthesis.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  no_synthesis          = MetadataKey(bool)

  #: In the translated source, wrap the clk port connection of the
  #: component within \`ifndef SYNTHESIS.
  #: This option can only be enabled while ``no_synthesis`` is ``True``.
  #: Enabling this option effectively removes the clk pin of the component
  #: during logic synthesis.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  no_synthesis_no_clk   = MetadataKey(bool)

  #: In the translated source, wrap the reset port connection of the
  #: component within \`ifndef SYNTHESIS.
  #: This option can only be enabled while ``no_synthesis`` is ``True``.
  #: Enabling this option effectively removes the reset pin of the component
  #: during logic synthesis.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  no_synthesis_no_reset = MetadataKey(bool)

  # Translation pass output pass data

  #: An instance of :class:`TranslationConfigs` that contains the parsed options.
  #:
  #: Type: ``TranslationConfigs``; output
  translate_config      = MetadataKey()

  #: Whether or not the translated result is the same as the existing output file.
  #:
  #: Type: ``bool``; output
  is_same               = MetadataKey(bool)

  #: A reference of the translator called during translation.
  #:
  #: Type: output
  translator            = MetadataKey()

  #: Whether or not the component has been translated.
  #:
  #: Type: ``bool``; output
  translated            = MetadataKey(bool)

  #: Filename of the translation result.
  #:
  #: Type: ``str``; output
  translated_filename   = MetadataKey(str)

  #: Top level module name in the translation result.
  #:
  #: Type: ``str``; output
  translated_top_module = MetadataKey(str)

  def __call__( s, top ):
    """Translate a PyMTL component hierarhcy rooted at ``top``."""
    s.top = top
    s.translator = VTranslator( s.top )
    s.traverse_hierarchy( top )

  def get_translation_config( s ):
    from pymtl3.passes.backends.verilog.translation.VerilogTranslationConfigs import (
        VerilogTranslationConfigs,
    )
    return VerilogTranslationConfigs

  def gen_tr_cfgs( s, m ):
    tr_cfgs = {}

    def traverse( m ):
      nonlocal tr_cfgs
      tr_cfgs[m] = s.get_translation_config()( m )
      for _m in m.get_child_components(repr):
        traverse( _m )

    traverse( m )
    return tr_cfgs

  def traverse_hierarchy( s, m ):
    c = s.__class__

    if m.has_metadata( c.enable ) and m.get_metadata( c.enable ):
      m.set_metadata( c.translate_config, s.gen_tr_cfgs(m) )
      s.translator.translate( m, m.get_metadata( c.translate_config ) )

      module_name = s.translator._top_module_full_name

      if m.has_metadata( c.explicit_file_name ) and \
         m.get_metadata( c.explicit_file_name ):
        fname = m.get_metadata( c.explicit_file_name )
        if '.v' in fname:
          filename = fname.split('.v')[0]
        elif '.sv' in fname:
          filename = fname.split('.sv')[0]
        else:
          filename = fname
      else:
        filename = f"{module_name}__pickled"

      output_file = filename + '.v'

      # Create a temporary file under the current directory.
      is_same = False
      tmp_fd, tmp_path = tempfile.mkstemp(dir=os.curdir, text=True)

      with open(tmp_path, "w+") as tmp_file:
        tmp_file.write( s.translator.hierarchy.src )
        tmp_file.flush()
        tmp_file.seek(0)
        os.fsync( tmp_file )

        # `is_same` is set if there exists a file that has the same filename as
        # `output_file`, and that file is the same as the temporary file.
        if ( os.path.exists(output_file) ):
          is_same = verilog_cmp( tmp_file, output_file )

        if not is_same:
          # Rename the temporary file to the output file. os.replace() is an
          # atomic operation as required by POSIX.
          os.replace( tmp_path, output_file )

        # Expose some attributes about the translation process.
        m.set_metadata( c.is_same,               is_same      )
        m.set_metadata( c.translator,            s.translator )
        m.set_metadata( c.translated,            True         )
        m.set_metadata( c.translated_filename,   output_file  )
        m.set_metadata( c.translated_top_module, module_name  )

      # Clean up the temporary file.
      os.close( tmp_fd )
      if os.path.exists( tmp_path ):
        os.remove( tmp_path )

    else:
      for child in m.get_child_components(repr):
        s.traverse_hierarchy( child )

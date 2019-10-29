#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to sverilog passes."""

import os
import shutil
import textwrap
from hashlib import blake2b

from pymtl3.passes.rtlir.util.utility import get_component_full_name


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_component_unique_name( c_rtype ):
  full_name = get_component_full_name( c_rtype )

  if len( full_name ) < 64:
    return full_name

  comp_name = c_rtype.get_name()
  param_hash = blake2b(digest_size = 8)
  param_hash.update(full_name[len(comp_name):].encode('ascii'))
  param_name = param_hash.hexdigest()
  return comp_name + "__" + param_name

  def get_string( obj ):
    """Return the string that identifies `obj`"""
    if isinstance(obj, type): return obj.__name__
    return str( obj )

def wrap( s ):
  col = shutil.get_terminal_size().columns
  return "\n".join(sum((textwrap.wrap(line, col) for line in s.split("\n")), []))

def expand( v ):
  return os.path.expanduser(os.path.expandvars(v))

def get_dir( cur_file ):
  return os.path.dirname(os.path.abspath(cur_file))+os.path.sep

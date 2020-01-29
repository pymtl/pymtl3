#=========================================================================
# PlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Placeholders."""

import os
from textwrap import fill, indent

from pymtl3.passes.PassConfigs import BasePassConfigs, Checker


def expand( v ):
  return os.path.expanduser(os.path.expandvars(v))

class PlaceholderConfigs( BasePassConfigs ):

  Options = {
    # Enable?
    "is_valid" : True,

    # Enable verbose mode?
    "verbose" : False,

    # Parameters
    # Map the names of parameters to their values
    # If {} is provided, use the parameters inferred from `construct` instead
    "params" : {},

    # Port name mapping
    # Map PyMTL port names to external port names
    "port_map" : {},

    # Expects the name of the top component in external source files
    # "" to use name of the current component to be imported
    "top_module" : "",

    # Expects path of the file that contains the top module
    "src_file" : "",

    # Does the module to be imported has `clk` port?
    "has_clk" : True,

    # Does the module to be imported has `reset` port?
    "has_reset" : True,

    # Give an explicit name to the wrapper module
    # Use {top_module}_wrapper by default
    # "explicit_module_name" : "",
  }

  Checkers = {
    ("is_valid", "verbose", "has_clk", "has_reset") :
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),

    ("params", "port_map") : Checker( lambda v: isinstance(v, dict), "expects a dict"),

    "top_module": Checker( lambda v: isinstance(v, str) and v, "expects a non-empty string"),

    "src_file": Checker( lambda v: isinstance(v, str) and (os.path.isfile(expand(v)) or not v),
                "src_file should be a path to a file or an empty string!" ),

    # "explicit_module_name": Checker( lambda v: isinstance(v, str), "expects a string" ),
  }

  PassName = 'PlaceholderConfigs'

  def get_port_map( s ):
    pmap = s.port_map
    return lambda name: pmap[name] if name in pmap else name

  def vprint( s, msg, nspaces = 0, use_fill = False ):
    if s.verbose:
      if use_fill:
        print(indent(fill(msg), " "*nspaces))
      else:
        print(indent(msg, " "*nspaces))

  def is_default( s, opt ):
    return getattr( s, opt ) == s.Options[opt]

#=========================================================================
# PlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Placeholders."""

import os

from pymtl3.passes.PassConfigs import BasePassConfigs, Checker


def expand( v ):
  return os.path.expanduser(os.path.expandvars(v))

class PlaceholderConfigs( BasePassConfigs ):

  Options = {
    # Should placeholder passes handle this instance?
    "is_valid" : True,

    # Does the module to be imported has `clk` port?
    "has_clk" : True,

    # Does the module to be imported has `reset` port?
    "has_reset" : True,

    # Give an explicit name to the wrapper module
    # Use {top_module}_wrapper by default
    # "explicit_module_name" : "",
  }

  Checkers = {
    ("is_valid", "has_clk", "has_reset") :
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),

    # "explicit_module_name": Checker( lambda v: isinstance(v, str), "expects a string" ),
  }

  PassName = 'PlaceholderConfigs'

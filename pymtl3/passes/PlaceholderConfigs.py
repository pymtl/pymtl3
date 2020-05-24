#=========================================================================
# PlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Placeholders."""

import os

from pymtl3.passes.PassConfigs import BasePassConfigs, Checker
from pymtl3.passes.PlaceholderPass import PlaceholderPass


def expand( path ):
  return os.path.expanduser(os.path.expandvars(path))

class PlaceholderConfigs( BasePassConfigs ):

  Options = {
    # Should placeholder passes handle this instance?
    "enable" : True,

    # Does the module to be imported has `clk` port?
    "has_clk" : True,

    # Does the module to be imported has `reset` port?
    "has_reset" : True,
  }

  Checkers = {
    ("enable", "has_clk", "has_reset") :
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),
  }

  Pass = PlaceholderPass

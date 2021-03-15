#=========================================================================
# VerilogTranslationConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 28, 2020

from pymtl3.passes.backends.verilog import VerilogTranslationPass
from pymtl3.passes.PassConfigs import BasePassConfigs, Checker


class VerilogTranslationConfigs( BasePassConfigs ):

  Options = {
    # Translate the current instance?
    "enable" : False,

    # Give an explicit file name to the translated source
    "explicit_file_name" : "",

    # Give an explicit module name to the translated component
    "explicit_module_name" : "",

    # Remove module definition during synthesis
    # Note that this could be applied to non-top modules
    "no_synthesis" : False,

    # This module does not have clk pin during synthesis
    # Note that this could be applied to non-top modules
    # This option can only be enabled if no_synthesis is True
    "no_synthesis_no_clk" : False,

    # This module does not have reset pin during synthesis
    # Note that this could be applied to non-top modules
    # This option can only be enabled if no_synthesis is True
    "no_synthesis_no_reset" : False,
  }

  Checkers = {
    ("enable", "no_synthesis", "no_synthesis_no_clk", "no_synthesis_no_reset") :
    Checker( lambda v: isinstance( v, bool ), "expects a boolean" ),

    ("explicit_file_name", "explicit_module_name") :
    Checker( lambda v: isinstance(v, str), "expects a string" )
  }

  Pass = VerilogTranslationPass

#=========================================================================
# TranslationConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 28, 2020

from pymtl3.passes.PassConfigs import BasePassConfigs, Checker

class TranslationConfigs( BasePassConfigs ):

  Options = {
    # Translate the current instance?
    "translate" : True,

    # Give an explicit file name to the translated source
    "explicit_file_name" : "",

    # Give an explicit module name to the translated top level
    "explicit_module_name" : "",
  }

  Checkers = {
    "translate" : 
    Checker( lambda v: isinstance( v, bool ), "expects a boolean" ),

    ("explicit_file_name", "explicit_module_name") :
    Checker( lambda v: isinstance(v, str), "expects a string" )
  }

  PassName = "sverilog.TranslationPass"

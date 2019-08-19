#=========================================================================
# TranslationConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Aug 4, 2019

from pymtl3.passes.PassConfigs import BasePassConfigs
from pymtl3.passes.sverilog.util.utility import expand


class TranslationConfigs( BasePassConfigs ):
  PassName = "sverilog.TranslationPass"
  Options = {
    "v_src" : "",
  }

  def __init__( s, **kwargs ):
    s.set_checker(
        "v_src",
        lambda p: os.path.isfile(expand(path)),
        "expects path to a Verilog source file")
    super().__init__( **kwargs )

  def get_v_src( s ):
    return expand(s.get_option( "v_src" ))

#=========================================================================
# VerilogPlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Verilog placeholders."""

import os
from copy import deepcopy

from pymtl3.passes.PassConfigs import Checker
from pymtl3.passes.PlaceholderConfigs import PlaceholderConfigs, expand

from .VerilogPlaceholderPass import VerilogPlaceholderPass


class VerilogPlaceholderConfigs( PlaceholderConfigs ):

  VerilogOptions = {
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

    # -f
    # Expects the path to the flist file; "" to disable this option
    "v_flist" : "",

    # -v
    # Expects a list of paths to Verilog files; [] to disable this option
    "v_libs" : [],

    # -I ( alias of -y and +incdir+ )
    # Expects a list of include paths; [] to disable this option
    "v_include" : [],

    # The separator used for name mangling
    "separator" : '__',
  }

  VerilogCheckers = {
    ("params", "port_map") : Checker( lambda v: isinstance(v, dict), "expects a dict"),

    "top_module": Checker( lambda v: isinstance(v, str) and v, "expects a non-empty string"),

    "src_file": Checker( lambda v: isinstance(v, str) and (os.path.isfile(expand(v)) or not v),
                "src_file should be a path to a file or an empty string!" ),

    "v_flist": Checker( lambda v: isinstance(v, str) and os.path.isfile(expand(v)) or v == "",
                         "expects a path to a file" ),

    "v_libs": Checker( lambda v: isinstance(v, list) and all(os.path.exists(expand(p)) for p in v),
                            "expects a list of paths to files"),

    "v_include": Checker( lambda v: isinstance(v, list) and all(os.path.isdir(expand(p)) for p in v),
                            "expects a list of paths to directory"),
  }

  Pass = VerilogPlaceholderPass

  def __new__( cls, m ):
    inst = super().__new__( cls )

    # Do not pollute the attributes of the parent class
    cls.Options  = deepcopy( PlaceholderConfigs.Options )
    cls.Checkers = deepcopy( PlaceholderConfigs.Checkers )

    for key, val in cls.VerilogOptions.items():
      assert key not in cls.Options,\
        f'config {key} is duplicated between PlaceholderConfigs and VerilogPlaceholderConfigs'
      cls.Options[key] = val

    for cfgs, chk in cls.VerilogCheckers.items():
      if isinstance( cfgs, tuple ):
        for cfg in cfgs:
          inst._add_to_checkers( cls.Checkers, cfg, chk )
      elif isinstance( cfgs, str ):
        inst._add_to_checkers( cls.Checkers, cfgs, chk )

    return inst

  # Override
  def check( s ):
    super().check()

    # Exactly one of src_file and v_flist should be non-empty
    if (s.v_flist and os.path.isfile(expand(s.src_file))) or \
       (not s.v_flist and not os.path.isfile(expand(s.src_file))):
      raise InvalidPassOptionValue( 'src_file', s.src_file, s.Pass.__name__,
          'exactly one of src_file and v_flist should be non-emtpy!' )

  def get_port_map( s ):
    pmap = { p._dsl.full_name: name for p, name in s.port_map.items() }
    return lambda name: pmap[name] if name in pmap else name

  def _add_to_checkers( s, checkers, cfg, chk ):
    assert cfg not in checkers,\
      f'config {cfg} is duplicated between PlaceholderConfigs!'
    checkers[cfg] = chk

  # override to avoid deepcopying ports
  def collect_all_pass_configs( s, m ):
    c = s.__class__
    for opt, default in c.Options.items():
      assert not hasattr( s, opt ), f"There is already a field in config called '{opt}'. What happened?"
      if not m.has_metadata( getattr( c.Pass, opt ) ):
        setattr( s, opt, default )
      else:
        setattr( s, opt, m.get_metadata( getattr( c.Pass, opt ) ) )

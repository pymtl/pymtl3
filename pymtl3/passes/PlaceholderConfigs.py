#=========================================================================
# PlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 26, 2020

from copy import copy

from pymtl3 import Placeholder


class PlaceholderConfigs:

  Configs = {
      'is_valid'     : True,
      'top_module'   : '',
      'verilog_name' : '',
      'params'       : {},
      'portmap'      : {},
      'src_file'     : '',
      'pickled_file' : '',
      'file_type'    : 'SVerilog',
      'include_path' : [],
      'has_clk'      : True,
      'has_reset'    : True,
  }

  def __init__( s, m ):
    if isinstance( m, Placeholder ):
      s.fill_missing( m )
      s.check( m )
    else:
      s.is_valid = False

  def fill_missing( s, m ):
    for config, value in PlaceholderConfigs.Configs.items():
      if hasattr( m, f'placeholder_{config}' ):
        setattr( s, config, getattr( m, f'placeholder_{config}' ) )
      else:
        setattr( s, config, value )

    if not s.top_module:
      s.top_module = get_component_unique_name( m )
    if not s.verilog_name:
      s.verilog_name = f'placeholder_{s.top_module}'
    if not s.src_file:
      s.src_file = f'{s.top_module}.v'
    if not s.pickled_file:
      s.pickled_file = f'placeholder_{s.top_module}.v'

  def check( s, m ):
    assert s.file_type == 'SVerilog', \
        'only Verilog/SystemVerilog external files are currently supported!'

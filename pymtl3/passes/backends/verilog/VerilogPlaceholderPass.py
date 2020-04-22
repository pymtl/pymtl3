#=========================================================================
# VerilogPlaceholderPass.py
#=========================================================================
# For each placeholder in the component hierarchy, set up default values,
# check if all configs are valid, and pickle the specified Verilog
# source files.
#
# Author : Peitian Pan
# Date   : Jan 27, 2020

import os
import re
import sys
from textwrap import dedent

from pymtl3 import Placeholder
from pymtl3.passes.backends.verilog.util.utility import (
    gen_mapped_ports,
    get_component_unique_name,
)
from pymtl3.passes.backends.verilog.VerilogPlaceholderConfigs import (
    VerilogPlaceholderConfigs,
)
from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PlaceholderConfigs import expand
from pymtl3.passes.PlaceholderPass import PlaceholderPass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRGetter
from pymtl3.passes.rtlir import RTLIRType as rt


class VerilogPlaceholderPass( PlaceholderPass ):

  def visit_placeholder( s, m ):
    irepr = RTLIRGetter(cache=False).get_component_ifc_rtlir( m )

    s.setup_default_configs( m, irepr )

    # after the previous setup step, placeholder `m` is guaranteed to have
    # config_placeholder attribute.
    if m.config_placeholder.is_valid:
      s.check_valid( m, m.config_placeholder, irepr )
      s.pickle( m, m.config_placeholder, irepr )

  def setup_default_configs( s, m, irepr ):
    if not hasattr( m, 'config_placeholder' ):
      m.config_placeholder = VerilogPlaceholderConfigs()

    cfg = m.config_placeholder

    if cfg.is_valid:
      # If top_module is unspecified, infer it from the component and its
      # parameters. Note we need to make sure the infered top_module matches
      # the default translation result.
      if not cfg.top_module:
        cfg.top_module = irepr.get_name()
        cfg.unique_top_module = get_component_unique_name( irepr )
        # if m.get_parent_object() is None:
        #   # This is a top level module -- use the module name without the
        #   # parameters because we will generate a different wrapper for top!
        #   cfg.top_module = irepr.get_name()
        # else:
        #   # Otherwise use the full name
        #   cfg.top_module = get_component_unique_name( irepr )
      else:
        cfg.unique_top_module = cfg.top_module

      # Only try to infer the name of Verilog source file if both
      # flist and the source file are not specified.
      if not cfg.src_file and not cfg.v_flist:
        cfg.src_file = f"{cfg.top_module}.v"

  def check_valid( s, m, cfg, irepr ):
    pmap, src, flist, include = \
        cfg.port_map, cfg.src_file, cfg.v_flist, cfg.v_include

    # Check params
    for param_name, value in cfg.params.items():
      if not isinstance( value, int ):
        raise InvalidPassOptionValue("params", cfg.params, cfg.PassName,
            f"non-integer parameter {param_name} is not supported yet!")

    # Check port map

    # TODO: this should be based on RTLIR
    # unmapped_unpacked_ports = gen_unpacked_ports( irepr )
    # unmapped_port_names = list(map(lambda x: x[0], list(unmapped_unpacked_ports)))
    # for name in pmap.keys():
    #   if name not in unmapped_port_names:
    #     raise InvalidPassOptionValue("port_map", pmap, cfg.PassName,
    #       f"Port {name} does not exist in component {irepr.get_name()}!")

    for name in pmap.keys():
      try:
        eval(f'm.{name}')
      except:
        raise InvalidPassOptionValue("port_map", pmap, cfg.PassName,
          f"Port {name} does not exist in component {irepr.get_name()}!")

    # Check src_file
    if cfg.src_file and not os.path.isfile(expand(cfg.src_file)):
      raise InvalidPassOptionValue("src_file", cfg.src_file, cfg.PassName,
          'src_file should be a file path!')

    if cfg.v_flist:
      raise InvalidPassOptionValue("v_flist", cfg.v_flist, cfg.PassName,
          'Placeholders backed by Verilog flist are not supported yet!')

    # Check v_flist
    if cfg.v_flist and not os.path.isfile(expand(cfg.v_flist)):
      raise InvalidPassOptionValue("v_flist", cfg.v_flist, cfg.PassName,
          'v_flist should be a file path!')

    # Check v_include
    if cfg.v_include:
      for include in cfg.v_include:
        if not os.path.isdir(expand(include)):
          raise InvalidPassOptionValue("v_include", cfg.v_include, cfg.PassName,
              'v_include should be an array of dir paths!')

  def pickle( s, m, cfg, irepr ):
    # In the namespace cfg:
    #   pickled_dependency_file: path to the pickled Verilog dependency file
    #   pickled_wrapper_file: path to the pickled Verilog wrapper file
    #   pickled_top_module:  name of the top module in the pickled Verilog

    pickled_dependency_file = f'{cfg.unique_top_module}_pickled_dependency.v'
    pickled_wrapper_file = f'{cfg.unique_top_module}_pickled_wrapper.v'
    pickled_top_module = f'{cfg.unique_top_module}_wrapper'

    orig_comp_name       = get_component_unique_name( irepr )
    pickle_dependency    = s._get_v_lib_files( m, cfg, irepr )
    pickle_dependency   += s._get_dependent_verilog_modules( m, cfg, irepr )
    pickle_wrapper, tplt = s._gen_verilog_wrapper( m, cfg, irepr, pickled_top_module )
    def_symbol           = pickled_top_module.upper()

    # The directives are there to prevent potential duplicated definitions
    # pickle_template = dedent(
    #     '''\
    #         // This is a wrapper module that wraps PyMTL placeholder {orig_comp_name}
    #         // This file was generated by PyMTL VerilogPlaceholderPass
    #         `ifndef {def_symbol}
    #         `define {def_symbol}

    #         {pickle_dependency}
    #         {pickle_wrapper}

    #         `endif /* {def_symbol} */
    #     '''
    # )

    cfg.pickled_dependency_file  = pickled_dependency_file
    cfg.pickled_wrapper_file     = pickled_wrapper_file
    cfg.pickled_top_module       = pickled_top_module
    cfg.pickled_wrapper_template = tplt
    cfg.pickled_orig_file        = cfg.src_file
    cfg.def_symbol = def_symbol
    cfg.orig_comp_name = orig_comp_name
    cfg.pickle_dependency = pickle_dependency

    with open( pickled_dependency_file, 'w' ) as fd:
      fd.write( pickle_dependency )

    with open( pickled_wrapper_file, 'w' ) as fd:
      fd.write( pickle_wrapper )

  def _get_v_lib_files( s, m, cfg, irepr ):
    orig_comp_name = get_component_unique_name( irepr )
    tplt = dedent(
        """\
            // The source code below are included because they are specified
            // as the v_lib Verilog placeholder option of component {orig_comp_name}.

            // If you get a duplicated def error from files included below, please
            // make sure they are included either through the v_lib option or the
            // explicit `include statement in the Verilog source code -- if they
            // appear in both then they will be included twice!

            {v_libs}
            // End of all v_lib files for component {orig_comp_name}

        """
    )
    per_file_tplt = dedent(
        """\
            // File {filename} from v_lib option of component {orig_comp_name}
            {file_content}
        """
    )
    v_libs = []

    for filename in cfg.v_libs:
      with open(filename) as fd:
        file_content = fd.read()
        v_libs.append(per_file_tplt.format(**locals()))

    v_libs = ''.join(v_libs)
    return tplt.format(**locals())

  def _get_dependent_verilog_modules( s, m, cfg, irepr ):
    return s._import_sources( cfg, [cfg.src_file] )

  def _gen_verilog_wrapper( s, m, cfg, irepr, pickled_top_module ):
    rtlir_ports = gen_mapped_ports( m, cfg.port_map, cfg.has_clk, cfg.has_reset )

    all_port_names = list(map(lambda x: x[1], rtlir_ports))

    if not cfg.params:
      parameters = irepr.get_params()
    else:
      parameters = cfg.params.items()

    # Port definitions of wrapper
    ports = []
    for idx, (_, name, p, _) in enumerate(rtlir_ports):
      if name:
        if isinstance(p, rt.Array):
          n_dim = p.get_dim_sizes()
          s_dim = ''.join([f'[0:{idx-1}]' for idx in n_dim])
          p = p.get_next_dim_type()
        else:
          s_dim = ''
        ports.append(
            f"  {p.get_direction()} logic [{p.get_dtype().get_length()}-1:0]"\
            f" {name} {s_dim}{'' if idx == len(rtlir_ports)-1 else ','}"
        )

    # The wrapper has to have an unused clk port to make verilator
    # VCD tracing work.
    if 'clk' not in all_port_names:
      ports.insert( 0, '  input logic clk,' )

    if 'reset' not in all_port_names:
      ports.insert( 0, '  input logic reset,' )

    # Parameters passed to the module to be parametrized
    params = [
      f"    .{param}( {val} ){'' if idx == len(parameters)-1 else ','}"\
      for idx, (param, val) in enumerate(parameters)
    ]

    # Connections between top module and inner module
    connect_ports = [
      f"    .{name}( {name} ){'' if idx == len(rtlir_ports)-1 else ','}"\
      for idx, (_, name, p, _) in enumerate(rtlir_ports) if name
    ]

    lines = [
      f"module {pickled_top_module}",
      "(",
    ] + ports + [
      ");",
      f"  {cfg.top_module}",
      "  #(",
    ] + params + [
      "  ) v",
      "  (",
    ] + connect_ports + [
      "  );",
      "endmodule",
    ]

    template_lines = [
      "module {top_module_name}",
      "(",
    ] + ports + [
      ");",
      f"  {cfg.top_module}",
      "  #(",
    ] + params + [
      "  ) v",
      "  (",
    ] + connect_ports + [
      "  );",
      "endmodule",
    ]

    return '\n'.join( line for line in lines ), '\n'.join( line for line in template_lines )

  #-----------------------------------------------------------------------
  # import_sources
  #-----------------------------------------------------------------------
  # The right way to do this is to use a recursive function like I have
  # done below. This ensures that files are inserted into the output stream
  # in the correct order. -cbatten

  # Regex to extract verilog filenames from `include statements

  _include_re = re.compile( r'"(?P<filename>[\w/\.-]*)"' )

  def _output_verilog_file( s, include_path, verilog_file ):
    code = ""
    with open(verilog_file) as fp:

      short_verilog_file = verilog_file
      if verilog_file.startswith( include_path+"/" ):
        short_verilog_file = verilog_file[len(include_path+"/"):]

      code += '`line 1 "{}" 0\n'.format( short_verilog_file )

      line_num = 0
      for line in fp:
        line_num += 1
        if '`include' in line:
          filename = s._include_re.search( line ).group( 'filename' )
          fullname = os.path.join( include_path, filename )
          code += s._output_verilog_file( include_path, fullname )
          code += '\n'
          code += '`line {} "{}" 0\n'.format( line_num+1, short_verilog_file )
        else:
          code += line
    return code

  def _import_sources( s, cfg, source_list ):
    """Import Verilog source from all Verilog files source_list, as well
    as any source files specified by `include within those files.
    """

    code = ""

    if not source_list:
      return

    # We will use the first verilog file to find the root of PyMTL project

    first_verilog_file = source_list[0]

    # All verilog includes are relative to the root of the PyMTL project.
    # We identify the root of the PyMTL project by looking for the special
    # .pymtl_sim_root file.

    _path = os.path.dirname( first_verilog_file )
    special_file_found = False
    include_path = os.path.dirname( os.path.abspath( first_verilog_file ) )
    while include_path != "/":
      if os.path.exists( include_path + os.path.sep + ".pymtl_sim_root" ):
        special_file_found = True
        sys.path.insert(0,include_path)
        break
      include_path = os.path.dirname(include_path)

    # Append the user-defined include path to include_path
    # NOTE: the current pickler only supports one include path. If v_include
    # config is present, use it instead.

    if cfg.v_include:
      if len(cfg.v_include) != 1:
        raise InvalidPassOptionValue("v_include", cfg.v_include, cfg.PassName,
            'the current pickler only supports one user-defined v_include path...')
      include_path = cfg.v_include[0]

    # If we could not find the special .pymtl-python-path file, then assume
    # the include directory is the same as the directory that contains the
    # first verilog file.

    if not special_file_found and not cfg.v_include:
      include_path = os.path.dirname( os.path.abspath( first_verilog_file ) )

    # Regex to extract verilog filenames from `include statements

    s._include_re = re.compile( r'"(?P<filename>[\w/\.-]*)"' )

    # Iterate through all source files and add any `include files to the
    # list of source files to import.

    for source in source_list:
      code += s._output_verilog_file( include_path, source )

    return code

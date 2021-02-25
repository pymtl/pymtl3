#=========================================================================
# VerilogPlaceholderPass.py
#=========================================================================
# For each placeholder in the component hierarchy, set up default values,
# check if all configs are valid, and pickle the specified Verilog
# source files.
#
# Author : Peitian Pan
# Date   : Jan 27, 2020
import configparser
import inspect
import os
import re
import sys
from textwrap import dedent

from pymtl3 import MetadataKey
from pymtl3.passes.backends.verilog.util.utility import (
    gen_mapped_ports,
    get_component_unique_name,
)
from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PlaceholderConfigs import expand
from pymtl3.passes.PlaceholderPass import PlaceholderPass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRGetter
from pymtl3.passes.rtlir import RTLIRType as rt


class VerilogPlaceholderPass( PlaceholderPass ):

  # Placeholder pass public pass data

  #: A dict that maps the module parameters to their values.
  #:
  #: Type: ``{ str : int }``; input
  #:
  #: Default value: ``{}``
  params     = MetadataKey(dict)

  #: A dict that maps the PyMTL port name to the external source port name.
  #:
  #: Type: ``{ port : str }``; input
  #:
  #: Default value: ``{}``
  port_map   = MetadataKey(dict)

  #: Top level module name in the external source file.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: PyMTL component class name
  top_module = MetadataKey(str)

  #: Path to the external source file.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: <top_module>.v
  src_file   = MetadataKey(str)

  #: List of Verilog source file paths.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: []
  v_flist    = MetadataKey(list)

  #: List of Verilog library file paths. These files will be added to the
  #: beginning of the pikcling result.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: []
  v_libs     = MetadataKey(list)

  #: List of Verilog include directory paths.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: []
  v_include  = MetadataKey(list)

  #: Separator string used by name-mangling of interfaces and arrays.
  #: For example, with the default value, ``s.ifc.msg`` will be mangled to ``ifc_msg``.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``'_'``
  separator  = MetadataKey(str)

  @staticmethod
  def get_placeholder_config():
    from pymtl3.passes.backends.verilog.VerilogPlaceholderConfigs import (
        VerilogPlaceholderConfigs,
    )
    return VerilogPlaceholderConfigs

  # Override
  def visit_placeholder( s, m ):
    c = s.__class__
    super().visit_placeholder( m )
    irepr = RTLIRGetter(cache=False).get_component_ifc_rtlir( m )

    s.setup_default_configs( m, irepr )
    cfg = m.get_metadata( c.placeholder_config )

    if cfg.enable:
      s.check_valid( m, cfg, irepr )
      s.pickle( m, cfg, irepr )

  def setup_default_configs( s, m, irepr ):
    c = s.__class__
    cfg = m.get_metadata( c.placeholder_config )

    if cfg.enable:
      # If top_module is unspecified, infer it from the component and its
      # parameters. Note we need to make sure the infered top_module matches
      # the default translation result.
      if not cfg.top_module:
        cfg.top_module = irepr.get_name()

      # If the placeholder has parameters, use the mangled unique component
      # name. Otherwise use {class_name}_noparam to avoid duplicated defs.
      has_params = bool( irepr.get_params() ) or bool( cfg.params )
      if has_params:
        cfg.pickled_top_module = get_component_unique_name( irepr )
      else:
        cfg.pickled_top_module = f"{irepr.get_name()}_noparam"

      # Only try to infer the name of Verilog source file if both
      # flist and the source file are not specified.
      if not cfg.src_file and not cfg.v_flist:
        parent_dir = os.path.dirname(inspect.getfile(m.__class__))
        cfg.src_file = f"{parent_dir}{os.sep}{cfg.top_module}.v"

      # What is the original file/flist of the pickled source file?
      if cfg.src_file:
        cfg.pickled_orig_file = cfg.src_file
      else:
        cfg.pickled_orig_file = cfg.v_flist

      # The unique placeholder name
      cfg.orig_comp_name = get_component_unique_name( irepr )

      # The `ifdef dependency guard is a function of the placeholder
      # class name
      cfg.dependency_guard_symbol = m.__class__.__name__.upper()

      # The `ifdef placeholder guard is a function of the placeholder
      # wrapper name
      cfg.wrapper_guard_symbol = cfg.pickled_top_module.upper()

      # Scan through src_file to check for clk and reset
      if cfg.is_default('has_clk'):
        cfg.has_clk = s._has_pin(cfg.src_file, 'input', 1, 'clk')

      if cfg.is_default('has_reset'):
        cfg.has_reset = s._has_pin(cfg.src_file, 'input', 1, 'reset')

      # By default, the separator of placeholders is single underscore
      cfg.separator = '_'

      # Look for pymtl.ini starting from the directory that includes the def
      # of class m.__class__
      auto_prefix = s._get_auto_prefix( m )

      # Apply auto_prefix to top_module
      cfg.top_module = auto_prefix + cfg.top_module

  def check_valid( s, m, cfg, irepr ):
    pmap, src, flist, include = \
        cfg.port_map, cfg.src_file, cfg.v_flist, cfg.v_include

    # Check params
    for param_name, value in cfg.params.items():
      if not isinstance( value, int ):
        raise InvalidPassOptionValue("params", cfg.params, cfg.Pass.__name__,
            f"non-integer parameter {param_name} is not supported yet!")

    # Check port map
    # TODO: this should be based on RTLIR
    for port in pmap.keys():
      if port.get_host_component() is not m:
        raise InvalidPassOptionValue("port_map", pmap, cfg.Pass.__name__,
          f"Port {port} does not exist in component {irepr.get_name()}!")

    # Check src_file
    if cfg.src_file and not os.path.isfile(expand(cfg.src_file)):
      raise InvalidPassOptionValue("src_file", cfg.src_file, cfg.Pass.__name__,
          'src_file should be a file path!')

    if cfg.v_flist:
      raise InvalidPassOptionValue("v_flist", cfg.v_flist, cfg.Pass.__name__,
          'Placeholders backed by Verilog flist are not supported yet!')

    # Check v_flist
    if cfg.v_flist and not os.path.isfile(expand(cfg.v_flist)):
      raise InvalidPassOptionValue("v_flist", cfg.v_flist, cfg.Pass.__name__,
          'v_flist should be a file path!')

    # Check v_include
    if cfg.v_include:
      for include in cfg.v_include:
        if not os.path.isdir(expand(include)):
          raise InvalidPassOptionValue("v_include", cfg.v_include, cfg.Pass.__name__,
              'v_include should be an array of dir paths!')

    # Check if the top module name appears in the file
    if cfg.src_file:
      found = False
      with open(cfg.src_file) as src_file:
        for line in src_file.readlines():
          if cfg.top_module in line:
            found = True
            break
      if not found:
        raise InvalidPassOptionValue("top_module", cfg.top_module, cfg.Pass.__name__,
            f'cannot find top module {cfg.top_module} in source file {cfg.src_file}.\n'
            f'Please make sure you have specified the correct top module name through '
            f'the VerilogPlaceholderPass.top_module pass data name!')

  def pickle( s, m, cfg, irepr ):
    pickled_dependency    = s._get_v_lib_files( m, cfg, irepr )
    pickled_dependency   += s._get_dependent_verilog_modules( m, cfg, irepr )
    pickled_wrapper, tplt = s._gen_verilog_wrapper( m, cfg, irepr )

    pickled_dependency_source = (
        f"//***********************************************************\n"
        f"// Pickled source file of placeholder {cfg.orig_comp_name}\n"
        f"//***********************************************************\n"
        f"\n"
        f"//-----------------------------------------------------------\n"
        f"// Dependency of placeholder {m.__class__.__name__}\n"
        f"//-----------------------------------------------------------\n"
        f"\n"
        f"`ifndef {cfg.dependency_guard_symbol}\n"
        f"`define {cfg.dependency_guard_symbol}\n"
        f"\n"
        f"{pickled_dependency}"
        f"\n"
        f"`endif /* {cfg.dependency_guard_symbol} */\n"
    )

    pickled_wrapper_source_tplt = (
        f"\n"
        f"//-----------------------------------------------------------\n"
        f"// Wrapper of placeholder {cfg.orig_comp_name}\n"
        f"//-----------------------------------------------------------\n"
        f"\n"
        f"`ifndef {cfg.wrapper_guard_symbol}\n"
        f"`define {cfg.wrapper_guard_symbol}\n"
        f"\n"
        f"{{pickled_wrapper}}\n"
        f"\n"
        f"`endif /* {cfg.wrapper_guard_symbol} */\n"
    )

    pickled_wrapper_source = pickled_wrapper_source_tplt.format(pickled_wrapper=pickled_wrapper)
    pickled_source = pickled_dependency_source + pickled_wrapper_source

    cfg.pickled_wrapper_template = pickled_wrapper_source_tplt.format(pickled_wrapper=tplt)
    cfg.pickled_wrapper_nlines   = len(pickled_wrapper_source.split('\n'))-1

    cfg.pickled_source = pickled_source

  def _get_v_lib_files( s, m, cfg, irepr ):
    orig_comp_name = cfg.orig_comp_name
    tplt = dedent(
        """\
            // The source code below are included because they are specified
            // as the v_libs Verilog placeholder option of component {orig_comp_name}.

            // If you get a duplicated def error from files included below, please
            // make sure they are included either through the v_libs option or the
            // explicit `include statement in the Verilog source code -- if they
            // appear in both then they will be included twice!

            {v_libs}
            // End of all v_libs files for component {orig_comp_name}

        """
    )
    if cfg.v_libs:
      v_libs = s._import_sources( cfg, cfg.v_libs )
    else:
      v_libs = ""

    return tplt.format(**locals())

  def _get_dependent_verilog_modules( s, m, cfg, irepr ):
    return s._import_sources( cfg, [cfg.src_file] )

  def _gen_verilog_wrapper( s, m, cfg, irepr ):
    # By default use single underscore as separator
    rtlir_ports = gen_mapped_ports( m, cfg.port_map, cfg.has_clk, cfg.has_reset, '_' )

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
      f"module {cfg.pickled_top_module}",
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
  # _has_pin
  #-----------------------------------------------------------------------

  def _has_pin( s, src_file, direction, nbits, pin ):
    trim = lambda s: ''.join(s.split())
    targets = [
        f'{direction}logic[{nbits-1}:0]{pin}',
        f'{direction}[{nbits-1}:0]{pin}'
    ]
    if nbits == 1:
      targets.append( f'{direction}logic{pin}' )
      targets.append( f'{direction}{pin}' )
    try:
      with open(src_file) as fd:
        for line in fd.readlines():
          if any(map(lambda x: x in trim(line), targets)):
            return True
      return False
    except OSError:
      return False

  #-----------------------------------------------------------------------
  # _get_auto_prefix
  #-----------------------------------------------------------------------

  def _get_auto_prefix( s, m ):
    parent_dir = cwd = os.path.dirname(inspect.getfile(m.__class__))
    while cwd != '/':
      if os.path.exists(f"{cwd}{os.path.sep}pymtl.ini"):
        break
      cwd = os.path.dirname(cwd)

    if cwd == '/': return ''

    pymtl_config = configparser.ConfigParser()
    pymtl_config.read(f"{cwd}{os.path.sep}pymtl.ini")

    if 'placeholder' in pymtl_config and \
       'auto_prefix' in pymtl_config['placeholder'] and \
       pymtl_config.getboolean( 'placeholder', 'auto_prefix' ):
      return f"{os.path.basename(parent_dir)}_"
    else:
      return ''

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
          re_result = s._include_re.search( line )
        else:
          re_result = None

        if re_result:
          filename = re_result.group( 'filename' )
          fullname = os.path.join( include_path, filename )
          code += s._output_verilog_file( include_path, fullname )
          code += '\n'
          code += '`line {} "{}" 0\n'.format( line_num+1, short_verilog_file )
        else:
          code += line
    return code

  def _import_sources( s, cfg, source_list ):
    # Import Verilog source from all Verilog files source_list. This includes
    # any source files specified by `include within those files.

    code = ""

    if not source_list:
      return

    # We will use the first verilog file to find the root of PyMTL project

    first_verilog_file = source_list[0]

    # All verilog includes are relative to the root of the PyMTL project.
    # We identify the root of the PyMTL project by looking for the special
    # pymtl.ini file.

    _path = os.path.dirname( first_verilog_file )
    special_file_found = False
    include_path = os.path.dirname( os.path.abspath( first_verilog_file ) )
    while include_path != "/":
      if os.path.exists( include_path + os.path.sep + "pymtl.ini" ):
        special_file_found = True
        sys.path.insert(0,include_path)
        break
      include_path = os.path.dirname(include_path)

    # Append the user-defined include path to include_path
    # NOTE: the current pickler only supports one include path. If v_include
    # config is present, use it instead.

    if cfg.v_include:
      if len(cfg.v_include) != 1:
        raise InvalidPassOptionValue("v_include", cfg.v_include, cfg.Pass.__name__,
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

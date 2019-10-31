#=========================================================================
# ImportConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration class of SystemVerilog import pass."""

import os
import subprocess
from textwrap import fill, indent

from pymtl3.dsl import Placeholder
from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PassConfigs import BasePassConfigs
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog.util.utility import expand, get_component_unique_name


class ImportConfigs( BasePassConfigs ):

  def __init__( s, **kwargs ):
    super().__init__( **kwargs )

    s.set_checkers(
        ['import_', 'enable_assert', 'vl_W_lint', 'vl_W_style', 'vl_W_fatal',
         'vl_trace', 'verbose', 'has_clk', 'has_reset', 'coverage'],
        lambda v: isinstance(v, bool),
        "expects a boolean")
    s.set_checkers(
        ['c_flags', 'ld_flags', 'ld_libs'],
        lambda v: isinstance(v, str),
        "expects a string")
    s.set_checkers(
        ['vl_unroll_count', 'vl_unroll_stmts'],
        lambda v: isinstance(v, int) and v >= 0,
        "expects an integer >= 0")
    s.set_checker(
        "top_module",
        lambda v: isinstance(v, str) and v,
        "expects a non-empty string")
    s.set_checker( "port_map", lambda v: isinstance(v, dict), "expects a dict")
    s.set_checker(
        "vl_src",
        lambda v: isinstance(v, str) and os.path.isfile(expand(v)) or \
                  s.get_option("vl_flist"),
        "vl_src should be a path to a file when vl_flist is empty")
    s.set_checker(
        "vl_flist",
        lambda v: isinstance(v, str) and os.path.isfile(expand(v)) or v == "",
        "expects a path to a file")
    s.set_checker(
        "vl_Wno_list",
        lambda v: isinstance(v, list) and all(w in s.Warnings for w in v),
        "expects a list of warnings")
    s.set_checker(
        "vl_include",
        lambda v: isinstance(v, list) and \
                  all(os.path.isdir(expand(p)) for p in v),
        "expects a path to directory")
    s.set_checker(
        "vl_trace_timescale",
        lambda v: isinstance(v, str) and len(v) > 2 and v[-1] == 's' and \
                  v[-2] in ['p', 'n', 'u', 'm'] and \
                  all(c.isdigit() for c in v[:-2]),
        "expects a timescale string")
    s.set_checker(
        "vl_trace_cycle_time",
        lambda v: isinstance(v, int) and (v % 2) == 0,
        "expects an integer `n` such that `n`*`vl_trace_timescale` is the cycle time")
    s.set_checker(
        "vl_mk_dir",
        lambda v: isinstance(v, str),
        "expects a path to directory")
    s.set_checker(
        "c_include_path",
        lambda v: isinstance(v, list) and \
                  all(os.path.isdir(expand(p)) for p in v),
        "expects a list of paths to directories")
    s.set_checker(
        "c_srcs",
        lambda v: isinstance(v, list) and \
                  all(os.path.isfile(expand(p)) for p in v),
        "expects a list of paths to files")

  Warnings = [
      'ALWCOMBORDER', 'ASSIGNIN', 'ASSIGNDLY', 'BLKANDNBLK', 'BLKSEQ',
      'BLKLOOPINIT', 'BSSPACE', 'CASEINCOMPLETE', 'CASEOVERLAP',
      'CASEX', 'CASEWITHX', 'CDCRSTLOGIC', 'CLKDATA', 'CMPCONST',
      'COLONPLUS', 'COMBDLY', 'CONTASSREG', 'DECLFILENAME', 'DEFPARAM',
      'DETECTARRAY', 'ENDLABEL', 'GENCLK', 'IFDEPTH', 'IGNOREDRETURN',
      'IMPERFECTSCH', 'IMPLICIT', 'IMPORTSTAR', 'IMPURE', 'INCABSPATH',
      'INFINITELOOP', 'INITIALDLY', 'LITENDIAN', 'MODDUP', 'MULTIDRIVEN',
      'MULTITOP', 'PINCONNECTEMPTY', 'PINMISSING', 'PINNOCONNECT',
      'PROCASSWIRE', 'REALCVT', 'REDEFMACRO', 'SELRANGE', 'STMTDLY',
      'SYMRSVDWORD', 'SYNCASYNCNET', 'TASKNSVAR', 'TICKCOUNT', 'UNDRIVEN',
      'UNOPT', 'UNOPTFLAT', 'UNOPTTHREADS', 'UNPACKED', 'UNSIGNED', 'UNUSED',
      'USERINFO', 'USERWARN', 'USERERROR', 'USERFATAL', 'VARHIDDEN', 'WIDTH',
      'WIDTHCONCAT'
    ]

  Options = {
      # Import enable switch
      "import_" : True,

      # Enable verbose mode?
      "verbose" : False,

      # Port name mapping
      # Map pymtl names to Verilog names
      "port_map" : {},

      # Verilator code generation options
      # These options will be passed to verilator to generate the C simulator.
      # By default, verilator is called with `--cc`.

      # --top-module
      # Expects the name of the top component;
      # "" to use name of the current component to be imported
      "top_module" : "",

      # Does the module to be imported has `clk` port?
      "has_clk" : True,

      # Does the module to be imported has `reset` port?
      "has_reset" : True,

      # Expects path of the file that contains the top module to be verilated
      # "" to use "<top_module>.sv"
      "vl_src" : "",

      # --Mdir
      # Expects the path of Makefile output directory;
      # "" to use `obj_dir_<top_module>`
      "vl_mk_dir" : "",

      # -f
      # Expects the path to the flist file; "" to disable this option
      "vl_flist" : "",

      # -I ( alias of -y and +incdir+ )
      # Expects a list of include paths; [] to disable this option
      "vl_include" : [],

      # --assert
      # Expects a boolean value
      "enable_assert" : True,

      # Verilator optimization options

      # -O0/3
      # Expects a non-negative integer
      # Currently only support 0 (disable opt) and 3 (highest effort opt)
      "vl_opt_level" : 3,

      # --unroll-count
      # Expects a non-negative integer
      # 0 to disable this option
      "vl_unroll_count" : 1000000,

      # --unroll-stmts
      # Expects a non-negative integer
      # 0 to disable this option
      "vl_unroll_stmts" : 1000000,

      # Verilator warning-related options

      # False to disable the warnings, True to enable
      "vl_W_lint" : True,
      "vl_W_style" : True,
      "vl_W_fatal" : True,

      # Un-warn all warnings in the given list; [] to disable this option
      # The given list should only include strings that appear in `Warnings`
      "vl_Wno_list" : [],

      # Verilator misc options

      # --trace
      # Expects a boolean value
      "vl_trace" : False,

      # Passed to verilator tracing function
      "vl_trace_timescale" : "10ps",

      # `vl_trace_cycle_time`*`vl_trace_timescale` is the cycle time of the
      # PyMTL clock that appears in the generated VCD
      # With the default options, the frequency of PyMTL clock is 1GHz
      "vl_trace_cycle_time" : 100,

      # C-compilation options
      # These options will be passed to the C compiler to create a shared lib.

      # Additional flags to be passed to the C compiler.
      # By default, CC is called with `-O0 -fPIC -shared`.
      # "" to disable this option
      "c_flags" : "",

      # Additional include search path of the C compiler.
      # [] to disable this option
      "c_include_path" : [],

      # Additional C source files passed to the C compiler.
      # [] to compile verilator generated files only.
      "c_srcs" : [],

      # `LDLIBS` will be listed after the primary target file whereas
      # `LDFLAGS` will be listed before.

      # We enforce the GNU makefile implicit rule that `LDFLAGS` should only
      # include non-library linker flags such as `-L`.
      "ld_flags" : "",

      # We enforce the GNU makefile implicit rule that `LDLIBS` should only
      # include library linker flags/names such as `-lfoo`.
      "ld_libs" : "",

      # Enable all verilator coverage
      "coverage" : False,

      # Enable all verilator coverage
      "line_coverage" : False,

      # Enable all verilator coverage
      "toggle_coverage" : False,
    }

  PassName = 'sverilog.ImportPass'

  #-----------------------------------------------------------------------
  # Public APIs
  #-----------------------------------------------------------------------

  def create_vl_cmd( s ):
    top_module  =  f"--top-module {s.get_top_module()}"
    src         = s.get_option("vl_src")
    mk_dir      = f"--Mdir {s.get_option('vl_mk_dir')}"
    flist       = "" if s.is_default("vl_flist") else \
                  f"-f {s.get_option('vl_flist')}"
    include     = "" if s.is_default("vl_include") else \
                  " ".join("-I" + path for path in s.get_option("vl_include"))
    en_assert   = "--assert" if s.is_default("enable_assert") else ""
    opt_level   = "-O3" if s.is_default("vl_opt_level") else "-O0"
    loop_unroll = "" if s.get_option("vl_unroll_count") == 0 else \
                  f"--unroll-count {s.get_option('vl_unroll_count')}"
    stmt_unroll = "" if s.get_option("vl_unroll_stmts") == 0 else \
                  f"--unroll-stmts {s.get_option('vl_unroll_stmts')}"
    trace       = "" if s.is_default("vl_trace") else "--trace"
    coverage    = "--coverage" if s.get_option("coverage") else ""
    line_cov    = "--coverage-line" if s.get_option("line_coverage") else ""
    toggle_cov  = "--coverage-toggle" if s.get_option("toggle_coverage") else ""
    warnings    = s.create_vl_warning_cmd()

    all_opts = [
      top_module, mk_dir, include, en_assert, opt_level, loop_unroll,
      stmt_unroll, trace, warnings, flist, src, coverage, 
      line_cov, toggle_cov,
    ]

    return f"verilator --cc {' '.join(opt for opt in all_opts if opt)}"

  def create_cc_cmd( s ):
    c_flags = "-O0 -fPIC -shared" + \
             ("" if s.is_default("c_flags") else f" {s.get_option('c_flags')}")
    c_include_path = " ".join("-I"+p for p in s.get_all_includes() if p)
    out_file = s.get_shared_lib_path()
    c_src_files = " ".join(s.get_c_src_files())
    ld_flags = s.get_option("ld_flags")
    ld_libs = s.get_option("ld_libs")
    coverage = "-DVM_COVERAGE" if s.get_option("coverage") or \
                                  s.get_option("line_coverage") or \
                                  s.get_option("toggle_coverage") else ""
    return f"g++ {c_flags} {c_include_path} {ld_flags}"\
           f" -o {out_file} {c_src_files} {ld_libs} {coverage}"

  def fill_missing( s, m ):
    rtype = get_component_ifc_rtlir(m)
    s.v_param = rtype.get_params()
    s.is_param_wrapper = isinstance(m, Placeholder) and s.v_param
    top_module = s.get_top_module()

    # Check if the keys of `port_map` are port names of `m`
    # Note that the keys can be expressions such as `ifc[0].foo` and
    # therefore we do not check if a port name of `m` is in the keys. 
    if s.get_option("port_map"):
      s.check_p_map( rtype )

    # Fill in the top module if unspecified
    # If the top-level module is not a wrapper
    if not s.is_param_wrapper:
      full_name = get_component_unique_name( rtype )
      if not top_module:
        # Default top_module is the name of component concatenated
        # with parameters
        s.set_option("top_module", full_name)

    # If the top-level module is a wrapper
    else:
      # Check if all parameters are integers
      assert all(isinstance(v[1], int) for v in s.v_param), \
          "Only support integers as parameters of Verilog modules!"

      # wrapped_module is the name of the module to be parametrized
      # top_module is the name of the new top-level module
      if top_module:
        s.wrapped_module = top_module
        s.set_option("top_module", f"{top_module}_w_params")
      else:
        # Default top_module is the name of component
        s.wrapped_module = rtype.get_name()
        s.set_option("top_module", f"{s.wrapped_module}_w_params")

    top_module = s.get_top_module()

    # Only try to infer the name of Verilog source file if both
    # flist and the source file are not specified.
    if not s.get_option("vl_src") and not s.get_option("vl_flist"):
      s.set_option("vl_src", f"{top_module}.sv")

    if not s.get_option("vl_mk_dir"):
      s.set_option("vl_mk_dir", f"obj_dir_{top_module}")

    if s.is_param_wrapper:
      # If toplevel module is a param-wrapper, `vl_src` has to be specified
      # because the file containing the wrapper will include `vl_src` for
      # the module to be parametrized.
      if not s.get_option("vl_src"):
        raise InvalidPassOptionValue(
            "vl_src", s.get_option("vl_src"), s.PassName,
            "vl_src must be specified when Placeholder is to be imported!")
      s.v_module2param = s.get_option("vl_src")
      s.set_option("vl_src", top_module+".sv")

  def has_clk( s ):
    return s.get_option( "has_clk" )

  def has_reset( s ):
    return s.get_option( "has_reset" )

  def is_import_enabled( s ):
    return s.get_option( "import_" )

  def is_top_wrapper( s ):
    return s.is_param_wrapper

  def is_vl_trace_enabled( s ):
    return s.get_option( "vl_trace" )

  def is_port_mapped( s ):
    return bool(s.get_option("port_map"))

  def get_top_module( s ):
    return s.get_option( "top_module" )

  def get_port_map( s ):
    pmap = s.get_option("port_map")
    return lambda name: pmap[name]

  def get_vl_trace_timescale( s ):
    return s.get_option( "vl_trace_timescale" )

  def get_vl_trace_half_cycle_time( s ):
    return s.get_option( "vl_trace_cycle_time" ) // 2

  def get_module_to_parametrize( s ):
    return s.wrapped_module

  def get_param_include( s ):
    return s.v_module2param

  def get_v_param( s ):
    return s.v_param

  def get_c_wrapper_path( s ):
    return f"{s.get_top_module()}_v.cpp"

  def get_py_wrapper_path( s ):
    return f"{s.get_top_module()}_v.py"

  def get_shared_lib_path( s ):
    return f"lib{s.get_top_module()}_v.so"

  def get_vl_mk_dir( s ):
    return s.get_option( "vl_mk_dir" )

  def vprint( s, msg, nspaces = 0, use_fill = False ):
    if s.get_option("verbose"):
      if use_fill:
        print(indent(fill(msg), " "*nspaces))
      else:
        print(indent(msg, " "*nspaces))

  #-----------------------------------------------------------------------
  # Internal helper methods
  #-----------------------------------------------------------------------

  def check_p_map( s, rtype ):
    """Check if each port name of `rtype` is in port map."""
    pm = s.get_option("port_map")
    all_ports = rtype.get_ports_packed()
    assert all(isinstance(p, rt.Port) and \
               isinstance(p.get_dtype(), rdt.Vector) for n, p in all_ports), \
        f"Port map option currently requires all ports of {rtype.get_name()}"\
        f" to be a single vector port."
    for name, port in all_ports:
      if name not in pm:
        raise InvalidPassOptionValue("port_map", pm, s.PassName,
          f"Port {name} of {rtype.get_name()} should be mapped to a new name!")
    if len(all_ports) != len(pm):
      raise InvalidPassOptionValue("port_map", pm, s.PassName,
        f"All ports of {rtype.get_name()} should be mapped to a new name!")

  def get_all_includes( s ):
    includes = s.get_option("c_include_path")

    # Try to obtain verilator include path either from environment variable
    # or from `pkg-config`
    vl_include_dir = os.environ.get("PYMTL_VERILATOR_INCLUDE_DIR")
    if vl_include_dir is None:
      get_dir_cmd = ["pkg-config", "--variable=includedir", "verilator"]
      try:
        vl_include_dir = \
            subprocess.check_output(get_dir_cmd, stderr = subprocess.STDOUT).strip()
        vl_include_dir = vl_include_dir.decode('ascii')
      except OSError as e:
        vl_include_dir_msg = \
"""\
Cannot locate the include directory of verilator. Please make sure either \
$PYMTL_VERILATOR_INCLUDE_DIR is set or `pkg-config` has been configured properly!
"""
        raise OSError(fill(vl_include_dir_msg)) from e

    # Add verilator include path
    s.vl_include_dir = vl_include_dir
    includes += [vl_include_dir, vl_include_dir + "/vltstd"]

    return includes

  def get_c_src_files( s ):
    srcs = s.get_option("c_srcs")
    top_module = s.get_top_module()
    vl_mk_dir = s.get_option("vl_mk_dir")
    vl_class_mk = f"{vl_mk_dir}/V{top_module}_classes.mk"

    # Add C wrapper
    srcs.append(s.get_c_wrapper_path())

    # Add files listed in class makefile
    with open(vl_class_mk, "r") as class_mk:
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_CLASSES_FAST")
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_CLASSES_SLOW")
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_SUPPORT_FAST")
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_SUPPORT_SLOW")
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, s.vl_include_dir, "VM_GLOBAL_FAST")
      srcs += s.get_srcs_from_vl_class_mk(
          class_mk, s.vl_include_dir, "VM_GLOBAL_SLOW")

    return srcs

  def get_srcs_from_vl_class_mk( s, mk, path, label ):
    """Return all files under `path` directory in `label` section of `mk`."""
    srcs, found = [], False
    mk.seek(0)
    for line in mk:
      if line.startswith(label):
        found = True
      elif found:
        if line.strip() == "":
          found = False
        else:
          file_name = line.strip()[:-2]
          srcs.append( path + "/" + file_name + ".cpp" )
    return srcs

  def create_vl_warning_cmd( s ):
    lint = "" if s.is_default("vl_W_lint") else "--Wno-lint"
    style = "" if s.is_default("vl_W_style") else "--Wno-style"
    fatal = "" if s.is_default("vl_W_fatal") else "--Wno-fatal"
    wno = " ".join(f"--Wno-{w}" for w in s.get_option("vl_Wno_list"))
    return " ".join(w for w in [lint, style, fatal, wno] if w)

  def is_default( s, opt ):
    return s.options[opt] == s.Options[opt]

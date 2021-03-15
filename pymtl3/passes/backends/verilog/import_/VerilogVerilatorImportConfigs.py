#=========================================================================
# VerilogVerilatorImportConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Verilator import pass."""

import copy
import os
import subprocess
from textwrap import fill, indent

from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PassConfigs import BasePassConfigs, Checker
from pymtl3.passes.PlaceholderConfigs import expand

from ..util.utility import get_hash_of_lean_verilog
from .VerilogVerilatorImportPass import VerilogVerilatorImportPass


class VerilogVerilatorImportConfigs( BasePassConfigs ):

  Options = {
    # Import this component?
    "enable" : False,

    # Enable verbose mode?
    "verbose" : False,

    # Trade off compilation time for fast simulation performance?
    # controls: vl_opt_level, vl_unroll_count
    "fast": False,

    # Verilator optimization options

    # Enable external line trace?
    # Once enabled, the `line_trace()` method of the imported component
    # will return a string read from the external `line_trace()` function.
    # This means your Verilog module has to have a `line_trace` function
    # that provides the line trace string which has less than 512 characters.
    # Default to False
    "vl_line_trace" : False,

    # Enable all verilator coverage
    "vl_coverage" : False,

    # Enable all verilator coverage
    "vl_line_coverage" : False,

    # Enable all verilator coverage
    "vl_toggle_coverage" : False,

    # Verilator code generation options
    # These options will be passed to verilator to generate the C simulator.
    # By default, verilator is called with `--cc`.

    # --Mdir
    # Expects the path of Makefile output directory;
    # "" to use `obj_dir_<translated_top_module>`
    "vl_mk_dir" : "",

    # --assert
    # Expects a boolean value
    "vl_enable_assert" : True,

    # Verilator warning-related options

    # False to disable the warnings, True to enable
    "vl_W_lint" : True,
    "vl_W_style" : True,
    "vl_W_fatal" : True,

    # Un-warn all warnings in the given list; [] to disable this option
    # The given list should only include strings that appear in `Warnings`
    "vl_Wno_list" : [ 'UNOPTFLAT', 'UNSIGNED', 'WIDTH' ],

    # Verilator misc options

    # What is the inital value of signals?
    # Should be one of ['zeros', 'ones', 'rand']
    "vl_xinit" : "zeros",

    # --trace
    # Expects a boolean value
    "vl_trace" : False,

    # The output filename of Verilator VCD tracing
    # default is {component_name}.verilator1
    "vl_trace_filename" : "",

    # Passed to verilator tracing function
    "vl_trace_timescale" : "10ps",

    # `vl_trace_cycle_time`*`vl_trace_timescale` is the cycle time of the
    # PyMTL clock that appears in the generated VCD
    # With the default options, the frequency of PyMTL clock is 1GHz
    "vl_trace_cycle_time" : 100,

    # Set to true to allow for on-demand VCD dumping
    "vl_trace_on_demand" : False,

    # Top level port name that is used to enable VCD dumping when
    # `vl_trace_on_demand` is True. Assuming the port is an active-high
    # enable signal.
    "vl_trace_on_demand_portname" : "",

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

    "c_flags" : "",
  }

  Checkers = {
    ("enable", "verbose", "vl_enable_assert", "vl_line_trace", "vl_W_lint", "vl_W_style",
     "vl_W_fatal", "vl_trace", "vl_coverage", "vl_line_coverage", "vl_toggle_coverage",
     "vl_trace_on_demand"):
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),

    ("c_flags", "ld_flags", "ld_libs", "vl_trace_filename", "vl_trace_on_demand_portname"):
      Checker( lambda v: isinstance(v, str),  "expects a string" ),

    "vl_Wno_list": Checker( lambda v: isinstance(v, list) and all(w in VerilogPlaceholderConfigs.Warnings for w in v),
                            "expects a list of warnings" ),

    "vl_xinit": Checker( lambda v: (v in ['zeros', 'ones', 'rand']) or isinstance(v, int),
                  "vl_xinit should be an integer or one of ['zeros', 'ones', 'rand']" ),

    "vl_trace_timescale": Checker( lambda v: isinstance(v, str) and len(v) > 2 and v[-1] == 's' and \
                                    v[-2] in ['p', 'n', 'u', 'm'] and \
                                    all(c.isdigit() for c in v[:-2]),
                                    "expects a timescale string" ),

    "vl_trace_cycle_time": Checker( lambda v: isinstance(v, int) and (v % 2) == 0,
                                    "expects an integer `n` such that `n`*`vl_trace_timescale` is the cycle time" ),

    "vl_mk_dir": Checker( lambda v: isinstance(v, str), "expects a path to directory" ),

    "c_include_path": Checker( lambda v: isinstance(v, list) and all(os.path.isdir(expand(p)) for p in v),
                                "expects a list of paths to directories" ),

    "c_srcs": Checker( lambda v: isinstance(v, list) and all(os.path.isfile(expand(p)) for p in v),
                       "expects a list of paths to files" )
  }

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
    'WIDTHCONCAT',
  ]

  Pass = VerilogVerilatorImportPass

  #---------------------------------------------------
  # Public APIs
  #---------------------------------------------------

  def setup_configs( s, m, tr_pass, ph_pass ):
    # VerilatorImportConfigs alone does not have the complete information about
    # the module to be imported. For example, we need to read from the placeholder
    # configuration to figure out the pickled file name and the top module name.
    # This method is meant to be called before calling other public APIs.

    s.translated_top_module = m.get_metadata( tr_pass.translated_top_module )
    s.translated_source_file = m.get_metadata( tr_pass.translated_filename )

    ph_cfg = m.get_metadata( ph_pass.placeholder_config )
    s.verilog_hash = get_hash_of_lean_verilog( s.translated_source_file )
    s.v_include = ph_cfg.v_include
    s.v_libs = ph_cfg.v_libs
    s.src_file = ph_cfg.src_file
    s.port_map = ph_cfg.port_map
    s.params = ph_cfg.params

    # Infer vl_line_trace by scanning through the source file
    try:
      trim = lambda s: ''.join(s.split())
      if not s.vl_line_trace:
        with open(s.src_file) as fd:
          for line in fd.readlines():
            if "`VC_TRACE_BEGIN" in trim(line):
              s.vl_line_trace = True
              break
    except OSError:
      pass

    if not s.vl_mk_dir:
      s.vl_mk_dir = f'obj_dir_{s.translated_top_module}'

  def get_vl_xinit_value( s ):
    if s.vl_xinit == 'zeros':
      return 0
    elif s.vl_xinit == 'ones':
      return 1
    elif ( s.vl_xinit == 'rand' ) or isinstance( s.vl_xinit, int ):
      return 2
    else:
      raise InvalidPassOptionValue("vl_xinit should be an int or one of 'zeros', 'ones', or 'rand'!")

  def get_vl_xinit_seed( s ):
    if isinstance( s.vl_xinit, int ):
      return s.vl_xinit
    else:
      return 0

  def get_c_wrapper_path( s ):
    return f'{s.translated_top_module}_v.cpp'

  def get_py_wrapper_path( s ):
    return f'{s.translated_top_module}_v.py'

  def get_shared_lib_path( s ):
    return f'lib{s.translated_top_module}_v.so'

  #---------------------
  # Command generation
  #---------------------

  def create_vl_cmd( s ):
    top_module  = f"--top-module {s.translated_top_module}"
    src         = s.translated_source_file
    mk_dir      = f"--Mdir {s.vl_mk_dir}"
    # flist       = "" if s.is_default("v_flist") else \
    #               f"-f {s.v_flist}"
    # We don't need this since all v_libs appear in the translation result
    # vlibs       = "" if not s.v_libs else \
    #               " ".join([f"-v {lib}" for lib in s.v_libs])
    vlibs       = ""
    include     = "" if not s.v_include else \
                  " ".join("-I" + path for path in s.v_include)
    en_assert   = "--assert" if s.vl_enable_assert else ""

    # Always verilator -O3 and unroll because -O0 may lead to this error:
    # -Info: Command Line disabled gate optimization with -Og/-O0.  This may cause ordering problems
    opt_level   = "-O3"
    loop_unroll = "--unroll-count 1000000"
    stmt_unroll = "--unroll-stmts 1000000"
    trace       = "--trace" if s.vl_trace else ""
    coverage    = "--coverage" if s.vl_coverage else ""
    line_cov    = "--coverage-line" if s.vl_line_coverage else ""
    toggle_cov  = "--coverage-toggle" if s.vl_toggle_coverage else ""
    warnings    = s._create_vl_warning_cmd()

    all_opts = [
      top_module, mk_dir, include, en_assert, opt_level, loop_unroll,
      # stmt_unroll, trace, warnings, flist, src, coverage,
      stmt_unroll, trace, warnings, src, vlibs, coverage,
      line_cov, toggle_cov,
    ]

    return f"verilator --cc {' '.join(opt for opt in all_opts if opt)}"

  def create_cc_cmd( s ):
    # Shunning: GCC has a family of optimizations on the SSA tree -ftree-***.
    # It belongs to -O1, and takes a lot of time to execute when I compile the verilated C++.
    # However, the compiled code has worse performance after applying those tree optimizations.
    # I guess it's because verilator already emits very regular and low-level code in the form of C++.
    # Also gcc -O1, -O2, -O3 result in the same compilation time after all optimization flags are turned off
    # gcc -O0 still has shorter compilation time than O1-3 with all flags off
    # My guess is that -O1 has some hidden optimization that the user cannot turn off, and -O2-3 inherit that part
    # the difference between O1-3 is just flags
    # so right now I'm using "-O1 with all options off" to get the fastest compilation time and good performance
    # !!! -fno-tree-forwprop is removed due to:
    # In file included from /usr/include/fcntl.h:290:0,
    #                   from /usr/local/share/verilator/include/verilated_vcd_c.cpp:29:
    # In function ‘int open(const char*, int, ...)’,
    #     inlined from ‘virtual bool VerilatedVcdFile::open(const string&)’ at
    # /usr/local/share/verilator/include/verilated_vcd_c.cpp:116:18:
    # /usr/include/x86_64-linux-gnu/bits/fcntl2.h:44:26: error: call to
    # ‘__open_too_many_args’ declared with attribute error: open can be called either
    # with 2 or 3 arguments, not more
    #       __open_too_many_args ();
    #       ~~~~~~~~~~~~~~~~~~~~~^~
    # /usr/include/x86_64-linux-gnu/bits/fcntl2.h:50:24: error: call to
    # ‘__open_missing_mode’ declared with attribute error: open with O_CREAT or
    # O_TMPFILE in second argument needs 3 arguments
    #     __open_missing_mode ();
    #     ~~~~~~~~~~~~~~~~~~~~^~
    # Shunning (7/7/2020): Use O0 here because O1 will lead to corruptions
    # in the CFFI-managed shared library pools. Basically what happened
    # is if we run two tests with the same component name but different
    # contents in a row, the second one uses the first library instead
    # of the second ...
    # (7/9/2020): Use -O0 by default so that normally the tests are super fast and don't corrupt cffi,
    # but when the user gives a "fast" flag, it uses -O1.
    if s.fast:
      c_flags = "-O1 -fno-guess-branch-probability -fno-reorder-blocks -fno-if-conversion -fno-if-conversion2 -fno-dce -fno-delayed-branch -fno-dse -fno-auto-inc-dec -fno-branch-count-reg -fno-combine-stack-adjustments -fno-cprop-registers -fno-forward-propagate -fno-inline-functions-called-once -fno-ipa-profile -fno-ipa-pure-const -fno-ipa-reference -fno-move-loop-invariants -fno-omit-frame-pointer -fno-split-wide-types -fno-tree-bit-ccp -fno-tree-ccp -fno-tree-ch -fno-tree-coalesce-vars -fno-tree-copy-prop -fno-tree-dce -fno-tree-dominator-opts -fno-tree-dse -fno-tree-fre -fno-tree-phiprop -fno-tree-pta -fno-tree-scev-cprop -fno-tree-sink -fno-tree-slsr -fno-tree-sra -fno-tree-ter -fno-tree-reassoc -fPIC -fno-gnu-unique -shared"
    else:
      c_flags = "-O0 -fno-guess-branch-probability -fno-reorder-blocks -fno-if-conversion -fno-if-conversion2 -fno-dce -fno-delayed-branch -fno-dse -fno-auto-inc-dec -fno-branch-count-reg -fno-combine-stack-adjustments -fno-cprop-registers -fno-forward-propagate -fno-inline-functions-called-once -fno-ipa-profile -fno-ipa-pure-const -fno-ipa-reference -fno-move-loop-invariants -fno-omit-frame-pointer -fno-split-wide-types -fno-tree-bit-ccp -fno-tree-ccp -fno-tree-ch -fno-tree-coalesce-vars -fno-tree-copy-prop -fno-tree-dce -fno-tree-dominator-opts -fno-tree-dse -fno-tree-fre -fno-tree-phiprop -fno-tree-pta -fno-tree-scev-cprop -fno-tree-sink -fno-tree-slsr -fno-tree-sra -fno-tree-ter -fno-tree-reassoc -fPIC -fno-gnu-unique -shared"

    if not s.is_default("c_flags"):
      c_flags += f" {expand(s.c_flags)}"

    c_include_path = " ".join("-I"+p for p in s._get_all_includes() if p)
    out_file = s.get_shared_lib_path()
    c_src_files = " ".join(s._get_c_src_files())
    ld_flags = expand(s.ld_flags)
    ld_libs = s.ld_libs
    coverage = "-DVM_COVERAGE" if s.vl_coverage or \
                                  s.vl_line_coverage or \
                                  s.vl_toggle_coverage else ""
    return f"g++ {c_flags} {c_include_path} {ld_flags}"\
           f" -o {out_file} {c_src_files} {ld_libs} {coverage}"

  def vprint( s, msg, nspaces = 0, use_fill = False ):
    if s.verbose:
      if use_fill:
        print(indent(fill(msg), " "*nspaces))
      else:
        print(indent(msg, " "*nspaces))

  #---------------------
  # Internal helpers
  #---------------------

  def _create_vl_warning_cmd( s ):
    lint = "" if s.is_default("vl_W_lint") else "--Wno-lint"
    style = "" if s.is_default("vl_W_style") else "--Wno-style"
    fatal = "" if s.is_default("vl_W_fatal") else "--Wno-fatal"
    wno = " ".join(f"--Wno-{w}" for w in s.vl_Wno_list)
    return " ".join(w for w in [lint, style, fatal, wno] if w)

  def _get_all_includes( s ):
    includes = copy.copy(s.c_include_path)

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

  def _get_c_src_files( s ):
    top_module = s.translated_top_module
    vl_mk_dir = s.vl_mk_dir
    vl_class_mk = f"{vl_mk_dir}/V{top_module}_classes.mk"

    # Add C wrapper
    o0 = []
    o1 = copy.copy(s.c_srcs) + [ s.get_c_wrapper_path() ]

    # Add files listed in class makefile
    with open(vl_class_mk) as class_mk:
      all_lines = class_mk.readlines()
      o1 += s._get_srcs_from_vl_class_mk( all_lines, vl_mk_dir, "VM_CLASSES_FAST")
      o1 += s._get_srcs_from_vl_class_mk( all_lines, vl_mk_dir, "VM_SUPPORT_FAST")
      o1 += s._get_srcs_from_vl_class_mk( all_lines, s.vl_include_dir, "VM_GLOBAL_FAST")

      o0 += s._get_srcs_from_vl_class_mk( all_lines, vl_mk_dir, "VM_CLASSES_SLOW")
      o0 += s._get_srcs_from_vl_class_mk( all_lines, vl_mk_dir, "VM_SUPPORT_SLOW")
      o0 += s._get_srcs_from_vl_class_mk( all_lines, s.vl_include_dir, "VM_GLOBAL_SLOW")

    with open(f"{top_module}_v__ALL_pickled.cpp", 'w') as out:

      if not s.fast:
        out.write('\n'.join( [ f'#include "{x}"' for x in o1 + o0 ]))

      else:
        if o1:
          out.write('\n'.join( [ f'#include "{x}"' for x in o1 ]))

        out.write('\n')

        if o0:
        # Apply no optimization for SLOW files
          out.write('\n#pragma GCC push_options')
          out.write('\n#pragma GCC optimize ("O0")\n')
          out.write('\n'.join( [ f'#include "{x}"' for x in o0 ]))
          out.write('\n#pragma GCC pop_options\n')

    return [ f"{top_module}_v__ALL_pickled.cpp" ]

  def _get_srcs_from_vl_class_mk( s, all_lines, path, label ):
    """Return all files under `path` directory in `label` section of `mk`."""
    srcs, found = [], False
    for line in all_lines:
      if line.startswith(label):
        found = True
      elif found:
        if line.strip() == "":
          found = False
        else:
          file_name = line.strip()[:-2]
          srcs.append( path + "/" + file_name + ".cpp" )
    return srcs

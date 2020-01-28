#=========================================================================
# VerilatorPlaceholderConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Verilator placeholders."""

import os

from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PassConfigs import Checker

from pymtl3.passes.PlaceholderConfigs import expand
from pymtl3.passes.backends.sverilog.VerilogPlaceholderConfigs import VerilogPlaceholderConfigs


class VerilatorPlaceholderConfigs( VerilogPlaceholderConfigs ):

  VerilatorOptions = {
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
    # "" to use `obj_dir_<top_module>`
    "vl_mk_dir" : "",

    # --assert
    # Expects a boolean value
    "vl_enable_assert" : True,

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

    # What is the inital value of signals?
    # Should be one of ['zeros', 'ones', 'rand']
    "vl_xinit" : "zeros",

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
  }

  VerilatorCheckers = {
    ("vl_enable_assert", "vl_line_trace", "vl_W_lint", "vl_W_style",
     "vl_W_fatal", "vl_trace", "vl_coverage", "vl_line_coverage", "vl_toggle_coverage"):
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),

    ("c_flags", "ld_flags", "ld_libs"):
      Checker( lambda v: isinstance(v, str),  "expects a string" ),

    ("vl_opt_level", "vl_unroll_count", "vl_unroll_stmts"):
      Checker( lambda v: isinstance(v, int) and v >= 0, "expects an integer >= 0" ),

    "vl_Wno_list": Checker( lambda v: isinstance(v, list) and all(w in VerilogPlaceholderConfigs.Warnings for w in v),
                            "expects a list of warnings" ),

    "vl_xinit": Checker( lambda v: v in ['zeros', 'ones', 'rand'],
                  "vl_xinit should be one of ['zeros', 'ones', 'rand']" ),

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

  VerilatorWarnings = [
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

  PassName = 'VerilatorPlaceholderConfigs'

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, args, kwargs )
    assert len(args) == 0, "We only accept keyword arguments here."

    cls.Options  = deepcopy( cls.Options )
    cls.Checkers = deepcopy( cls.Checkers )

    for key, val in cls.VerilatorOptions:
      assert key not in cls.Options,\
        f'config {key} is duplicated between VerilogPlaceholderConfigs and VerilatorPlaceholderConfigs'
      cls.Options[key] = val

    all_checkers = s._get_all_checker_configs( cls )

    for cfgs, chk in cls.VerilatorCheckers:
      if isinstance( cfgs, tuple ):
        for cfg in cfgs:
          s._add_to_checkers( cls.Checkers, cfg, chk )
      elif isinstance( cfgs, str ):
        s._add_to_checkers( cls.Checkers, cfgs, chk )

  def get_vl_xinit_value( s ):
    if s.vl_xinit == 'zeros':
      return 0
    elif s.vl_xinit == 'ones':
      return 1
    elif s.vl_xinit == 'rand':
      return 2
    else:
      raise InvalidPassOptionValue("vl_xinit should be one of 'zeros', 'ones', or 'rand'!")

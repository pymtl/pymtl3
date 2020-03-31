#=========================================================================
# TracingConfigs.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Dec 4, 2019
"""Configuration class of tracing passes"""


from copy import deepcopy

from pymtl3.passes.PassConfigs import BasePassConfigs, Checker


class TracingConfigs( BasePassConfigs ):

  Options = {
    "tracing" : 'none',
    "vcd_file_name" : "",
    "chars_per_cycle" : 6,
    "method_trace" : True,
  }

  Checkers = {
    'tracing': Checker(
      lambda v: v in ['none', 'vcd', 'text_ascii', 'text_fancy' ],
      "expects a string in ['none', 'vcd', 'text_ascii', 'text_fancy']"
    ),

    'vcd_file_name': Checker(
      condition = lambda v: isinstance(v, str),
      error_msg = "expects a string"
    ),

    'chars_per_cycle': Checker(
      condition = lambda v: isinstance(v, int),
      error_msg = "expects a string"
    ),

    'method_trace': Checker(
      condition = lambda v: isinstance(v, bool),
      error_msg = "expects a boolean"
    ),
  }

  PassName = 'passes.tracing.*'

  # TODO: this is the old pass config. we need to incrementally migrate to
  # the new pass config.
  def __init__( s, *args, **kwargs ):
    assert len(args) == 0, "We only accept keyword arguments here."
    cls = s.__class__
    assert hasattr( cls, "Options"  )
    assert hasattr( cls, "PassName" )
    assert hasattr( cls, "Checkers" )

    opts = deepcopy( cls.Options )
    for opt, value in kwargs.items():
      if opt not in cls.Options:
        raise InvalidPassOption( opt, s.PassName )
      opts[opt] = value

    cls.opts = opts.keys()

    # Preprocess checkers
    cls._Checkers = {}
    for opt, chk in cls.Checkers.items():
      assert isinstance( chk, Checker ), f'Checker for "{opt}" can only be an instance of Checker, not {chk}.'

      if isinstance( opt, tuple ):
        for op in opt:
          assert op in opts, f"'{op}' is not a valid operation so we cannot set Checker for it."
          cls._Checkers[ op ] = chk

      elif isinstance( opt, str ):
        assert opt in opts, f"'{op}' is not a valid operation so we cannot set Checker for it."
        cls._Checkers[ opt ] = chk

      else:
        raise InvalidPassOption(f"Option name can only be a tuple of strings (a,b,c) or string a, not '{op}'")

    trivial_checker = Checker( lambda x: True, "" )
    for opt, value in opts.items():
      if opt not in cls._Checkers:
        cls._Checkers[opt] = trivial_checker
      assert not hasattr( s, opt ), f"There is already a field in config called '{opt}'. What happened?"
      setattr( s, opt, value )

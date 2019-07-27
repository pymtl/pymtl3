#=========================================================================
# PassConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 26, 2019
"""Base class of customized pass configuration classes."""

from copy import copy

from .errors import InvalidPassOption, InvalidPassOptionValue


class BasePassConfigs:
  """Base class of customized pass configrations.

  Users who wish to use this Base class should (1) put the name of their
  pass to `PassName`; (2) fill their own options and default values into
  `Options` class attribute; (3) define `check_<option_name>` methods
  that takes the value of `<option_name>` and returns whether this
  option is valid.
  """
  def __init__( s, **kwargs ):
    # s.Options = {}
    # s.PassName = "<base_pass>"
    s.options = s._gen_options( kwargs )

  def check_options( s ):
    """Return whether the given options are all valid."""
    for opt, value in s.options.items():
      func = getattr( s, "check_"+opt, lambda self, val: True )
      # check_* methods will throw exceptions if the check fails
      func(s, value)
    return True

  def get_option( s, opt ):
    """Return the value of option `opt`."""
    return s.options[opt]

  def set_option( s, opt, value ):
    s.options[opt] = value

  def _gen_options( s, _opts ):
    opts = copy( s.Options )
    for opt, value in _opts.items():
      if opt not in s.Options:
        raise InvalidPassOption( opt, s.PassName )
      opts[opt] = value
    return opts

  def gen_checker( s, opt, func, msg ):
    def _check( s, value ):
      try:
        return func(value)
      except AssertionError as e:
        raise InvalidPassOptionValue(opt, value, s.PassName, msg) from e
    return _check

  def set_checkers( s, opts, func, msg ):
    for opt in opts:
      s.set_checker(opt, func, msg)

  def set_checker( s, opt, func, msg ):
    setattr(s, "checke_"+opt, s.gen_checker(opt, func, msg))

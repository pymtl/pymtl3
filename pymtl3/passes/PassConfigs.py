#=========================================================================
# PassConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 26, 2019
"""Base class of customized pass configuration classes."""

from copy import deepcopy

from .errors import InvalidPassOption, InvalidPassOptionValue


class BasePassConfigs:
  """Base class of customized pass configrations.

  This base class provides methods to get/set option values, set the checking
  functions (checkers) for one or more options, and check if all given options
  are valid. Subclasses will provide all possible options with their default
  values. After initialization, all options and their values can be accessed
  from `s.options` or through `get_option` and `set_option`.

  Users who wish to use this Base class should (1) put the name of their
  pass to `PassName`; (2) fill their own options and default values into
  `Options` class attribute; (3) call `set_checker(s)` to define checkers for
  options or manually define `check_<option_name>` methods that takes the value
  of `<option_name>` and returns whether this option is valid. Note that this
  base class assumes a method with name `check_<option_name>` is a checker and
  will call that method to determine whether the value of option `<option_name>`
  is valid.
  """
  def __init__( s, **kwargs ):
    opts = deepcopy( s.Options )
    for opt, value in kwargs.items():
      if opt not in s.Options:
        raise InvalidPassOption( opt, s.PassName )
      opts[opt] = value
    s.options = opts

  @property
  def Options( s ):
    """Config classes extending 'BasePassConfigs' should define class attribute
    'Options', which is a dict of option names and their default values."""
    raise NotImplementedError(
        "PassConfigs must provide options and their default values to 'Options'!")

  @property
  def PassName( s ):
    """Config classes extending 'BasePassConfigs' should define class attribute
    'PassName', which is the name of the pass that accepts this config."""
    raise NotImplementedError(
        "PassConfigs must provide the name of the pass to 'PassName'!")

  def check_options( s ):
    """Return whether the given options are valid by calling checkers."""
    for opt, value in s.options.items():
      func = getattr( s, "check_"+opt, lambda self, val: True )
      # check_* methods will throw exceptions if the check fails
      func(s, value)
    return True

  def get_option( s, opt ):
    """Return the value of option `opt`."""
    return s.options[opt]

  def set_option( s, opt, value ):
    """Set the value of option `opt` to `value`."""
    s.options[opt] = value

  def set_checkers( s, opts, func, msg ):
    """Set checker for all options in `opts` using `func`; throw an exception
    with message `msg`.

    `opts` is a list of option names whose checking functions are to be set.
    `func` is a checking function that takes the value of an option and returns
    whether that is a valid value. Whenever `func` returns False, an
    `InvalidPassOptionValue` exception will be raised with message `msg`.
    """
    for opt in opts:
      s.set_checker(opt, func, msg)

  def set_checker( s, opt, func, msg ):
    """Set checker for option `opt` using `func`; throw an exception
    with message `msg`.

    `opt` is an option whose checking function is to be set. `func` is a checking
    function that takes the value of an option and returns whether that is a valid
    value. Whenever `func` returns False, an `InvalidPassOptionValue` exception
    will be raised with message `msg`.
    """
    def _check( s, value ):
      if not func(value):
        raise InvalidPassOptionValue(opt, value, s.PassName, msg)
      else:
        return True
    setattr(s, "check_"+opt, _check)

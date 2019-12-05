#=========================================================================
# PassConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 26, 2019

from copy import deepcopy

from .errors import InvalidPassOption, InvalidPassOptionValue


class Checker:

  def __init__( s, condition=lambda x: True, error_msg="" ):
    s.condition = condition
    s.error_msg = error_msg

  def check( s, opt, value, pass_name ):
    if not s.condition( value ):
      raise InvalidPassOptionValue( opt, value, pass_name, s.error_msg )

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
  def __new__( cls, *args, **kwargs ):
    assert len(args) == 0, "We only accept keyword arguments here."
    assert hasattr( cls, "Options"  )
    assert hasattr( cls, "PassName" )
    assert hasattr( cls, "Checkers" )

    inst = super().__new__( cls )

    opts = deepcopy( cls.Options )
    for opt, value in kwargs.items():
      if opt not in cls.Options:
        raise InvalidPassOption( opt, inst.PassName )
      opts[opt] = value

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
        cls._Checkers[ op ] = chk

      else:
        raise InvalidPassOption(f"Option name can only be a tuple of strings (a,b,c) or string a, not '{op}'")
    # Check each option and its value

    trivial_checker = Checker( lambda x: True, "" )

    for opt, value in opts.items():
      chk = cls.Checkers.get( opt, trivial_checker )
      if not chk.condition( value ):
        raise InvalidPassOptionValue( opt, value, cls.PassName, chk.error_msg )
      assert not hasattr( inst, opt ), "Cannot declare two options with the same name"
      setattr( inst, opt, value )

    return inst

  def fill_missing( cls,

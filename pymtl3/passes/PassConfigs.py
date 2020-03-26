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

  def __init__( s, m ):
    c = s.__class__
    assert hasattr( c, "Options"  )
    assert hasattr( c, "Pass"     )
    assert hasattr( c, "Checkers" )
    s.setup_checkers()
    s.collect_all_pass_configs( m )

  def setup_checkers( s ):
    c = s.__class__
    # Preprocess checkers
    opts = c.Options.keys()
    c._Checkers = {}
    for opt, chk in c.Checkers.items():
      assert isinstance( chk, Checker ), f'Checker for "{opt}" can only be an instance of Checker, not {chk}.'

      if isinstance( opt, tuple ):
        for op in opt:
          assert op in opts, f"'{op}' is not a valid operation so we cannot set Checker for it."
          c._Checkers[ op ] = chk

      elif isinstance( opt, str ):
        assert opt in opts, f"'{op}' is not a valid operation so we cannot set Checker for it."
        c._Checkers[ opt ] = chk

      else:
        raise InvalidPassOption(f"Option name can only be a tuple of strings (a,b,c) or string a, not '{op}'")

    trivial_checker = Checker( lambda x: True, "" )
    for opt, value in c.Options.items():
      if opt not in c._Checkers:
        c._Checkers[opt] = trivial_checker

  def collect_all_pass_configs( s, m ):
    c = s.__class__
    for opt, default in c.Options.items():
      assert not hasattr( s, opt ), f"There is already a field in config called '{opt}'. What happened?"
      if not m.has_metadata( getattr( c.Pass, opt ) ):
        setattr( s, opt, deepcopy(default) )
      else:
        setattr( s, opt, deepcopy(m.get_metadata( getattr( c.Pass, opt ) )) )

  def check( s ):
    """Check whether the given options are valid by calling checkers."""
    for opt in s.opts:
      chk   = s._Checkers[opt]
      value = getattr( s, opt )
      if not chk.condition( value ):
        raise InvalidPassOptionValue( opt, value, s.Pass.__name__, chk.error_msg )

  def is_default( s, opt ):
    """Return True if `opt` has the default value."""
    return getattr( s, opt ) == s.Options[opt]

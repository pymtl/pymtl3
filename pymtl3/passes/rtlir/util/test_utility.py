#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 21, 2019
"""Test utilities used by RTLIR tests."""

from contextlib import contextmanager

import pytest


@pytest.fixture
def do_test( request ):
  """Call `local_do_test` of the requesting module."""
  return request.module.local_do_test

@contextmanager
def expected_failure( exception = Exception, msg = None ):
  """Mark one test case as should-fail.

  Not to be confused with pytest.xfail, which is commonly used to mark
  tests related to unimplemented functionality. This test only passes when
  it throws an expected exception.
  """
  try:
    yield
  except exception as e:
    if msg is None or e.args[0].find( msg ) != -1:
      return
    else:
      raise
  raise Exception( 'expected-to-fail test unexpectedly passed!' )

def get_parameter( name, func ):
  """Return the parameter for `name` arg of `func`"""
  try:
    for mark in func.pytestmark:
      if mark.name == 'parametrize':
        # Find the position of the given name
        pos = -1
        for i, arg in enumerate( mark.args[0].split() ):
          if arg == name:
            pos = i
            break
        if pos == -1:
          raise Exception( f'{func} does not have parameter named {name}!' )
        if len(mark.args[0].split()) == 1:
          return mark.args[1]
        return list(map(lambda x: x[pos], mark.args[1]))
  except AttributeError:
    raise Exception( f'given function {func} does not have pytest marks!' )

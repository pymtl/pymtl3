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

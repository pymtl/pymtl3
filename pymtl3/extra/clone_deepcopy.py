"""
========================================================================
clone_deepcopy.py
========================================================================

Author: Shunning Jiang
  Date: June 9, 2020
"""
from copy import deepcopy


def clone_deepcopy( x ):
  try:
    return x.clone()
  except AttributeError:
    return deepcopy(x)

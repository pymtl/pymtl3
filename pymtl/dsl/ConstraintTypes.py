"""
========================================================================
ConstraintType.py
========================================================================
Explicit constraint class types.

Author : Shunning Jiang
Date   : July 7, 2017
"""
from __future__ import absolute_import, division, print_function


class FuncConstraint(object):
  def __init__( self, func ): self.func = func
  def __lt__( self, other ):  return (self, other, False)
  def __gt__( self, other ):  return (other, self, False)
  def __eq__( self, other ):  return (self, other, True)

class ValueConstraint(object):
  def __init__( self, var ):  self.var = var
  def __lt__( self, other ):  return (self, other, False)
  def __gt__( self, other ):  return (other, self, False)

class U(FuncConstraint): pass
class M(FuncConstraint): pass

class RD(ValueConstraint): pass
class WR(ValueConstraint): pass

from PyMTLObject     import PyMTLObject

class FuncConstraint(PyMTLObject):
  def __init__( self, func ):  self.func = func
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)
  def __call__( self ):        self.func()

class ValueConstraint(PyMTLObject):
  def __init__( self, var ):   self.var = var
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)

class U(FuncConstraint): pass
class M(FuncConstraint): pass

class RD(ValueConstraint): pass
class WR(ValueConstraint): pass

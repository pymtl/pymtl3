class U(object):
  def __init__( self, func ):  self.func = func
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)
  def __call__( self ):        self.func()

class M(object):
  def __init__( self, func ):  self.func = func
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)
  def __call__( self ):        self.func()

class RD(object):
  def __init__( self, var ):   self.var = var
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)

class WR(object):
  def __init__( self, var ):   self.var = var
  def __lt__( self, other ):   return (self, other)
  def __gt__( self, other ):   return (other, self)


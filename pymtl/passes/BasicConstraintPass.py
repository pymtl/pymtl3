#-------------------------------------------------------------------------
# BasicConstraintPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass

class BasicConstraintPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def execute( self, m ): # execute pass on model m
    assert hasattr( m, "_blkid_upblk" ), "Please apply other passes to generate model._expl_constraints"

    m._constraints = m._expl_constraints.copy()

    if self.dump:
      self.print_constraints( m )
    return m

  @staticmethod
  def print_constraints( m ):

    print
    print "+-------------------------------------------------------------"
    print "+ Constraints"
    print "+-------------------------------------------------------------"
    for (x, y) in m._expl_constraints:
      print m._blkid_upblk[x].__name__.center(25),"  <  ", m._blkid_upblk[y].__name__.center(25)

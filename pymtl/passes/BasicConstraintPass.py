#-------------------------------------------------------------------------
# BasicConstraintPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass

class BasicConstraintPass( BasePass ):

  def execute( self, m ): # execute pass on model m
    m._constraints = m._U_U_constraints.copy()
    return m

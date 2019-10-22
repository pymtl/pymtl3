#=========================================================================
# PlacementPass.py
#=========================================================================
# Generate placement geometric information module recursively.
#
# Author : Cheng Tan
# Date   : Oct 22, 2019

from pymtl3.passes.BasePass import BasePass
from collections            import deque

class PlacementPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "elaborate_physical" ):
#      print( "Note that there is no elaborate_physical defined in "
#             "network module:{}".format(top.__class__.__name__) )
      all_components = sorted( top.get_all_components(), key=repr )
      translatable_roots = top.get_translatable_roots()
      print 'translatable_roots: ', translatable_roots
      return

    all_components = sorted( top.get_all_components(), key=repr )
    all_components.reverse()
    for c in all_components:
      if hasattr( c, "elaborate_physical" ):
        c.elaborate_physical()
    top.elaborate_physical()

    # Generate the floorplanning script

    print '\n---- placement geometric information ----'
    print "createFence Ring4 {} {} {} {}\n".format( top.dim.x, top.dim.y, 
        top.dim.x + top.dim.w, top.dim.y + top.dim.h )
    for i, r in enumerate( top.routers ):
      print "createFence router__{} {} {} {} {}".format( str(i),
          r.dim.x, r.dim.y, r.dim.x + r.dim.w, r.dim.y + r.dim.h )

    print '---------------------'


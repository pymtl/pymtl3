#=========================================================================
# OCNDrawPass.py
#=========================================================================
# Draw topology for the network generated from OCN generator.
#
# Author : Cheng Tan
# Date   : May 22, 2019

from pymtl.passes import BasePass
from collections  import deque
from graphviz     import Digraph
from errors       import PassOrderError
from BasePass     import BasePass

class OCNDrawPass( BasePass ):

  def __call__( self, top ):

    all_components = sorted( top.get_all_components(), key=repr )
    all_components.reverse()
#    for c in all_components:
#      print '*********: ', c._dsl.adjacency

    print '---------------------'


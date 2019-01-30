#========================================================================
# UpblkTranslationPass.py
#========================================================================
# Translation pass for all update blocks within one component. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

import ast
from pymtl       import *
from pymtl.dsl   import ComponentLevel1
from BasePass    import BasePass
from collections import defaultdict, deque
from errors      import TranslationError
from inspect     import getsource

from UpblkRASTGenPass import UpblkRASTGenPass
from UpblkRASTToSVPass import UpblkRASTToSVPass
from RASTVisualizationPass import RASTVisualizationPass
from UpblkRASTTypeCheckPass import UpblkRASTTypeCheckPass

class UpblkTranslationPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """ translate all upblks in component m and return the source code
    string"""

    # Generate and visualize RAST
    UpblkRASTGenPass()( m )
    UpblkRASTTypeCheckPass( s.type_env )( m )
    RASTVisualizationPass()( m )
    UpblkRASTToSVPass()( m )

    # Copy generated SystemVerilog source code into this pass's namespace
    m._blk_srcs = {}

    for blk in m.get_update_blocks():
      m._blk_srcs[ blk ] = m._rast_to_sv[ blk ]

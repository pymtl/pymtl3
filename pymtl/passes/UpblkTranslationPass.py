#========================================================================
# UpblkTranslationPass.py
#========================================================================
# Translation pass for all update blocks within one component. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

import ast
from pymtl        import *
from pymtl.model  import ComponentLevel1
from BasePass     import BasePass
from collections  import defaultdict, deque
from errors       import TranslationError
from inspect      import getsource

from UpblkRASTGenPass import UpblkRASTGenPass
from RASTVisualizationPass import RASTVisualizationPass
from UpblkRASTTypeCheckPass import UpblkRASTTypeCheckPass

class UpblkTranslationPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """ translate all upblks in component m and return the source code
    string"""

    blk_srcs = ''

    # Generate and visualize RAST
    UpblkRASTGenPass()( m )
    UpblkRASTTypeCheckPass( s.type_env )( m )
    RASTVisualizationPass()( m )

    return blk_srcs


#========================================================================
# LineTraceParamPass.py
#========================================================================
# Enable multi-level line trace.
#
# Author : Yanghui Ou
#   Date : May 29, 2019

from pymtl3.dsl import *
from pymtl3.passes.BasePass import BasePass, PassMetadata


class LineTraceParamPass( BasePass ):

  def __call__( self, top ):

    def wrap_line_trace( obj ):
      if not hasattr( obj, '_ml_trace' ):
        obj._ml_trace = PassMetadata()
      obj._ml_trace.line_trace = obj.line_trace

      def wrapped_line_trace( self, *args, **kwargs ):
        if self._dsl.param_tree is not None:
          if self._dsl.param_tree.leaf is not None:
            if 'line_trace' in self._dsl.param_tree.leaf:
              # TODO: figure out whether it is necessary to enforce no
              # positional args.
              assert len( args ) == 0
              more_args = self._dsl.param_tree.leaf['line_trace'].items()
              kwargs.update({ x:y for x, y in more_args })
        try:
          return self._ml_trace.line_trace( *args, **kwargs )
        except TypeError:
          return self._ml_trace.line_trace()

      obj.line_trace = lambda *args, **kwargs : wrapped_line_trace( obj, *args, **kwargs )

    all_objects = top.get_all_object_filter( lambda x: True )
    for obj in all_objects:
      if hasattr( obj, 'line_trace' ):
        wrap_line_trace( obj )

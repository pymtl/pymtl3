#========================================================================
# CLLineTracePass.py
#========================================================================
# Enable CL line trace.
#
# Author : Yanghui Ou
#   Date : May 21, 2019

from __future__ import absolute_import, division, print_function

from copy import deepcopy

from pymtl.dsl.Connectable import CalleePort, CallerPort, MethodPort
from pymtl.passes.BasePass import BasePass, PassMetadata


class CLLineTracePass( BasePass ):

  def __call__( self, top ):
    
    # A new __call__ function for CallerPort
    def __caller_call__( self, *args, **kwargs ):
      self.saved_args = args
      self.saved_kwargs = kwargs
      self.called = True
      self.saved_ret = self._dsl.driver( *args, **kwargs )
      return self.saved_ret

    # A new __call__ function for CalleePort
    def __callee_call__( self, *args, **kwargs ):
      self.saved_args = args
      self.saved_kwargs = kwargs
      self.called = True
      self.saved_ret = self.method( *args, **kwargs )
      if self._dsl.is_writer:
        for mport in self._dsl.drived_methods:
          mport.update_trace( self.saved_ret, *args, **kwargs )
      return self.saved_ret

    # Update trace function for MethodPort, so that the actual driver
    # can update the trace of all methods it's driving
    def update_trace( self, ret, *args, **kwargs ):
      self.called = True
      self.saved_args = args
      self.saved_kwargs = kwargs
      self.saved_ret = ret

    # Mutate classes
    MethodPort.update_trace = update_trace
    CallerPort.__call_trace__ = __caller_call__
    CalleePort.__call_trace__ = __callee_call__

    # Collect all method ports and add some stamps
    all_method_ports = top.get_all_object_filter( 
      lambda s: isinstance( s, MethodPort ) 
    )
    for mport in all_method_ports:
      mport.called = False
      mport._dsl.line_trace_flag = True

    # An update block that resets all method ports to not called
    def reset_method_ports():
      for mport in all_method_ports:
        mport.called = False
        mport.saved_args = None
        mport.saved_kwargs = None
        mport.saved_ret = None

    top._cl_trace = PassMetadata()

    # Create a new schedule
    new_schedule = deepcopy( top._sched.schedule )
    new_schedule.insert( 0, reset_method_ports )
    top._cl_trace.schedule = new_schedule

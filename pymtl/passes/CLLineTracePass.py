#========================================================================
# CLLineTracePass.py
#========================================================================
# Enable CL line trace.
#
# Author : Yanghui Ou
#   Date : May 21, 2019

from __future__ import absolute_import, division, print_function

from copy import deepcopy

from pymtl.dsl.Connectable import (
    CalleePort,
    CallerPort,
    MethodPort,
    NonBlockingInterface,
)
from pymtl.passes.BasePass import BasePass, PassMetadata


class CLLineTracePass( BasePass ):

  def __call__( self, top ):

    def wrap_callee_method( mport, drived_methods ):

      mport.raw_method = mport.method
      def wrapped_method( self, *args, **kwargs ):
        self.saved_args = args
        self.saved_kwargs = kwargs
        self.called = True
        self.saved_ret = self.raw_method( *args, **kwargs )
        for m in drived_methods:
          m.called = True
          m.saved_args = self.saved_args
          m.saved_kwargs = self.saved_kwargs
          m.saved_ret = self.saved_ret
        return self.saved_ret
      mport.method = lambda *args, **kwargs : wrapped_method( mport, *args, **kwargs )

    def wrap_caller_method( mport, driver ):
      mport.raw_method = mport.method
      def wrapped_method( self, *args, **kwargs ):
        self.saved_args = args
        self.saved_kwargs = kwargs
        self.called = True
        self.saved_ret = driver( *args, **kwargs )
        return self.saved_ret
      mport.method = lambda *args, **kwargs : wrapped_method( mport, *args, **kwargs )

    def new_str( s ):
      if s.method.called:
        args_str = ",".join(
          [ str( arg ) for arg in s.method.saved_args ] 
        )
        kwargs_str = ",".join(
          [ str( arg ) for _, arg in s.method.saved_kwargs.items() ]
        )
        ret_str = (
          "" if s.method.saved_ret is None else 
          str( s.method.saved_ret )
        )
        trace = []
        if len( args_str ) > 0: trace.append( args_str )
        if len( kwargs_str ) > 0: trace.append( kwargs_str )
        if len( ret_str ) > 0 : trace.append( ret_str )
        trace_str = ",".join( trace )
        return trace_str.ljust( s._dsl.trace_len ) 
      elif s.rdy.called:
        if s.rdy.saved_ret:
          return " ".ljust( s._dsl.trace_len )
        else:
          return "#".ljust( s._dsl.trace_len )
      elif not s.rdy.called:
        return ".".ljust( s._dsl.trace_len )
      else:
        return "X".ljust( s._dsl.trace_len )

    # Collect all method ports and add some stamps
    all_callees = set()
    all_method_ports = top.get_all_object_filter( 
      lambda s: isinstance( s, MethodPort ) 
    )
    for mport in all_method_ports:
      mport.called = False
      mport.saved_args = None
      mport.saved_kwargs = None
      mport.saved_ret = None
      if isinstance( mport, CalleePort ):
        all_callees.add( mport )

    # Collect all method nets and wrap the actual driving method
    all_drivers = set()
    all_method_nets = top.get_all_method_nets()
    for driver, net in all_method_nets:
      wrap_callee_method( driver, net )
      all_drivers.add( driver )
      for member in net:
        if isinstance( member, CallerPort ):
          assert member is not driver
          wrap_caller_method( member, driver )
    
    # Handle other callee that is not driving anything
    for mport in ( all_callees - all_drivers ):
      wrap_callee_method( mport, set() )


    # Collecting all non blocking interfaces and replace the str hook
    all_nblk_ifcs = top.get_all_object_filter( 
      lambda s: isinstance( s, NonBlockingInterface ) 
    )
    for ifc in all_nblk_ifcs:
      ifc._str_hook = lambda : new_str( ifc )

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

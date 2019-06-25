#========================================================================
# CLLineTracePass.py
#========================================================================
# Enable CL line trace.
#
# Author : Yanghui Ou
#   Date : May 21, 2019

from pymtl3.dsl import *

from .BasePass import BasePass, PassMetadata


class CLLineTracePass( BasePass ):

  def __init__( self, trace_len=16 ):
    self.default_trace_len = trace_len

  def __call__( self, top ):

    # Create a new schedule

    if hasattr( top, "_sched" ):
      top._cl_trace = PassMetadata()
      top._cl_trace.schedule = [ self.process_component( top ) ] + top._sched.schedule

  def process_component( self, top ):

    # [wrap_callee_method] wraps the original method in a callee port
    # into a new method that not only calls the origianl method, but
    # also saves the arguments to the method and the return value,
    # which can be used for composing the line trace.
    # The wrapped method also need to update the saved arguments and
    # return value of all the methods this callee port is driving.
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

    # [wrap_caller_method] wraps the original method in a caller port
    # into a new method that calls its driver instead of the actual
    # method, which will trigger the actual driver to update all other
    # method ports connected to this net.
    def wrap_caller_method( mport, driver ):
      mport.raw_method = mport.method
      def wrapped_method( self, *args, **kwargs ):
        self.saved_args = args
        self.saved_kwargs = kwargs
        self.called = True
        self.saved_ret = driver( *args, **kwargs )
        return self.saved_ret
      mport.method = lambda *args, **kwargs : wrapped_method( mport, *args, **kwargs )

    # [mk_new_str] replaces [_str_hook] in a non-blocking interface with
    # a new to-string function that uses the metadata to compose line
    # trace.
    # When the rdy is called and returns true, and the method gets called,
    # the line trace just prints out the actual message. Otherwise, it '
    # prints out some special characters under different circumstances:
    # - 'x' rdy not called but method called
    # - '.' rdy not called, method not called
    # - "#" rdy called and is false, method not called
    # - "X" rdy called and is false, method still called
    # - " " rdy called and is true, method not called
    # For example, a cycle-level single element normal queue would have
    # the following line trace:
    #      enq     deq
    #  1:( 0000 () #    ) - enq(0000) called, deq is not ready
    #  2:( #    () 0000 ) - enq is not ready, deq() gets called
    #  3:( 0001 () #    ) - enq(0001) called, deq is not ready again
    def mk_new_str( ifc ):
      def new_str( self ):
        # If rdy is called
        if self.rdy.called:

          # If rdy is called and returns true
          if self.rdy.saved_ret:

            # If rdy and method called - return actuall message
            if self.method.called:
              args_str = ",".join(
                [ str( arg ) for arg in self.method.saved_args ]
              )
              kwargs_str = ",".join(
                [ str( arg ) for _, arg in self.method.saved_kwargs.items() ]
              )
              ret_str = (
                "" if self.method.saved_ret is None else
                str( self.method.saved_ret )
              )
              trace = []
              if len( args_str ) > 0: trace.append( args_str )
              if len( kwargs_str ) > 0: trace.append( kwargs_str )
              if len( ret_str ) > 0 : trace.append( ret_str )
              trace_str = ",".join( trace )
              return trace_str.ljust( self.trace_len )

            # If rdy and method not called
            else:
              return " ".ljust( self.trace_len )

          # If rdy is called and returns false
          elif self.method.called:
            return "X".ljust( self.trace_len )
          else:
            return "#".ljust( self.trace_len )

        # If rdy is not called
        elif self.method.called:
          return "x".ljust( self.trace_len )

        else:
          return ".".ljust( self.trace_len )

      ifc._str_hook = lambda : new_str( ifc )

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
      if driver is not None:
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
      if ifc.method.Type is not None:
        trace_len = len( str( ifc.method.Type() ) )
      else:
        trace_len = self.default_trace_len
      ifc.trace_len = trace_len
      mk_new_str( ifc )

    # An update block that resets all method ports to not called
    def reset_method_ports():
      for mport in all_method_ports:
        mport.called = False
        mport.saved_args = None
        mport.saved_kwargs = None
        mport.saved_ret = None

    return reset_method_ports

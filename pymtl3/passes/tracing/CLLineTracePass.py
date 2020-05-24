#========================================================================
# CLLineTracePass.py
#========================================================================
# Enable CL line trace.
#
# Author : Yanghui Ou
#   Date : May 21, 2019

from pymtl3.dsl import *
from pymtl3.passes.BasePass import BasePass


class CLLineTracePass( BasePass ):

  # CLLineTracePass public pass data

  #: enable
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: True
  enable = MetadataKey(bool)

  clear_cl_trace_func = MetadataKey()

  def __init__( self, default_trace_len=8 ):
    self.default_trace_len = default_trace_len

  def __call__( self, top ):

    # Turn on by default
    if top.has_metadata( self.enable ) and top.get_metadata( self.enable ) is False:
      return

    assert not top.has_metadata( self.clear_cl_trace_func )

    top.set_metadata( self.clear_cl_trace_func, self.process_component( top ) )

  def process_component( self, top ):

    # [wrap_callee_method] wraps the original method in a callee port
    # into a new method that not only calls the origianl method, but
    # also saves the arguments to the method and the return value,
    # which can be used for composing the line trace.
    # The wrapped method also need to update the saved arguments and
    # return value of all the methods this callee port is driving.
    def wrap_callee_method( mport, net ):
      mport.raw_method = mport.method
      def wrapped_method( self, *args, **kwargs ):
        # If it has greenlet i.e. blocking ... we need to make sure
        # we record everything after the method is successfully invoked
        ret = self.raw_method( *args, **kwargs )
        for m in net:
          m.called = True
          m.saved_args = args
          m.saved_kwargs = kwargs
          m.saved_ret = ret
        return ret
      mport.method = lambda *args, **kwargs : wrapped_method( mport, *args, **kwargs )

    # [wrap_caller_method] wraps the original method in a caller port
    # into a new method that calls its driver instead of the actual
    # method, which will trigger the actual driver to update all other
    # method ports connected to this net.
    def wrap_caller_method( mport, driver_method ):
      def wrapped_method( self, *args, **kwargs ):
        return driver_method( *args, **kwargs )
      mport.method = lambda *args, **kwargs : wrapped_method( mport, *args, **kwargs )

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

    def mk_new_str_non_blocking( ifc ):
      def new_str():
        # If rdy is called
        if ifc.rdy.called:
          # If rdy is called and returns true
          if ifc.rdy.saved_ret:
            # If rdy and method called - return actual message
            if ifc.method.called:
              args_strs = [ str( arg ) for arg in ifc.method.saved_args ] + \
                          [ str( arg ) for _, arg in ifc.method.saved_kwargs.items() ]

              ret_str = "" if ifc.method.saved_ret is None else str( ifc.method.saved_ret )

              trace = ""
              if args_strs:
                trace += f"({','.join(args_strs)})"
              if ret_str:
                trace += f"={ret_str}"

              ifc.trace_len = len(trace)
              return trace

            # If rdy and method not called
            else:
              return " ".ljust( ifc.trace_len )

          # If rdy is called and returns false
          elif ifc.method.called:
            return "X".ljust( ifc.trace_len )
          else:
            return "#".ljust( ifc.trace_len )

        # If rdy is not called
        elif ifc.method.called:
          return "x".ljust( ifc.trace_len )

        else:
          return ".".ljust( ifc.trace_len )
      return new_str

    # Collecting all non blocking interfaces and replace the str hook
    for ifc in top.get_all_object_filter( lambda s: isinstance( s, NonBlockingIfc ) ):
      if ifc.method.Type is not None:
        ifc.trace_len = len( str( ifc.method.Type() ) )
      else:
        ifc.trace_len = self.default_trace_len
      ifc._str_hook = mk_new_str_non_blocking( ifc )

    # [mk_new_str] replaces [_str_hook] in a blocking interface with
    # a new to-string function that uses the metadata to compose line
    # trace. The case for blocking interfaces is simpler than
    # non-blocking interfaces as we only have two possibilities
    # called/not called.
    # - " " method not called
    # - msg method called
    def mk_new_str_blocking( ifc ):
      def new_str():
        # If method called - return actual message
        if ifc.method.called:
          args_strs = [ str( arg ) for arg in ifc.method.saved_args ] + \
                      [ str( arg ) for _, arg in ifc.method.saved_kwargs.items() ]

          ret_str = "" if ifc.method.saved_ret is None else str( ifc.method.saved_ret )

          trace = ""
          if args_strs:
            trace += f"({','.join(args_strs)})"
          if ret_str:
            trace += f"={ret_str}"

          ifc.trace_len = len(trace)
          return trace

        # If method not called
        else:
          return " ".ljust( ifc.trace_len )
      return new_str

    # Collecting all blocking interfaces and replace the str hook
    for ifc in top.get_all_object_filter( lambda s: isinstance( s, BlockingIfc ) ):
      if ifc.method.Type is not None:
        ifc.trace_len = len( str( ifc.method.Type() ) )
      else:
        ifc.trace_len = self.default_trace_len
      ifc._str_hook = mk_new_str_blocking( ifc )

    # An update block that resets all method ports to not called
    def reset_method_ports():
      for mport in all_method_ports:
        mport.called = False
        mport.saved_args = None
        mport.saved_kwargs = None
        mport.saved_ret = None

    return reset_method_ports

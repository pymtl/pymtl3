#=========================================================================
# test_wrapper
#=========================================================================
# Wrappers for testing rtl model.
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

from pymtl import *
from template import *


def _mangleName( method_name, port_name ):
  return method_name + "_" + port_name


#-------------------------------------------------------------------------
# Result
#-------------------------------------------------------------------------
class Result():
  pass

  def __eq__( self, obj ):
    if not isinstance( obj, Result ):
      return false
    return self.__dict__ == obj.__dict__


#-------------------------------------------------------------------------
# RTLAdapter
#-------------------------------------------------------------------------
class RTLAdapter( RTLComponent ):

  def construct( s, rtl_model, method_specs ):
    s.model = rtl_model
    s.method_specs = method_specs
    s.ports = {}

    for method_name, method_spec in s.method_specs.iteritems():
      s._add_ports( method_spec )
      s._gen_update( method_spec )

  def _rename( s, f, newname ):
    f.__name__ = newname

  def _add_ports( s, method_spec ):
    ports = {}
    setattr( s, method_spec.method_name, InVPort( Bits1 ) )
    setattr( s, _mangleName( method_spec.method_name, "rdy" ),
             OutVPort( Bits1 ) )
    for arg, dtype in method_spec.args.iteritems():
      ports[ arg ] = InVPort( dtype )
      setattr( s, _mangleName( method_spec.method_name, arg ),
               InVPort( dtype ) )
    for ret, dtype in method_spec.rets.iteritems():
      setattr( s, _mangleName( method_spec.method_name, ret ),
               OutVPort( dtype ) )
    s.ports[ method_spec.method_name ] = ports

  def _gen_update( s, method_spec ):

    assign_args = ""
    for arg in method_spec.args.keys():
      assign_args += assign_args_tmpl.format(
          method_name=method_spec.method_name, arg=arg )

    assign_rets = ""
    for ret in method_spec.rets.keys():
      assign_rets += assign_rets_tmpl.format(
          method_name=method_spec.method_name, ret=ret )

    updates = update_tmpl.format(
        assign_rets=assign_rets,
        assign_args=assign_args,
        method_name=method_spec.method_name )

    # The problem with generating update block code is that
    # inpect.getsource will throw exception. To work around that we create
    # a fake filename and write the source code to linecache
    # This is a hacky workaround that might change later
    filename = '<dynamic-123456>'
    exec ( compile( updates, filename, 'exec' ), locals() )
    lines = [ line + '\n' for line in updates.splitlines() ]
    import linecache
    linecache.cache[ filename ] = ( len( updates ), None, lines, filename )
    s._rename( update, "update_" + method_spec.method_name + "_adapter" )
    s.update( update )

  def line_trace( s ):
    return s.model.line_trace()


#-------------------------------------------------------------------------
# RTLWrapper
#-------------------------------------------------------------------------


class RTLWrapper():

  def __init__( self, model ):
    self.model = model
    self.model.apply( SimpleSim )
    self.method_specs = self.model.method_specs
    self._post_construct()
    self.results = {}
    for method, spec in self.method_specs.iteritems():
      self._add_result( spec )
      self._add_method( spec )
    self._add_cycle()

  def _post_construct( s ):
    for method_name, method_spec in s.method_specs.iteritems():
      ports = {}
      ports[ "__method" ] = getattr( s.model, method_spec.method_name )
      ports[ "rdy" ] = getattr( s.model,
                                _mangleName( method_spec.method_name, "rdy" ) )
      for arg, dtype in method_spec.args.iteritems():
        ports[ arg ] = getattr( s.model,
                                _mangleName( method_spec.method_name, arg ) )
      for ret, dtype in method_spec.rets.iteritems():
        ports[ ret ] = getattr( s.model,
                                _mangleName( method_spec.method_name, ret ) )
      s.model.ports[ method_name ] = ports

  def _add_result( self, method_spec ):
    self.results[ method_spec.method_name ] = Result()

  def _add_method( self, method_spec ):
    method_name = method_spec.method_name
    result = self.results[ method_name ]

    assign_args = ""
    for arg in method_spec.args.keys():
      assign_args += arg_tmpl.format( arg=arg, method=method_name )

    method_code = method_tmpl.format(
        method=method_name, assign_args=assign_args )
    exec ( compile( method_code, "<string>", 'exec' ), locals() )

    setattr( method, "__name__", method_name )
    setattr( self, method_name, method )

  def _add_cycle( self ):

    assign_rets = ""
    for method, spec in self.method_specs.iteritems():
      assign_rets += rdy_tmpl.format( method=method )
      for ret in spec.rets.keys():
        assign_rets += ret_tmpl.format( method=method, ret=ret )
      assign_rets += clear_tmpl.format( method=method )

    cycle_code = cycle_tmpl.format( assign_rets=assign_rets )
    exec ( compile( cycle_code, "<string>", 'exec' ), locals() )
    setattr( self, "cycle", cycle )

  def reset( self ):
    pass

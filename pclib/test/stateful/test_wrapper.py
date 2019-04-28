#=========================================================================
# test_wrapper
#=========================================================================
# Wrappers for testing rtl model.
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

from pymtl import *
from template import *
from pclib.ifcs.GuardedIfc import guarded_ifc, GuardedCalleeIfc
from pymtl.dsl.ComponentLevel6 import ComponentLevel6

import inspect
import attr


def _mangleName( method_name, port_name ):
  return method_name + "_" + port_name


#-------------------------------------------------------------------------
# Result
#-------------------------------------------------------------------------


class Result():
  pass

  def __eq__( self, obj ):
    if not isinstance( obj, Result ):
      return False
    return self.__dict__ == obj.__dict__


#-------------------------------------------------------------------------
# Method
#-------------------------------------------------------------------------


@attr.s()
class Method( object ):
  method_name = attr.ib()
  args = attr.ib( default={} )
  rets = attr.ib( default={} )


def rename( f, newname ):
  f.__name__ = newname


#-------------------------------------------------------------------------
# RTLAdapter
#-------------------------------------------------------------------------


class RTL2CLWrapper( Component ):

  def _construct( s ):
    Component._construct( s )

  def inspect( s, rtl_model ):
    method_specs = {}

    for method, ifc in inspect.getmembers( rtl_model ):
      args = {}
      rets = {}
      if isinstance( ifc, Interface ):
        for name, port in inspect.getmembers( ifc ):
          if name == 'en' or name == 'rdy':
            continue
          if isinstance( port, InPort ):
            args[ name ] = port._dsl.Type
          if isinstance( port, OutPort ):
            rets[ name ] = port._dsl.Type

        method_specs[ method ] = Method(
            method_name=method, args=args, rets=rets )
    return method_specs

  def bind_methods( s ):
    # This code is copied from ComponentLevel6
    # In a RTL2CLWrapper bind_method needs to be called inside construct after
    # cl methods are added, which happens after inspecting the rtl model

    # NOTE from Yanghui: I replaced this piece of code.
    ComponentLevel6._handle_guard_methods( s )

  def construct( s, rtl_model ):
    s.model = rtl_model

    s.method_specs = s.inspect( s.model )
    for method_name, method_spec in s.method_specs.iteritems():
      s._add_method( method_spec )

    s.bind_methods()

    s.ports = {}
    s.reset_called = Bits1()
    s._constraints = []

    for method_name, method_spec in s.method_specs.iteritems():
      s._add_ports( method_spec )
      s._gen_update( method_spec )

  def _add_ports( s, method_spec ):
    setattr( s, _mangleName( method_spec.method_name, "called" ), Bits1() )
    setattr( s, _mangleName( method_spec.method_name, "rdy" ), Bits1() )
    for arg, dtype in method_spec.args.iteritems():
      setattr( s, _mangleName( method_spec.method_name, arg ), dtype() )
    for ret, dtype in method_spec.rets.iteritems():
      setattr( s, _mangleName( method_spec.method_name, ret ), dtype() )

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

    # Rename to avoid name conflicts
    rename( update_rdy, "update_" + method_spec.method_name + "_rdy_adapter" )
    rename( update, "update_" + method_spec.method_name + "_adapter" )
    rename( update_rets, "update_" + method_spec.method_name + "_rets_adapter" )
    rename( update_args, "update_" + method_spec.method_name + "_args_adapter" )

    s.update( update )
    s.update( update_rdy )

    rdy_func = s.__dict__[ method_spec.method_name ].rdy
    method_func = s.__dict__[ method_spec.method_name ]
    ifcs = s.model.__dict__[ method_spec.method_name ]

    if method_spec.args:
      s.update( update_args )
      s.add_constraints( M( method_func ) < U( update_args ) )
      for arg in method_spec.args.keys():
        s.add_constraints( U( update_args ) < RD( ifcs.__dict__[ arg ] ) )
        s.add_constraints( U( update ) < RD( ifcs.__dict__[ arg ] ) )

    if method_spec.rets:
      s.update( update_rets )
      s.add_constraints( U( update_rets ) < M( method_func ) )
      for ret in method_spec.args.keys():
        s.add_constraints( WR( ifcs.__dict__[ ret ] ) < U( update_rets ) )

      #s.add_constraints( U( update_rets ) < U( update ) )

    s.add_constraints(
        U( update_rdy ) < M( rdy_func ),
        U( update_rdy ) < M( rdy_func ),
        M( rdy_func ) < U( update ),
        M( method_func ) < U( update ),
        U( update ) < RD( ifcs.en ) )

  def _add_method( self, method_spec ):

    method_name = method_spec.method_name
    assign_args = ""
    for arg in method_spec.args.keys():
      assign_args += arg_tmpl.format( arg=arg, method=method_name )

    method_code = method_tmpl.format(
        method=method_name, assign_args=assign_args )

    method_spec = method_spec

    def method(*args, **kwargs ):
      namespace = { 'method_spec': method_spec, 'kwargs': kwargs, 'self': self}
      if not kwargs and args:
        count = 0
        for arg in method_spec.args.keys():
          kwargs[ arg ] = args[ count ]
          count += 1
      exec ( compile( method_code, "<string>", 'exec' ), namespace )
      ret_list = [
          self.__dict__[ _mangleName( method_name, ret ) ]
          for ret in method_spec.rets.keys()
      ]
      if ret_list:
        return ret_list[ 0 ]

    # FIXME: is this the right way to replcae method_port?
    method = guarded_ifc( lambda s: s.__dict__[ method_name + "_rdy" ] )(
        method )
    setattr( method, "__name__", method_name )

    setattr( self, method_name, method )

  def line_trace( s ):
    return s.model.line_trace()

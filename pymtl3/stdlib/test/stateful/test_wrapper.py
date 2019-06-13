#=========================================================================
# test_wrapper
#=========================================================================
# Wrappers for testing rtl model.
#
# Author : Yixiao Zhang
#   Date : June 10, 2019

from __future__ import absolute_import, division, print_function

import inspect

import attr
import hypothesis.strategies as st

from pymtl3 import *
from pymtl3.dsl.ComponentLevel6 import ComponentLevel6
from pymtl3.stdlib.ifcs import callee_ifc_rtl, CalleeIfcRTL


#-------------------------------------------------------------------------
# Method
#-------------------------------------------------------------------------
@attr.s()
class Method( object ):
  method_name = attr.ib()
  args = attr.ib( default={} )
  rets_type = attr.ib( default={} )


#-------------------------------------------------------------------------
# rename
#-------------------------------------------------------------------------
def rename( name ):

  def wrap( f ):
    f.__name__ = name
    return f

  return wrap


#-------------------------------------------------------------------------
# inspect_rtl
#-------------------------------------------------------------------------
def inspect_rtl( rtl ):
  method_specs = {}

  for method, ifc in inspect.getmembers( rtl ):
    if isinstance( ifc, CalleeIfcRTL ):
      args = ifc.args._dsl.Type.fields if ifc.args else []
      rets_type = ifc.rets._dsl.Type if ifc.rets else None
      ifc.method_spec = Method(
          method_name=method, args=args, rets_type=rets_type )
      method_specs[ method ] = ifc.method_spec

  return method_specs


#-------------------------------------------------------------------------
# RTL2CLWrapper
#-------------------------------------------------------------------------
class RTL2CLWrapper( Component ):

  def __init__( s, rtl_model ):
    super( RTL2CLWrapper, s ).__init__()

    s.model_name = type( rtl_model ).__name__

  def construct( s, rtl_model ):
    """Create adapter & add top-level method for each ifc in rtl_model
    """

    s.model = rtl_model

    s.method_specs = inspect_rtl( s.model )

    # Add adapters
    for method_name, method_spec in s.method_specs.iteritems():
      callee_ifc = NonBlockingCalleeIfc()
      setattr( s, method_name, callee_ifc )
      s.connect( callee_ifc, getattr( s.model, method_name ) )

  def line_trace( s ):
    trace = ""
    for name in s.method_specs:
      trace += str( getattr( s, name ) )
    return s.model.line_trace() + "  " + trace

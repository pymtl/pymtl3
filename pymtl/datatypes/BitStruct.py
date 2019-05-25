#=========================================================================
# BitStruct.py
#=========================================================================
# A basic BitStruct definition.
# 
# Author : Yanghui Ou
#   Date : Apr 8, 2019

from __future__ import absolute_import, division, print_function

from functools import reduce

import py

from pymtl import *


class BitStruct( object ):

  fields = []

  def to_bits( self ):
    bits_lst = []
    for name, Type in self.fields:
      if issubclass( Type, Bits ):
        bits_lst.append( Type( vars( self )[name] ) ) 
      elif issubclass( Type, BitStruct ):
        assert isinstance( vars( self )[name], BitStruct )
        bits_lst.append( vars( self )[name].to_bits() )
      else:
        raise AssertionError( 
          "Type {} cannot be translated into bits!".format( Type )
        )
    return reduce( lambda x, y : concat( x, y ), bits_lst )

  # Default line trace

  def __str__( self ):
    trace = ""
    for name, _ in self.fields:
      trace += "{}:".format( vars( self )[name] )
    return trace[:-1]
  
  # Compare only fields

  def __eq__( self, other ): 
    if type( self ) != type( other ):
      raise AssertionError(
        "Cannot compare {} against {}".format( type( self ), type( other ) )
      )
    # Maybe we should compare each fields recursively so that BitStruct can
    # support types that cannot be converted to bits?
    return self.to_bits() == other.to_bits()

  def __ne__( self, other ):
    if type( self ) != type( other ):
      raise AssertionError(
        "Cannot compare {} against {}".format( type( self ), type( other ) )
      )
    # Same thing here...
    return self.to_bits() != other.to_bits()

#-------------------------------------------------------------------------
# Dynamically generate bit struct
#-------------------------------------------------------------------------

_struct_dict = dict()
_fields_dict = dict()
_struct_tmpl = """
class {name}( BitStruct ):

  def __init__( s, {args_str} ):
{assign_str}

_struct_dict[\"{name}\"] = {name}
"""

def mk_bit_struct( name, fields, str_func=None ):

  if name in _struct_dict:
    if _fields_dict[name] == fields:
      return _struct_dict[name]
    else:
      raise AssertionError(
        "BitStruct {} has already been created!".format( name ) 
      )
  else:
    args_str   = ""
    assert_str = ""
    assign_str = ""
    for field_name, FieldType in fields:
      args_str   += "{}={}(), ".format( field_name, FieldType.__name__ )
      # I decided not to assert constructor arg type at the moment. 
      # assert_str += "    assert isinstance( {}, {} )\n".format( field_name, FieldType.__name__ ) 
      assign_str += "    s.{} = {}\n".format( field_name, field_name )
    args_str = args_str[:-2]

    exec(py.code.Source(
      _struct_tmpl.format( **locals() )
    ).compile(), globals())

    cls = _struct_dict[name]

    cls.fields = fields
    if str_func is not None:
      cls.__str__ = str_func

    _fields_dict[name] = fields
    return _struct_dict[name]

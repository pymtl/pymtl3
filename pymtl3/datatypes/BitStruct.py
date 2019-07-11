"""
#=========================================================================
# BitStruct.py
#=========================================================================
# A basic BitStruct definition.
#
# Author : Yanghui Ou
#   Date : Apr 8, 2019
"""
from __future__ import absolute_import, division, print_function

from functools import reduce

import py

from .bits_import import *
from .helpers import concat


class BitStruct( object ):

  fields = []
  nbits = 0

  def to_bits( self ):
    bits_lst = []
    assert self.fields, \
        "fields of BitStruct {} are not specified!".format( self.__class__.__name__ )
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

  # TODO: better error message.
  @classmethod
  def field_nbits( cls, field_name ):
    for fname, FieldType in cls.fields:
      if field_name == fname:
        return FieldType.nbits
    raise AssertionError(
      "{} does not have field {}!".format( cls.__name__, field_name )
    )

  # Default __str__ function

  def __str__( self ):
    trace = ""
    for name, _ in self.fields:
      trace += "{}:".format( vars( self )[name] )
    return trace[:-1]

  # Compare only fields
  # TODO: figure out how frequently user might directly compare the whole
  # struct as the comparison between structs can be slow. We assume this
  # would mainly happen in test sinks.
  def __eq__( self, other ):
    if type( self ) != type( other ):
      raise AssertionError(
        "Cannot compare {} against {}".format( type( self ), type( other ) )
      )
    # TODO: figure out whether we should just compare each fields
    # recursively so that it supports types that cannot be converted to bits?
    return self.to_bits() == other.to_bits()
  
  def __hash__( self ):
    return hash((self.__class__, self.to_bits()))

  def __ne__( self, other ):
    if type( self ) != type( other ):
      raise AssertionError(
        "Cannot compare {} against {}".format( type( self ), type( other ) )
      )
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

  def __hash__( s ):
    return hash(({hash_str}))

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
    # Check for duplicate fields first.
    # TODO: better error message
    keys = [ fname for fname, _ in fields ]
    if any( keys.count(k) > 1 for k in keys):
      raise AssertionError(
        "Failed to create {} due to duplicate fields!".format( name )
      )

    args_str   = ""
    assign_str = ""
    hash_str = name + ", "
    nbits      = 0
    for field_name, FieldType in fields:
      nbits += FieldType.nbits
      args_str   += "{}={}(), ".format( field_name, FieldType.__name__ )
      assign_str += "    s.{} = {}\n".format( field_name, field_name )
      hash_str += "s.{}, ".format(field_name)
    args_str = args_str[:-2]

    tmpl = _struct_tmpl.format( **locals() )
    exec( py.code.Source( tmpl ).compile(), globals() )

    cls = _struct_dict[name]

    cls.fields = fields
    cls.nbits  = nbits
    if str_func is not None:
      cls.__str__ = str_func

    _fields_dict[name] = fields
    return _struct_dict[name]

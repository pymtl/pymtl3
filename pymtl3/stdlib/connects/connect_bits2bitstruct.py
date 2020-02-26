'''
==========================================================================
connect_bits2bitstruct.py
==========================================================================
A connect function that connects a bits signal and a bitsrtuct signal that
has the same width.

Author : Yanghui Ou
  Date : Feb 24, 2020
'''
from pymtl3 import Bits, connect
from pymtl3.datatypes.bitstructs import _FIELDS, is_bitstruct_class

#-------------------------------------------------------------------------
# _connect_bits2bitstruct_h
#-------------------------------------------------------------------------
# Helper function for connect_bits2bitstruct.

def _connect_bits2bitstruct_h( field, bits_signal, slices ):

  # NOTE: We do not support list of fields at the moment because: 1) there
  # are very few use cases; 2) the pack order of a list of fields is
  # somewhat ambiguous.
  if isinstance( field, list ):
    assert False, 'A list of fields is not supported at the moment.'

  field_type = field.get_type()

  if issubclass( field_type, Bits ):
    start     = 0 if not slices else slices[-1].stop
    stop      = start + field_type.nbits
    cur_slice = slice( start, stop )
    slices.append( cur_slice )
    connect( field, bits_signal[ cur_slice ] )

  else:
    assert is_bitstruct_class( field_type )
    fields_dict = getattr( field_type, _FIELDS )
    fields_lst  = list( fields_dict.items() )
    fields_lst.reverse() # reverse is faster than [::-1]
    for fname, _ in fields_lst:
      subfield = getattr( field, fname )
      _connect_bits2bitstruct_h( subfield, bits_signal, slices )

#-------------------------------------------------------------------------
# connect_bits2bitstruct
#-------------------------------------------------------------------------

def connect_bits2bitstruct( signal1, signal2 ):
  type1 = signal1.get_type()
  type2 = signal2.get_type()

  if is_bitstruct_class( type1 ):
    assert issubclass( type2, Bits ), \
      f'Connecting {type1.__qualname__} to {type2.__qualname__}: ' \
      f'{type1.__qualname__} is a bitstruct ' \
      f'but {type2.__qualname__} is not a Bits type!'
    bits_signal, bitstruct_signal = signal2, signal1

  elif is_bitstruct_class( type2 ):
    assert issubclass( type1, Bits ), \
      f'Connecting {type1.__qualname__} to {type2.__qualname__}: ' \
      f'{type2.__qualname__} is a bitstruct ' \
      f'but {type1.__qualname__} is not a Bits type!'
    bits_signal, bitstruct_signal = signal1, signal2

  else:
    assert False, 'Can only connect a bitstruct wire to bits wire'

  # Connect field to corresponding slice
  _connect_bits2bitstruct_h( bitstruct_signal, bits_signal, [] )

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

def _connect_bits2bitstruct_h( field, bits_signal, start ):

  # NOTE: We do not support list of fields at the moment because: 1) there
  # are very few use cases; 2) the pack order of a list of fields is
  # somewhat ambiguous.
  if isinstance( field, list ):
    assert False, 'A list of fields is not supported at the moment.'

  field_type = field.get_type()

  if issubclass( field_type, Bits ):
    stop      = start + field_type.nbits
    cur_slice = slice( start, stop )
    connect( field, bits_signal[ cur_slice ] )
    return stop

  else:
    fields_dict = getattr( field_type, _FIELDS )
    cur_stop    = start
    for fname, _ in reversed( list( fields_dict.items() ) ):
      subfield = getattr( field, fname )
      cur_stop = _connect_bits2bitstruct_h( subfield, bits_signal, cur_stop )
    return cur_stop

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

  bw1 = type1.nbits
  bw2 = type2.nbits
  assert bw1 == bw2, 'Bitwidth mismatch! ' \
    f'{type1.__qualname__} is {bw1}-bit ' \
    f'but {type2.__qualname__} is {bw2}-bit.'

  # Connect field to corresponding slice
  stop = _connect_bits2bitstruct_h( bitstruct_signal, bits_signal, 0 )
  assert stop == bw1, 'Sanity check failed! Might be a bug. ' \
    'Please create a Github issue.'

"""
==========================================================================
ChecksumFL.py
==========================================================================
Functional-level implementation of a checksum unit which implements a
simplified version of Fletcher's algorithm. Here is a straightforward C
implementation for the classic version:

  uint32_t Fletcher32( uint16_t* data, int count )
  {
    uint32_t sum1 = 0;
    uint32_t sum2 = 0;

    for( int index = 0; index < count; index++ ) {
      sum1 = ( sum1 + data[index] ) % 65535;
      sum2 = ( sum2 + sum1        ) % 65535;
    }

    return ( sum2 << 16 ) | sum1;
  }

In our simplified version, we will use 65536 as the modulus which means
we can implement the modulus with a mask.

Author : Yanghui Ou, Christopher Batten
  Date : June 6, 2019
"""
from pymtl3 import *

#-------------------------------------------------------------------------
# Checksum FL
#-------------------------------------------------------------------------

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the functional-level checksum here
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Use the pseudocode above for inspiration. Use Bits to implement
#; fixed bitwidth types (e.g., Bits32 for uint32_t). Modulus 65536 is the
#; same as anding with 0xffff.

def checksum( words ):

  sum1 = b16(0)
  sum2 = b16(0)
  for word in words:
    sum1 = ( sum1 + word ) & 0xffff
    sum2 = ( sum2 + sum1 ) & 0xffff

  return concat( sum2, sum1 )

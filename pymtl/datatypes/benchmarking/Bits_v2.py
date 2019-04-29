from __future__ import division, print_function

import copy
from builtins import object

from past.utils import old_div

# =======================================================================
# Bits.py
# =======================================================================
# Module containing the Bits class.


# -----------------------------------------------------------------------
# _get_nbits
# -----------------------------------------------------------------------
def _get_nbits(N):
    "Utility class for calculating number of bits needed to store a value"
    if N > 0:
        return N.bit_length()
    else:
        return N.bit_length() + 1


# -----------------------------------------------------------------------
# Bits
# -----------------------------------------------------------------------
class Bits(object):
    "Class emulating limited precision values of a fixed bitwidth."

    # ---------------------------------------------------------------------
    # __init__
    # ---------------------------------------------------------------------
    def __init__(self, nbits, value=0, trunc=False):

        value = int(value)
        nbits = int(nbits)

        # Make sure width is non-zero and that we have space for the value
        if not (nbits > 0):
            raise ValueError("The value of nbits must be > 0!")

        # Set the nbits and bitmask (_mask) attributes
        self.nbits = nbits

        # Convert negative values into unsigned ints and store them
        value_uint = value if (value >= 0) else (~(-value) + 1)
        self._uint = value_uint & ((1 << self.nbits) - 1)

        self._target_bits = self

    # ---------------------------------------------------------------------
    # __call__
    # ---------------------------------------------------------------------
    # Allow Bits to act like a type that can be instantiated.
    def __call__(self):
        return Bits(self.nbits)

    # ---------------------------------------------------------------------
    # __int__
    # ---------------------------------------------------------------------
    # Type conversion to an int.
    def __int__(self):
        return int(self._uint)

    # ---------------------------------------------------------------------
    # __long__
    # ---------------------------------------------------------------------
    # Type conversion to a long.
    def __long__(self):
        return int(self._uint)

    # ---------------------------------------------------------------------
    # __index__
    # ---------------------------------------------------------------------
    # Behave like an int() when used as an index to slices.
    def __index__(self):
        return self._uint

    # ---------------------------------------------------------------------
    # uint
    # ---------------------------------------------------------------------
    # Return the unsigned integer representation of the bits.
    def uint(self):
        return self._uint

    # ---------------------------------------------------------------------
    # int
    # ---------------------------------------------------------------------
    # Return the integer representation of the bits.
    def int(self):
        if self[self.nbits - 1]:
            twos_complement = ~self + 1
            return -twos_complement._uint
        else:
            return self._uint

    # ---------------------------------------------------------------------
    # bit_length
    # ---------------------------------------------------------------------
    # Implement bit_length method provided by the int built-in. Simplifies
    # the implementation of get_nbits().
    def bit_length(self):
        return self._uint.bit_length()

    # ---------------------------------------------------------------------
    # Print Methods
    # ---------------------------------------------------------------------

    def __repr__(self):
        return "Bits( {0}, {1} )".format(self.nbits, self.hex())

    def __str__(self):
        num_chars = (old_div((self.nbits - 1), 4)) + 1
        str = "{:x}".format(self._uint).zfill(num_chars)
        return str

    def __oct__(self):
        print("DEPRECATED: Please use .oct()!")
        return self.oct()

    def __hex__(self):
        print("DEPRECATED: Please use .oct()!")
        return self.hex()

    def bin(self):
        str = "{:b}".format(self._uint).zfill(self.nbits)
        return "0b" + str

    def oct(self):
        num_chars = (old_div((self.nbits - 1), 2)) + 1
        str = "{:o}".format(self._uint).zfill(num_chars)
        return "0o" + str

    def hex(self):
        num_chars = (old_div((self.nbits - 1), 4)) + 1
        str = "{:x}".format(self._uint).zfill(num_chars)
        return "0x" + str

    # ----------------------------------------------------------------------
    # __getitem__
    # ----------------------------------------------------------------------
    # Read a subset of bits in the Bits object.
    def __getitem__(self, addr):

        # TODO: optimize this logic?

        # Handle slices
        if isinstance(addr, slice):

            if addr.step:
                raise IndexError(
                    "Bits slicing using steps [start:stop:step] is not supported"
                )

            # Parse address range
            start = addr.start
            stop = addr.stop

            # Open-ended range ( [:] ), return a copy of self
            if start is None and stop is None:
                return copy.copy(self)

            # Open-ended range on left ( [:N] )
            elif start is None:
                start = 0

            # Open-ended range on right ( [N:] )
            elif stop is None:
                stop = self.nbits

            stop = int(stop)
            start = int(start)

            # Verify our ranges are sane
            if not (start < stop):
                raise IndexError(
                    "Bits slicing start index is not less than stop index"
                    "[start={}:stop={}]".format(start, stop)
                )
            if not (0 <= start < stop <= self.nbits):
                raise IndexError(
                    "Bits slice indices [{}:{}] out of range [0 - {}]".format(
                        start, stop, self.nbits
                    )
                )

            # Create a new Bits object containing the slice value and return it
            nbits = stop - start
            mask = (1 << nbits) - 1
            value = (self._uint & (mask << start)) >> start
            return BitSlice(nbits, value, target_bits=self, offset=start)

        # Handle integers
        else:

            addr = int(addr)

            # Verify the index is sane
            if not (0 <= addr < self.nbits):
                raise IndexError(
                    "Bits index [{}] out of range [0 - {}]".format(addr, self.nbits)
                )

            # Create a new Bits object containing the bit value and return it
            value = (self._uint & (1 << addr)) >> addr
            return BitSlice(1, value, target_bits=self, offset=addr)

    # ----------------------------------------------------------------------
    # __setitem__
    # ----------------------------------------------------------------------
    # Write a subset of bits in the Bits object.
    def __setitem__(self, addr, value):

        # TODO: optimize this logic?

        value = int(value)

        # Handle slices
        if isinstance(addr, slice):

            if addr.step:
                raise IndexError(
                    "Bits slicing using steps [start:stop:step] is not supported"
                )

            # Parse address range
            start = addr.start
            stop = addr.stop

            # Open-ended range ( [:] )
            if start is None and stop is None:
                if not (self._min <= value <= self._max):
                    raise ValueError(
                        "Provided value is too big to be represented with Bits({})!\n"
                        "({} bits are needed to represent value = {} in two's complement.)".format(
                            self.nbits, _get_nbits(value), value
                        )
                    )
                self._uint = value
                return

            # Open-ended range on left ( [:N] )
            elif start is None:
                start = 0

            # Open-ended range on right ( [N:] )
            elif stop is None:
                stop = self.nbits

            # Verify our ranges are sane
            if not (start < stop):
                raise IndexError(
                    "Bits slicing start index is not less than stop index"
                    "[start={}:stop={}]".format(start, stop)
                )
            if not (0 <= start < stop <= self.nbits):
                raise IndexError(
                    "Bits slice indices [{}:{}] out of range [0 - {}]".format(
                        start, stop, self.nbits
                    )
                )

            nbits = stop - start

            # This assert fires if the value you are trying to store is wider
            # than the bitwidth of the slice you are writing to!
            if not (nbits >= _get_nbits(value)):
                raise ValueError(
                    "Provided value is too big to fit in slice [{}:{}] ({} bits)!\n"
                    "({} bits are needed to represent value = {} in two's complement.)".format(
                        start, stop, nbits, _get_nbits(value), value
                    )
                )

            # Clear the bits we want to set
            ones = (1 << nbits) - 1
            mask = ~(ones << start)
            cleared_val = self._uint & mask

            # Set the bits, anding with ones to ensure negative value assign
            # works that way you would expect.
            self._uint = cleared_val | ((value & ones) << start)

        # Handle integers
        else:

            # Verify the index and values are sane
            if not (0 <= addr < self.nbits):
                raise IndexError(
                    "Bits index [{}] out of range [0 - {}]".format(addr, self.nbits)
                )
            if not (0 <= value <= 1):
                raise ValueError(
                    "Provided value is too big to fit in 1 bit!\n"
                    "({} bits are needed to represent value = {} in two's complement.)".format(
                        _get_nbits(value), value
                    )
                )

            # Clear the bits we want to set
            mask = ~(1 << int(addr))
            cleared_val = self._uint & mask

            # Set the bits
            self._uint = cleared_val | (value << addr)

    # ----------------------------------------------------------------------
    # Arithmetic Operators
    # ----------------------------------------------------------------------
    # For now, let's make the width equal to the max of the widths of the
    # two operands. These semantics match Verilog:
    # http://www1.pldworld.com/@xilinx/html/technote/TOOL/MANUAL/21i_doc/data/fndtn/ver/ver4_4.htm

    def __invert__(self):
        return Bits(self.nbits, ~self._uint, trunc=True)

    def __add__(self, other):
        try:
            return Bits(
                max(self.nbits, other.nbits), self._uint + other._uint, trunc=True
            )
        except:
            return Bits(self.nbits, self._uint + other, trunc=True)

    def __sub__(self, other):
        try:
            return Bits(
                max(self.nbits, other.nbits), self._uint - other._uint, trunc=True
            )
        except:
            return Bits(self.nbits, self._uint - other, trunc=True)

    # TODO: what about multiplying Bits object with an object of other type
    # where the bitwidth of the other type is larger than the bitwidth of the
    # Bits object? ( applies to every other operator as well.... )
    def __mul__(self, other):
        try:
            return Bits(
                2 * max(self.nbits, other.nbits), self._uint * other._uint, trunc=True
            )
        except:
            return Bits(2 * self.nbits, self._uint * other, trunc=True)

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return Bits(_get_nbits(other), other) - self

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        try:
            return Bits(
                2 * max(self.nbits, other.nbits),
                old_div(self._uint, other._uint),
                trunc=True,
            )
        except:
            return Bits(2 * self.nbits, old_div(self._uint, other), trunc=True)

    def __floordiv__(self, other):
        try:
            return Bits(
                2 * max(self.nbits, other.nbits),
                old_div(self._uint, other._uint),
                trunc=True,
            )
        except:
            return Bits(2 * self.nbits, old_div(self._uint, other), trunc=True)

    def __mod__(self, other):
        try:
            return Bits(
                2 * max(self.nbits, other.nbits), self._uint % other._uint, trunc=True
            )
        except:
            return Bits(2 * self.nbits, self._uint % other, trunc=True)

    # TODO: implement these?
    # def __divmod__(self, other)
    # def __pow__(self, other[, modulo])

    # ----------------------------------------------------------------------
    # Shift Operators
    # ----------------------------------------------------------------------

    def __lshift__(self, other):
        # Optimization to return 0 if shift amount is greater than self.nbits
        if int(other) >= self.nbits:
            return Bits(self.nbits, 0)
        return Bits(self.nbits, self._uint << int(other), trunc=True)

    def __rshift__(self, other):
        return Bits(self.nbits, self._uint >> int(other))

    # TODO: Not implementing reflective operators because its not clear
    #       how to determine width of other object in case of lshift
    # def __rlshift__(self, other):
    #  return self.__lshift__( other )
    # def __rrshift__(self, other):
    #  return self.__rshift__( other )

    # ----------------------------------------------------------------------
    # Bitwise Operators
    # ----------------------------------------------------------------------

    def __and__(self, other):
        assert other >= 0
        try:
            return Bits(
                max(self.nbits, other.nbits), self._uint & other._uint, trunc=True
            )
        except:
            return Bits(self.nbits, self._uint & other, trunc=True)

    def __xor__(self, other):
        assert other >= 0
        try:
            return Bits(
                max(self.nbits, other.nbits), self._uint ^ other._uint, trunc=True
            )
        except:
            return Bits(self.nbits, self._uint ^ other, trunc=True)

    def __or__(self, other):
        assert other >= 0
        try:
            return Bits(
                max(self.nbits, other.nbits), self._uint | other._uint, trunc=True
            )
        except:
            return Bits(self.nbits, self._uint | other, trunc=True)

    def __rand__(self, other):
        return self.__and__(other)

    def __rxor__(self, other):
        return self.__xor__(other)

    def __ror__(self, other):
        return self.__or__(other)

    # ----------------------------------------------------------------------
    # Comparison Operators
    # ----------------------------------------------------------------------

    def __bool__(self):
        return self._uint != 0

    # TODO: allow comparison with negative numbers?
    def __eq__(self, other):
        if other is None:
            return False
        assert other >= 0
        return self._uint == other

    def __ne__(self, other):
        if other is None:
            return True
        assert other >= 0
        return self._uint != other

    def __lt__(self, other):
        assert other >= 0
        return self._uint < other

    def __le__(self, other):
        assert other >= 0
        return self._uint <= other

    def __gt__(self, other):
        assert other >= 0
        return self._uint > other

    def __ge__(self, other):
        assert other >= 0
        return self._uint >= other

    # ----------------------------------------------------------------------
    # Extension
    # ----------------------------------------------------------------------
    # TODO: make abstract method in SignalValue, or implement differently?

    def _zext(self, new_width):
        return Bits(new_width, self._uint)

    def _sext(self, new_width):
        return Bits(new_width, self.int())


class BitSlice(Bits):

    # ---------------------------------------------------------------------
    # __init__
    # ---------------------------------------------------------------------
    def __init__(self, nbits, value, target_bits, offset):

        # Create the BitSlice object using the Bits constructor.
        super(BitSlice, self).__init__(nbits, value)

        # Extra fields specific to BitSlices: _target_bits points to the
        # Bits object we are slicing, _offset provides the position of the
        # specific bits we are slicing.
        self._target_bits = target_bits
        self._offset = offset
        self.slice = slice(offset, offset + nbits)

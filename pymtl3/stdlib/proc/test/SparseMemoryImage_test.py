#=========================================================================
# SparseMemoryImage_test.py
#=========================================================================

import copy
import random
import struct

from ..SparseMemoryImage import SparseMemoryImage

#-------------------------------------------------------------------------
# test_sections
#-------------------------------------------------------------------------

def test_sections():

  # The sparse memory image we will be testing

  mem_image = SparseMemoryImage()

  # Create first bytearray with some data

  data_ints_a  = [ random.randint(0,1000) for r in range(10) ]
  data_bytes_a = bytearray()
  for data_int in data_ints_a:
    data_bytes_a.extend(struct.pack("<I",data_int))

  # Create a second section section and add it to the sparse memory image

  section_a = SparseMemoryImage.Section( ".text", 0x1000, data_bytes_a )
  mem_image.add_section( section_a )

  # Create a second bytearray with some data

  data_ints_b  = [ random.randint(0,1000) for r in range(10) ]
  data_bytes_b = bytearray()
  for data_ints in data_ints_b:
    data_bytes_b.extend(struct.pack("<I",data_int))

  # Create a second section section and add it to the sparse memory
  # image. Use the alternative syntax for adding a section.

  section_b = SparseMemoryImage.Section( ".data", 0x2000, data_bytes_b )
  mem_image.add_section( ".data", 0x2000, data_bytes_b )

  # Retrieve and check both sections

  section_a_test = mem_image.get_section( ".text" )
  assert section_a_test == section_a

  section_b_test = mem_image.get_section( ".data" )
  assert section_b_test == section_b

  # Retrieve sections as a list

  sections_test = mem_image.get_sections()
  assert sections_test == [ section_a_test, section_b_test ]

#-------------------------------------------------------------------------
# test_equality
#-------------------------------------------------------------------------

def test_equality():

  # The sparse memory image we will be testing

  mem_image = SparseMemoryImage()

  # Create first bytearray with some data

  data_ints_a  = [ random.randint(0,1000) for r in range(10) ]
  data_bytes_a = bytearray()
  for data_int in data_ints_a:
    data_bytes_a.extend(struct.pack("<I",data_int))

  # Create a second section section and add it to the sparse memory image

  section_a = SparseMemoryImage.Section( ".text", 0x1000, data_bytes_a )
  mem_image.add_section( section_a )

  # Create a second bytearray with some data

  data_ints_b  = [ random.randint(0,1000) for r in range(10) ]
  data_bytes_b = bytearray()
  for data_ints in data_ints_b:
    data_bytes_b.extend(struct.pack("<I",data_int))

  # Create a second section section and add it to the sparse memory image

  section_b = SparseMemoryImage.Section( ".data", 0x2000, data_bytes_b )
  mem_image.add_section( section_b )

  # Create a copy

  mem_image_copy = copy.deepcopy( mem_image )

  # Check two images are equal

  assert mem_image == mem_image_copy

  # Add another section to the copy

  section_c = SparseMemoryImage.Section( ".test", 0x3000, bytearray(b"\x01\x02") )
  mem_image_copy.add_section( section_c )

  # Check two images are no longer equal

  assert mem_image != mem_image_copy

#-------------------------------------------------------------------------
# test_symbols
#-------------------------------------------------------------------------

def test_symbols():

  # The sparse memory image we will be testing

  mem_image = SparseMemoryImage()

  # Add some symbols

  mem_image.add_symbol( "func_a", 0x0002000 )
  mem_image.add_symbol( "func_b", 0x0003000 )
  mem_image.add_symbol( "var_a",  0x0011000 )
  mem_image.add_symbol( "var_b",  0x0011000 )

  # Check symbols

  assert mem_image.get_symbol( "func_a" ) == 0x0002000
  assert mem_image.get_symbol( "func_b" ) == 0x0003000
  assert mem_image.get_symbol( "var_a"  ) == 0x0011000
  assert mem_image.get_symbol( "var_b"  ) == 0x0011000

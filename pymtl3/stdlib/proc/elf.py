#=========================================================================
# elf
#=========================================================================
# A simple translator between ELF files and a sparse memory image object.
# Note that the translator is far from complete but is sufficient for use
# in our research processors. I found this document pretty useful for
# understanding the ELF32 format:
#
#  http://docs.oracle.com/cd/E19457-01/801-6737/801-6737.pdf
#
# Note that this implementation is inspired by the ELF object file reader
# here:
#
#  http://www.tinyos.net/tinyos-1.x/tools/src/mspgcc-pybsl/elf.py
#
# which includes this copyright:
#
#  (C) 2003 cliechti@gmx.net
#  Python license
#
# Shunning: I ported it to Python3 today and it is a bit interesting due
# to the recent bytes/str disambiguation in Python3. Basically, there
# are several changes worth noting:
# - Currently file_obj.read() will return _bytes_ instead of str, so if
#   we want to use the variable as string, we need to perform
#   bytes.decode().
# - struct.unpack only works for string/bytearray (I guess?) so I had to
#   use bytearray(bytes_obj) to avoid any changes to struct.unpack and the
#   format string.
# - Whenever we write the elf file, we have to convert the strings back
#   to bytes. Just keep in mind that for string purposes we need to decode
#   and encode back.
#
# Author : Christopher Batten, Shunning Jiang
# Date   : Feb 26, 2020

import struct

from .SparseMemoryImage import SparseMemoryImage

#-------------------------------------------------------------------------
# ELF File Format Types
#-------------------------------------------------------------------------
# These are the sizes for various ELF32 data types used in describing
# various structures below.
#
#            size alignment
# elf_addr   4    4  Unsigned program address
# elf_half   2    2  Unsigned medium integer
# elf_off    4    4  Unsigned file offset
# elf_sword  4    4  Signed   large integer
# elf_word   4    4  Unsigned large integer
# elf_byte   1    1  Unsigned small integer

#=========================================================================
# ElfHeader
#=========================================================================
# Class encapsulating an ELF32 header which implements the following
# C-structure.
#
# define EI_NIDENT 16
# typedef struct {
#   elf_byte e_ident[EI_NIDENT];
#   elf_half e_type;
#   elf_half e_machine;
#   elf_word e_version;
#   elf_addr e_entry;
#   elf_off  e_phoff;
#   elf_off  e_shoff;
#   elf_word e_flags;
#   elf_half e_ehsize;
#   elf_half e_phentsize;
#   elf_half e_phnum;
#   elf_half e_shentsize;
#   elf_half e_shnum;
#   elf_half e_shstrndx;
# } elf_ehdr;

class ElfHeader:

  FORMAT = "<16sHHIIIIIHHHHHH"
  NBYTES = struct.calcsize( FORMAT )

  # Offsets within e_ident

  IDENT_NBYTES      = 16     # Size of e_ident[]
  IDENT_IDX_MAG0    = 0      # File identification
  IDENT_IDX_MAG1    = 1      # File identification
  IDENT_IDX_MAG2    = 2      # File identification
  IDENT_IDX_MAG3    = 3      # File identification
  IDENT_IDX_CLASS   = 4      # File class
  IDENT_IDX_DATA    = 5      # Data encoding
  IDENT_IDX_VERSION = 6      # File version
  IDENT_IDX_PAD     = 7      # Start of padding bytes

  # Elf file type flags

  TYPE_NONE         = 0      # No file type
  TYPE_REL          = 1      # Relocatable file
  TYPE_EXEC         = 2      # Executable file
  TYPE_DYN          = 3      # Shared object file
  TYPE_CORE         = 4      # Core file
  TYPE_LOPROC       = 0xff00 # Processor-specific
  TYPE_HIPROC       = 0xffff # Processor-specific

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, data=None ):
    if data != None:
      self.from_bytes( data )

  #-----------------------------------------------------------------------
  # from_bytes
  #-----------------------------------------------------------------------

  def from_bytes( self, data ):
    ehdr_list = struct.unpack( ElfHeader.FORMAT, bytearray(data) )
    self.ident     = ehdr_list[0].decode()
    self.type      = ehdr_list[1]
    self.machine   = ehdr_list[2]
    self.version   = ehdr_list[3]
    self.entry     = ehdr_list[4]
    self.phoff     = ehdr_list[5]
    self.shoff     = ehdr_list[6]
    self.flags     = ehdr_list[7]
    self.ehsize    = ehdr_list[8]
    self.phentsize = ehdr_list[9]
    self.phnum     = ehdr_list[10]
    self.shentsize = ehdr_list[11]
    self.shnum     = ehdr_list[12]
    self.shstrndx  = ehdr_list[13]

  #-----------------------------------------------------------------------
  # to_bytes
  #-----------------------------------------------------------------------

  def to_bytes( self ):
    return struct.pack( ElfHeader.FORMAT,
      self.ident.encode(),
      self.type,
      self.machine,
      self.version,
      self.entry,
      self.phoff,
      self.shoff,
      self.flags,
      self.ehsize,
      self.phentsize,
      self.phnum,
      self.shentsize,
      self.shnum,
      self.shstrndx,
   )

  #-----------------------------------------------------------------------
  # __str__
  #-----------------------------------------------------------------------

  def __str__( self ):
    return \
"""
 ElfHeader:
   ident     = {},
   type      = {},
   machine   = {},
   version   = {},
   entry     = {},
   phoff     = {},
   shoff     = {},
   flags     = {},
   ehsize    = {},
   phentsize = {},
   phnum     = {},
   shentsize = {},
   shnum     = {},
   shstrndx  = {}
""".format(
   self.ident,
   self.type,
   self.machine,
   self.version,
   hex(self.entry),
   hex(self.phoff),
   hex(self.shoff),
   hex(self.flags),
   self.ehsize,
   self.phentsize,
   self.phnum,
   self.shentsize,
   self.shnum,
   self.shstrndx,
)

#=========================================================================
# ElfSectionHeader
#=========================================================================
# Class encapsulating an ELF32 section header which implements the
# following C-structure.
#
# typedef struct {
#   elf_word sh_name;
#   elf_word sh_type;
#   elf_word sh_flags;
#   elf_addr sh_addr;
#   elf_off  sh_offset;
#   elf_word sh_size;
#   elf_word sh_link;
#   elf_word sh_info;
#   elf_word sh_addralign;
#   elf_word sh_entsize;
# } elf_shdr;
#

class ElfSectionHeader:

  FORMAT = "<IIIIIIIIII"
  NBYTES = struct.calcsize( FORMAT )

  # Section types. Note that we only load some of these sections.

  TYPE_NULL        = 0
  TYPE_PROGBITS    = 1 # \
  TYPE_SYMTAB      = 2 # | We only load sections of these types
  TYPE_STRTAB      = 3 # /
  TYPE_RELA        = 4
  TYPE_HASH        = 5
  TYPE_DYNAMIC     = 6
  TYPE_NOTE        = 7
  TYPE_NOBITS      = 8
  TYPE_REL         = 9
  TYPE_SHLIB       = 10
  TYPE_DYNSYM      = 11
  TYPE_LOPROC      = 0x70000000
  TYPE_HIPROC      = 0x7fffffff
  TYPE_LOUSER      = 0x80000000
  TYPE_HIUSER      = 0xffffffff

  # Section attribute flags. Note that we only load sections with the
  # SHF_ALLOC flag set into the actual sparse memory.

  FLAGS_WRITE       = 0x1
  FLAGS_ALLOC       = 0x2
  FLAGS_EXECINSTR   = 0x4
  FLAGS_MASKPROC    = 0xf0000000

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, data=None ):
    if data != None:
      self.from_bytes( data )

  #-----------------------------------------------------------------------
  # from_bytes
  #-----------------------------------------------------------------------

  def from_bytes( self, data ):
    shdr_list = struct.unpack( ElfSectionHeader.FORMAT, bytearray(data) )
    self.name      = shdr_list[0]
    self.type      = shdr_list[1]
    self.flags     = shdr_list[2]
    self.addr      = shdr_list[3]
    self.offset    = shdr_list[4]
    self.size      = shdr_list[5]
    self.link      = shdr_list[6]
    self.info      = shdr_list[7]
    self.addralign = shdr_list[8]
    self.entsize   = shdr_list[9]

  #-----------------------------------------------------------------------
  # to_bytes
  #-----------------------------------------------------------------------

  def to_bytes( self ):
    return struct.pack( ElfSectionHeader.FORMAT,
      self.name,
      self.type,
      self.flags,
      self.addr,
      self.offset,
      self.size,
      self.link,
      self.info,
      self.addralign,
      self.entsize,
   )

  #-----------------------------------------------------------------------
  # __str__
  #-----------------------------------------------------------------------

  def __str__( self ):
    return \
"""
 ElfSectionHeader:
   name      = {},
   type      = {},
   flags     = {},
   addr      = {},
   offset    = {},
   size      = {},
   link      = {},
   info      = {},
   addralign = {},
   entsize   = {},
""".format(
   self.name,
   self.type,
   hex(self.flags),
   hex(self.addr),
   hex(self.offset),
   self.size,
   self.link,
   self.info,
   self.addralign,
   self.entsize,
)

#=========================================================================
# ElfSymTabEntry
#=========================================================================
# Class encapsulating an ELF32 symbol table entry which implements the
# following C-structure.
#
# typedef struct {
#   elf_word st_name;
#   elf_addr st_value;
#   elf_word st_size;
#   elf_byte st_info;
#   elf_byte st_other;
#   elf_half st_shndx;
# } elf_sym;
#

class ElfSymTabEntry:

  FORMAT = "<IIIBBH"
  NBYTES = struct.calcsize( FORMAT )

  # Symbol types. Note we only load some of these types.

  TYPE_NOTYPE  = 0 # \
  TYPE_OBJECT  = 1 # | We only load symbols of these types
  TYPE_FUNC    = 2 # /
  TYPE_SECTION = 3
  TYPE_FILE    = 4
  TYPE_LOPROC  = 13
  TYPE_HIPROC  = 15

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, data=None ):
    if data != None:
      self.from_bytes( data )

  #-----------------------------------------------------------------------
  # from_bytes
  #-----------------------------------------------------------------------

  def from_bytes( self, data ):
    sym_list = struct.unpack( ElfSymTabEntry.FORMAT, bytearray(data) )
    self.name  = sym_list[0]
    self.value = sym_list[1]
    self.size  = sym_list[2]
    self.info  = sym_list[3]
    self.other = sym_list[4]
    self.shndx = sym_list[5]

  #-----------------------------------------------------------------------
  # to_bytes
  #-----------------------------------------------------------------------

  def to_bytes( self ):
    return struct.pack( ElfSymTabEntry.FORMAT,
      self.name,
      self.value,
      self.size,
      self.info,
      self.other,
      self.shndx,
   )

  #-----------------------------------------------------------------------
  # __str__
  #-----------------------------------------------------------------------

  def __str__( self ):
    return \
"""
 ElfSymTabEntry:
   ident     = {}
   value     = {}
   size      = {}
   info      = {}
   other     = {}
   shndx     = {}
""".format(
   self.name,
   hex(self.value),
   self.size,
   self.info,
   self.other,
   self.shndx,
)

#-------------------------------------------------------------------------
# elf_reader
#-------------------------------------------------------------------------
# Opens and parses an ELF file into a sparse memory image object.

def elf_reader( file_obj ):

  # Read the data for the ELF header

  ehdr_data = file_obj.read( ElfHeader.NBYTES )

  # Construct an ELF header object

  ehdr = ElfHeader( ehdr_data )

  # Verify if its a known format and really an ELF file

  if ehdr.ident[0:4] != '\x7fELF':
    raise ValueError( "Not a valid ELF file" )

  # We need to find the section string table so we can figure out the
  # name of each section. We know that the section header for the section
  # string table is entry shstrndx, so we first get the data for this
  # section header.

  file_obj.seek( ehdr.shoff + ehdr.shstrndx * ehdr.shentsize )
  shdr_data = file_obj.read(ehdr.shentsize)

  # Construct a section header object for the section string table

  shdr = ElfSectionHeader( shdr_data )

  # Read the data for the section header table

  file_obj.seek( shdr.offset )
  shstrtab_data = file_obj.read( shdr.size ).decode() # this is used as string!

  # Load sections

  symtab_data = None
  strtab_data = None

  mem_image = SparseMemoryImage()

  for section_idx in range(ehdr.shnum):

    # Read the data for the section header

    file_obj.seek( ehdr.shoff + section_idx * ehdr.shentsize )
    shdr_data = file_obj.read(ehdr.shentsize)

    # Pad the returned string in case the section header is not long
    # enough (otherwise the unpack function would not work)

    shdr_data = shdr_data.ljust( ElfSectionHeader.NBYTES, b'\0' )

    # Construct a section header object

    shdr = ElfSectionHeader( shdr_data )

    # Find the section name

    start = shstrtab_data[shdr.name:]
    section_name = start.partition('\0')[0]

    # Only sections marked as alloc should be written to memory

    if not ( shdr.flags & ElfSectionHeader.FLAGS_ALLOC ):
      continue

    # Read the section data if it exists

    if section_name not in ['.sbss', '.bss']:
      file_obj.seek( shdr.offset )
      data = file_obj.read( shdr.size )

    # NOTE: the .bss and .sbss sections don't actually contain any
    # data in the ELF.  These sections should be initialized to zero.
    # For more information see:
    #
    # - http://stackoverflow.com/questions/610682/bss-section-in-elf-file

    else:
      data = b'\0' * shdr.size

    # Save the data holding the symbol string table

    if shdr.type == ElfSectionHeader.TYPE_STRTAB:
      strtab_data = data

    # Save the data holding the symbol table

    elif shdr.type == ElfSectionHeader.TYPE_SYMTAB:
      symtab_data = data

    # Otherwise create section and append it to our list of sections

    else:
      section = SparseMemoryImage.Section( section_name, shdr.addr, data )
      mem_image.add_section( section )

  # Load symbols. We skip the first symbol since it both "designates the
  # first entry in the table and serves as the undefined symbol index".
  # For now, I have commented this out, since we are not really using it.

  # num_symbols = len(symtab_data) / ElfSymTabEntry.NBYTES
  # for sym_idx in xrange(1,num_symbols):
  #
  #   # Read the data for a symbol table entry
  #
  #   start = sym_idx * ElfSymTabEntry.NBYTES
  #   sym_data = symtab_data[start:start+ElfSymTabEntry.NBYTES]
  #
  #   # Construct a symbol table entry
  #
  #   sym = ElfSymTabEntry( sym_data )
  #
  #   # Get the symbol type
  #
  #   sym_type  = sym.info & 0xf
  #
  #   # Check to see if symbol is one of the three types we want to load
  #
  #   valid_sym_types = \
  #   [
  #     ElfSymTabEntry.TYPE_NOTYPE,
  #     ElfSymTabEntry.TYPE_OBJECT,
  #     ElfSymTabEntry.TYPE_FUNC,
  #   ]
  #
  #   # Check to see if symbol is one of the three types we want to load
  #
  #   if sym_type not in valid_sym_types:
  #     continue
  #
  #   # Get the symbol name from the string table
  #
  #   start = strtab_data[sym.name:]
  #   name = start.partition('\0')[0]
  #
  #   # Add symbol to the sparse memory image
  #
  #   mem_image.add_symbol( name, sym.value )

  return mem_image

#-------------------------------------------------------------------------
# elf_writer
#-------------------------------------------------------------------------
# Writes a sparse memory image object to an ELF file. Currently we write
# the ELF file in the following order:
#
#  - ElfHeader
#  - ElfSectionHeader for "null" section
#  - ElfSectionHeader for all "normal" sections
#  - ElfSectionHeader for ".shstrtab" section
#  - data for all "normal" sections
#  - data for ".shstrtab" section
#

def elf_writer( mem_image, file_obj ):

  # Get the sections

  sections = mem_image.get_sections()

  ehdr = ElfHeader()

  # Many of these fields are just copied from what binutils generates.
  # Note that we have two extra sections beyond the normal sections. The
  # first "null" section and the final ".shstrtab" section.

  ehdr.ident     = "\x7fELF\x01\x01\x01".ljust( ElfHeader.IDENT_NBYTES, '0' )
  ehdr.type      = ElfHeader.TYPE_EXEC
  ehdr.machine   = 8
  ehdr.version   = 1
  ehdr.entry     = 0x00001000
  ehdr.phoff     = 0
  ehdr.shoff     = ElfHeader.NBYTES         # shdrs right after ehdr
  ehdr.flags     = 0x70b03000
  ehdr.ehsize    = 0
  ehdr.phentsize = 0
  ehdr.phnum     = 0
  ehdr.shentsize = ElfSectionHeader.NBYTES  # shdrs are fixed size
  ehdr.shnum     = len(sections) + 2        # add 2 for extra sections
  ehdr.shstrndx  = len(sections) + 1        # location of shstrtab

  # Write the ELF header to the file

  file_obj.write( ehdr.to_bytes() )

  # Write the first "null" section header to the file

  shdr = ElfSectionHeader()
  shdr.name      = 0
  shdr.type      = 0
  shdr.flags     = 0
  shdr.addr      = 0
  shdr.offset    = 0
  shdr.size      = 0
  shdr.link      = 0
  shdr.info      = 0
  shdr.addralign = 0
  shdr.entsize   = 0
  file_obj.write( shdr.to_bytes() )

  # The section data is going to start after the ELF header and all of
  # the section headers.

  section_offset =  ElfHeader.NBYTES                        # ELF header
  section_offset += ElfSectionHeader.NBYTES                 # null shdr
  section_offset += len(sections) * ElfSectionHeader.NBYTES # normal shdrs
  section_offset += 1 * ElfSectionHeader.NBYTES             # shstrtab shdr

  # Collect section names in a string for writing to ".shstrtab"

  section_names = "\0"

  # Write the "normal" section headers to the file

  for section in sections:

    shdr = ElfSectionHeader()
    shdr.name      = len(section_names)
    shdr.type      = ElfSectionHeader.TYPE_PROGBITS
    shdr.flags     = ElfSectionHeader.FLAGS_ALLOC
    shdr.addr      = section.addr
    shdr.offset    = section_offset
    shdr.size      = len(section.data)
    shdr.link      = 0
    shdr.info      = 0
    shdr.addralign = 0
    shdr.entsize   = 0

    file_obj.write( shdr.to_bytes() )

    section_names  += section.name + "\0"
    section_offset += len(section.data)

  # Write the ".shstrtab" section header to the file

  shdr = ElfSectionHeader()
  shdr.name      = len(section_names)
  shdr.type      = ElfSectionHeader.TYPE_STRTAB
  shdr.flags     = 0
  shdr.addr      = 0
  shdr.offset    = section_offset
  shdr.size      = len( section_names + ".shstrtab\0" )
  shdr.link      = 0
  shdr.info      = 0
  shdr.addralign = 0
  shdr.entsize   = 0

  file_obj.write( shdr.to_bytes() )

  section_names  += ".shstrtab\0"
  section_offset += len(section_names)

  # Write the section data for "normal" sections

  for section in sections:
    file_obj.write( section.data )

  # Write the data for the ".shstrtab" section

  file_obj.write( section_names.encode() )

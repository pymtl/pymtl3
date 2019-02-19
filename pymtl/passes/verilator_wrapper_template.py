#=========================================================================
# V{top_module}_v.py
#=========================================================================
# This wrapper makes a Verilator-generated C++ model appear as if it
# were a normal PyMTL model. This template is based on PyMTL v2.

import os

from pymtl import *
from cffi  import FFI

#-------------------------------------------------------------------------
# {top_module}
#-------------------------------------------------------------------------
class {top_module}( RTLComponent ):
  id_ = 0

  def __init__( s ):

    # initialize FFI, define the exposed interface
    s.ffi = FFI()
    s.ffi.cdef('''
      typedef struct {{

        // Exposed port interface
        {port_externs}

        // Verilator model
        void * model;

      }} V{top_module}_t;

      V{top_module}_t * create_model();
      void destroy_model( V{top_module}_t *);
      void eval( V{top_module}_t * );

    ''')

    # Import the shared library containing the model. We defer
    # construction to the elaborate_logic function to allow the user to
    # set the vcd_file.

    s._ffi_inst = s.ffi.dlopen('./{lib_file}')

    # dummy class to emulate PortBundles
    # class BundleProxy( PortBundle ):
      # flip = False

    # increment instance count
    {top_module}.id_ += 1

  def __del__( s ):
    # s._ffi_inst.destroy_model( s._ffi_m )
    s.ffi.dlclose( s._ffi_inst )
    # Deref the cffi objects so that GC can work. We need this because 
    # the linked shared library seems to be cached somewhere. Simply call 
    # dlclose() does not work. 
    s.ffi = None
    s._ffi_inst = None

  def construct( s ):

    # Construct the model.

    s._ffi_m = s._ffi_inst.create_model()

    # define the port interface
    {port_defs}

{comb_upblks}

    # The support for sequential logics will be added later.
    # @s.update_on_edge
    # def tick():

      # s._ffi_m.clk[0] = 0
      # s._ffi_inst.eval( s._ffi_m )
      # s._ffi_m.clk[0] = 1
      # s._ffi_inst.eval( s._ffi_m )

      # # double buffer register outputs
      # # FIXME: currently treat all outputs as combinational outs
    {seq_upblk}

  def line_trace( s ):
    return {line_trace}

  def internal_line_trace( s ):
    return {in_line_trace}

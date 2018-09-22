#=======================================================================
# V{top_module}_v.py
#=======================================================================
# This wrapper makes a Verilator-generated C++ model appear as if it
# were a normal PyMTL model.

import os

from pymtl import *
from cffi  import FFI

#-----------------------------------------------------------------------
# {top_module}
#-----------------------------------------------------------------------
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

    s._ffi = s.ffi.dlopen('./{lib_file}')

    # dummy class to emulate PortBundles
    # class BundleProxy( PortBundle ):
      # flip = False

    # define the port interface
    {port_defs}

    # increment instance count
    {top_module}.id_ += 1

  def __del__( s ):
    s._ffi.destroy_model( s._m )

  def construct( s ):

    # Construct the model.

    s._m = s._ffi.create_model()

    @s.update
    def logic():

      # set inputs
      {set_inputs}

      # execute combinational logic
      s._ffi.eval( s._m )

      # set outputs
      # FIXME: currently write all outputs, not just combinational outs
      {set_comb}

    @s.update_on_edge
    def tick():

      s._m.clk[0] = 0
      s._ffi.eval( s._m )
      s._m.clk[0] = 1
      s._ffi.eval( s._m )

      # double buffer register outputs
      # FIXME: currently write all outputs, not just registered outs
      {set_next}


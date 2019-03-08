#=========================================================================
# PyMTLWrapperGen.py
#=========================================================================
# This file include the function that generates a PyMTL wrapper for an
# imported model. The wrapper template and most of the code ehre  are 
# based on PyMTL v2.
# 
# Author : Peitian Pan
# Date   : Feb 22, 2019

import os

from pymtl.passes.utility.pass_utility import make_indent

from helpers                           import *

#-----------------------------------------------------------------------
# generate_py_wrapper
#-----------------------------------------------------------------------
# The function that generates PyMTL wrapper.

def generate_py_wrapper( interface, ports, top_name, lib_file, port_cdefs, ssg_name ):
    
    template_name =\
      os.path.dirname( os.path.abspath( __file__ ) ) +\
      os.path.sep + 'verilator_wrapper.template.py'

    wrapper_name = top_name + '_v.py'

    # Port definitions for verilated model
    make_indent( port_cdefs, 4 )

    # Port definition in PyMTL style
    port_defs = []

    for name, port in interface:
      port_defs.append( generate_signal_decl_py( name, port ) )

    make_indent( port_defs, 2 )

    # Load the sensitivity group from .ssg file
    ssg = load_ssg( ssg_name )

    if ssg is None: ssg = generate_default_ssg( ports )

    constraints = []

    # Sequential upblks
    seq_upblk, _constraints = generate_seq_upblk_py( ports, ssg )

    constraints += _constraints

    # Combinational upblks
    comb_upblks, _constraints = generate_comb_upblks_py( ports, ssg )

    constraints += _constraints

    # Read-out combinational upblks

    readout_upblks, _constraints = generate_readout_upblks_py( ports, ssg )

    constraints += _constraints

    # Constraints
    
    make_indent( constraints, 3 )

    constraint_str = '' if constraints is [] else \
      's.add_constraints(\n{}\n    )'.format(
        '\n'.join( constraints )
      )

    # Line trace 
    line_trace = generate_line_trace_py( ports )

    # Internal line trace 
    in_line_trace = generate_internal_line_trace_py( ports )

    # Fill in the python wrapper template
    with open( template_name, 'r' ) as template:
      with open( wrapper_name, 'w' ) as output:

        py_wrapper = template.read()
        py_wrapper = py_wrapper.format(
          top_name       = top_name,
          lib_file       = lib_file,
          port_externs   = '\n'.join( port_cdefs ),
          port_defs      = '\n'.join( port_defs ),
          seq_upblk      = seq_upblk,
          comb_upblks    = '\n'.join( comb_upblks ),
          readout_upblks = '\n'.join( readout_upblks ),
          constraints    = constraint_str,
          line_trace     = line_trace,
          in_line_trace  = in_line_trace,
        )
        output.write( py_wrapper )

    return wrapper_name

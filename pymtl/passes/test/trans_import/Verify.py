#========================================================================
# Verify.py
#========================================================================
# Verify the correctness of the translation pass and the import pass.
# 
# Author : Peitian Pan
# Date   : Oct 18, 2018

import os
import sys
import pytest

from pymtl import *
from pymtl.passes.SimRTLPass import SimRTLPass
from pymtl.passes.SystemVerilogTranslationPass import\
  SystemVerilogTranslationPass as TranslationPass
from pymtl.passes.SimpleImportPass import SimpleImportPass as ImportPass
from pymtl.passes.SimpleImportPass import get_array_name, get_array_idx

# Print info according to the verbosity setting of pytest
# if pytest is run with -v, s will be printed
def v_print( s, verbosity ):
  if verbosity > 0:
    print s

def verification_init( model_name, verbosity, *args, **kwargs ):
  """ translate model_name and import it back to get ready for
  the verification"""

  # We work under a new directory in the current working directory
  # to keep the pwd tidy.

  working_dir = \
    os.path.dirname(os.path.realpath(__file__)) + os.path.sep + model_name

  os.chdir( working_dir )

  if not working_dir in sys.path:
    sys.path.append( working_dir )

  v_print( 'Entered ' + working_dir, verbosity )

  v_print( '\tReading PyMTL source file...', verbosity )

  py_source_file = model_name

  if model_name in sys.modules:
    # We are in a test that is repeatedly running
    # The user might have updated the source file so we need to reload it
    exec( "reload( sys.modules[ '{model_name}' ] )".\
      format( model_name = model_name ) )
    exec( "PyMTLModel = sys.modules[ '{model_name}'].{model_name}".\
      format( model_name = model_name ) 
    )
  else:
    # First time execution
    import_cmd = 'from {py_source_file} import {model_name} as PyMTLModel'.\
      format( **locals() )

    exec( import_cmd )

  m = PyMTLModel( *args, **kwargs )

  v_print( '\tElaborating PyMTL model...', verbosity )

  m.elaborate()

  v_print( '\tCalling translation pass...', verbosity )

  TranslationPass()( m )

  v_print( '\tCalling import pass...', verbosity )

  ImportPass()( m )

  v_print( '\tElaborating imported model...', verbosity ) 

  m.imported_model.elaborate()

  return m

def verification_test_vector( \
    ref_model, imported_model, test_vectors, verbosity 
  ):
  """ verify the functionality of the imported model against the reference
  model with input specified by test_vectors"""

  v_print( '\tTesting models with test vectors...', verbosity )

  models = [ ref_model, imported_model ]

  # First line is port names

  if isinstance( test_vectors[0], str ):
    port_names = test_vectors[0].split()
  else:
    port_names = test_vectors[0]

  # Input values from the second element on

  test_vectors = test_vectors[1:]

  # We need the names of ports because later the ports will be overwritten
  # with numerical simulation values

  ref_in_port  = ref_model.get_input_value_ports()
  ref_out_port = ref_model.get_output_value_ports()
  imported_out_port = imported_model.get_output_value_ports()

  v_print( 'Running SimRTLPass()...', verbosity )

  SimRTLPass()( ref_model )

  # ref_model.unlock_simulation()

  SimRTLPass()( imported_model )

  # imported_model.unlock_simulation()

  # Start the simulation

  row_num = 0

  for row in test_vectors:

    row_num += 1

    print( 'Row number:{}, vector:{}\n'.format( row_num,  row ) )

    # Apply test inputs to the reference model

    for port_name, in_value in zip( port_names, row ):
      # Processing input ports
      exec( 'ref_model.{port_name} = in_value'.\
        format( port_name = port_name ) 
      )

    ref_model.tick()

    v_print( '\nReference model line traces:', verbosity )
    v_print( ref_model.line_trace(), verbosity )

    # Apply test inputs to the imported model

    for port_name, in_value in zip( port_names, row ):
      # Processing input ports 
      exec( 'imported_model.{port_name} = in_value'.\
        format( port_name = port_name ) 
      )

    imported_model.tick()

    v_print( '\nImported model line traces:', verbosity )
    v_print( imported_model.line_trace(), verbosity )

    # Generate reference output

    ref_output = {}

    v_print( 'Collecting reference model outputs...', verbosity )

    for port in ref_out_port:
      name = port._my_name

      if '[' in name:
        # Get array name and use that name to generate
        # mapping between port names and values
        name = get_array_name( name )

      output_value = ref_model.__dict__[ name ]
      
      ref_output[ name ] = output_value

    # Read output from the imported model

    v_print( 'Comparing outputs of models...', verbosity )

    for port in imported_out_port:
      name = port._my_name

      if '[' in name:
        # Get array name and use that name to generate
        # mapping between port names and values
        name = get_array_name( name )

      ref_value = ref_output[ name ]

      output_value = imported_model.__dict__[ name ]

      if ( not '[' in port._my_name ) or ( get_array_idx( port._my_name ) == 0 ):
        print( '\nModel ouptut comparison:' )
        print( "ref = {}\nout = {}".\
          format(\
            map( lambda x: x.uint(), ref_value ), 
            output_value 
          ) 
        )

      # Compare two values
      assert ref_value == output_value, """
  verification_test_vector() received an incorrect value!
  - row number      : {row_number}
  - port name       : {port_name}
  - expected value  : {expected_value}
  - actual value    : {actual_value}
        """.format(
          row_number      = row_num, 
          port_name       = port._my_name, 
          expected_value  = ref_value, 
          actual_value    = output_value, 
          )

  v_print( 'verification_test_vector() exits successfully!', verbosity )

def Verify( model_name, test_vector, verbosity, *args, **kwargs ):
  """ Verify the correctness of the translation and import pass by
  comparing the output of the reference model and the imported model.
  Work under passes/trans_import/<model_name> where all temp files are stored """

  v_print( 'Verify() working on {} with {}...\n'.\
    format( model_name, test_vector ), verbosity
  )

  try:
    model = verification_init( model_name, verbosity, *args, **kwargs )

    verification_test_vector( 
      model, model.imported_model, test_vector, verbosity 
    )
  except Exception as e:
    print( 'Exception caught! {0} with the following message\n{1}'.\
      format( type(e).__name__, e.args[0]) 
    )
    raise AssertionError
  finally:
    # We need to manually destroy the imported shared library because
    # the imported library seems to be cached somewhere.

    v_print( 'Destroying the linked share lib...', verbosity )

    model.imported_model.ffi.dlclose( model.imported_model._ffi_inst )
    model.imported_model.ffi = None
    model.imported_model = None
    model = None

    v_print( '==========================================', verbosity )
    print(\
      """Test passed: no discrepancy found between output of imported """
      """and reference models!""" 
    )
    v_print( '==========================================', verbosity )

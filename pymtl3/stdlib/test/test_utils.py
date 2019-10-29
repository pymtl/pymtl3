import collections

from pymtl3 import *

#-------------------------------------------------------------------------
# mk_test_case_table
#-------------------------------------------------------------------------

def mk_test_case_table( raw_test_case_table ):

  # First row in test vectors contains port names

  if isinstance(raw_test_case_table[0],str):
    test_param_names = raw_test_case_table[0].split()
  else:
    test_param_names = raw_test_case_table[0]

  TestCase = collections.namedtuple("TestCase",test_param_names)

  ids = []
  test_cases = []
  for row in raw_test_case_table[1:]:
    ids.append( row[0] )
    test_cases.append( TestCase(*row[1:]) )

  return {
    'ids'      : ids,
    'argnames' : ('test_params'),
    'argvalues' : test_cases,
  }

#------------------------------------------------------------------------------
# TestVectorSimulator
#------------------------------------------------------------------------------

class TestVectorSimulator:

  def __init__( self, model, test_vectors,
                set_inputs_func, verify_outputs_func, wait_cycles = 0 ):

    self.model               = model
    self.set_inputs_func     = set_inputs_func
    self.verify_outputs_func = verify_outputs_func
    self.test_vectors        = test_vectors
    self.wait_cycles         = wait_cycles

  def run_test( self ):

    self.model.apply( SimpleSim )

    self.model.sim_reset()

    print()
    for test_vector in self.test_vectors:

      # Set inputs
      self.set_inputs_func( self.model, test_vector )
      self.model.tick()

      # Print the line trace
      print(self.model.line_trace())

      # Verify outputs
      self.verify_outputs_func( self.model, test_vector )

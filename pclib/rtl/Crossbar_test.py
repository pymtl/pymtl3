#=======================================================================
# Crossbar_test.py
#=======================================================================

from pymtl      import *
from Crossbar   import Crossbar

class TestVectorSimulator( object ):

  def __init__( self, model, test_vectors,
                set_inputs_func, verify_outputs_func, wait_cycles = 0 ):

    self.model               = model
    self.set_inputs_func     = set_inputs_func
    self.verify_outputs_func = verify_outputs_func
    self.test_vectors        = test_vectors
    self.wait_cycles         = wait_cycles

  def run_test( self ):

    self.model.apply( SimpleSim )

    print()
    for test_vector in self.test_vectors:

      # Set inputs
      self.set_inputs_func( self.model, test_vector )
      self.model.tick()

      # Print the line trace
      print self.model.line_trace()

      # Verify outputs
      self.verify_outputs_func( self.model, test_vector )

#-----------------------------------------------------------------------
# run_test_crossbar
#-----------------------------------------------------------------------
def run_test_crossbar( model, test_vectors ):

  # Instantiate and elaborate the model

  model.elaborate()

  # Define functions mapping the test vector to ports in model

  num_inputs = len( model.in_ )

  def tv_in( model, test_vector ):
    n = num_inputs
    for i in range(num_inputs):
      model.in_[i] = test_vector[i]
      model.sel[i] = test_vector[n+i]

  def tv_out( model, test_vector ):
    n = 2*num_inputs
    for i in range(num_inputs):
      assert model.out[i] == test_vector[n+i]

  # Run the test

  sim = TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  sim.run_test()

#-----------------------------------------------------------------------
# test_crossbar3
#-----------------------------------------------------------------------
def test_crossbar3( dump_vcd, test_verilog ):
  model = Crossbar( 3, Bits16 )
  model.vcd_file = dump_vcd
  if test_verilog:
    model = TranslationTool( model )
  run_test_crossbar( model, [
    [ 0xdead, 0xbeef, 0xcafe, 0, 1, 2, 0xdead, 0xbeef, 0xcafe ],
    [ 0xdead, 0xbeef, 0xcafe, 0, 2, 1, 0xdead, 0xcafe, 0xbeef ],
    [ 0xdead, 0xbeef, 0xcafe, 1, 2, 0, 0xbeef, 0xcafe, 0xdead ],
    [ 0xdead, 0xbeef, 0xcafe, 1, 0, 2, 0xbeef, 0xdead, 0xcafe ],
    [ 0xdead, 0xbeef, 0xcafe, 2, 1, 0, 0xcafe, 0xbeef, 0xdead ],
    [ 0xdead, 0xbeef, 0xcafe, 2, 0, 1, 0xcafe, 0xdead, 0xbeef ],
  ])

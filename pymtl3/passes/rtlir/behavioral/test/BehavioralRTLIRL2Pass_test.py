#=========================================================================
# BehavioralRTLIRL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 2 behavioral RTLIR passes.

The L2 generation, L2 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

from pymtl3.dsl.errors import UpdateBlockWriteError
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL2Pass import (
    BehavioralRTLIRGenL2Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL2Pass import (
    BehavioralRTLIRTypeCheckL2Pass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    CaseAddComponentComp,
    CaseAddStructBits1Comp,
    CaseAndStructComp,
    CaseComponentEndRangeComp,
    CaseComponentIfCondComp,
    CaseComponentIfExpBodyComp,
    CaseComponentIfExpCondComp,
    CaseComponentIfExpElseComp,
    CaseComponentStartRangeComp,
    CaseComponentStepRangeComp,
    CaseDifferentTypesIfExpComp,
    CaseExplicitBoolComp,
    CaseForLoopElseComp,
    CaseFuncCallAfterInComp,
    CaseInvalidBreakComp,
    CaseInvalidContinueComp,
    CaseInvalidDivComp,
    CaseInvalidInComp,
    CaseInvalidIsComp,
    CaseInvalidIsNotComp,
    CaseInvalidNotInComp,
    CaseInvComponentComp,
    CaseLambdaConnectComp,
    CaseLambdaConnectWithListComp,
    CaseMultiOpComparisonComp,
    CaseNoArgsToRangeComp,
    CaseNotStructComp,
    CaseRedefLoopIndexComp,
    CaseSignalAfterInComp,
    CaseSignalAsLoopIndexComp,
    CaseStructIfCondComp,
    CaseStructIfExpCondComp,
    CaseTmpVarUsedBeforeAssignmentComp,
    CaseTooManyArgsToRangeComp,
    CaseVariableStepRangeComp,
    CaseZeroStepRangeComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  if isinstance(m, type):
    m = m.DUT()
  m.elaborate()
  m.apply( BehavioralRTLIRGenL2Pass( m ) )
  m.apply( BehavioralRTLIRTypeCheckL2Pass( m ) )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m.get_metadata( BehavioralRTLIRGenL2Pass.rtlir_upblks )[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L2_lambda_connect( do_test ):
  a = CaseLambdaConnectComp.DUT()
  a._rtlir_test_ref = { '_lambda__s_out' : CombUpblk( '_lambda__s_out', [
    Assign( [Attribute( Base( a ), 'out' )],
            BinOp(Attribute(Base(a), 'in_'), Add(), Number(42)), True
        ) ] ) }
  do_test( a )

def test_L2_lambda_connect_with_list( do_test ):
  a = CaseLambdaConnectWithListComp.DUT()
  a._rtlir_test_ref = { '_lambda__s_out_1_' : CombUpblk( '_lambda__s_out_1_', [
    Assign( [Index( Attribute( Base( a ), 'out' ), Number(1) )],
            BinOp(Attribute(Base(a), 'in_'), Add(), Number(42)), True
        ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L2_add_component( do_test ):
  with expected_failure( PyMTLTypeError, "rhs of binop should be signal/const" ):
    do_test( CaseAddComponentComp )

def test_L2_inv_component( do_test ):
  with expected_failure( PyMTLTypeError, "only applies to signals and consts" ):
    do_test( CaseInvComponentComp )

def test_L2_for_start_component( do_test ):
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( CaseComponentStartRangeComp )

def test_L2_for_end_component( do_test ):
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( CaseComponentEndRangeComp )

def test_L2_for_step_component( do_test ):
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( CaseComponentStepRangeComp )

def test_L2_if_cond_component( do_test ):
  with expected_failure( PyMTLTypeError, "condition of if must be a signal" ):
    do_test( CaseComponentIfCondComp )

def test_L2_ifexp_cond_component( do_test ):
  with expected_failure( PyMTLTypeError, "condition of if-exp must be a signal" ):
    do_test( CaseComponentIfExpCondComp )

def test_L2_ifexp_body_component( do_test ):
  with expected_failure( PyMTLTypeError, "body of if-exp must be a signal" ):
    do_test( CaseComponentIfExpBodyComp )

def test_L2_ifexp_orelse_component( do_test ):
  with expected_failure( PyMTLTypeError, "else branch of if-exp must be a signal" ):
    do_test( CaseComponentIfExpElseComp )

def test_L2_if_cond_bool( do_test ):
  with expected_failure( PyMTLTypeError, "cannot be converted to bool" ):
    do_test( CaseStructIfCondComp )

def test_L2_for_step_zero( do_test ):
  with expected_failure( PyMTLTypeError, "step of for-loop cannot be zero" ):
    do_test( CaseZeroStepRangeComp )

def test_L2_for_step_variable( do_test ):
  with expected_failure( PyMTLTypeError, "step of a for-loop must be a constant" ):
    do_test( CaseVariableStepRangeComp )

def test_L2_ifexp_cond_bool( do_test ):
  with expected_failure( PyMTLTypeError, "cannot be converted to bool" ):
    do_test( CaseStructIfExpCondComp )

def test_L2_ifexp_body_else_diff_type( do_test ):
  with expected_failure( PyMTLTypeError, "must have the same type" ):
    do_test( CaseDifferentTypesIfExpComp )

def test_L2_unary_not_cast_to_bool( do_test ):
  with expected_failure( PyMTLTypeError, "Vector1 vs Struct Bits32Foo" ):
    do_test( CaseNotStructComp )

def test_L2_bool_cast_to_bool( do_test ):
  with expected_failure( PyMTLTypeError, "should be of vector type" ):
    do_test( CaseAndStructComp )

def test_L2_binop_non_vector( do_test ):
  with expected_failure( PyMTLTypeError, "should be of vector type" ):
    do_test( CaseAddStructBits1Comp )

#-------------------------------------------------------------------------
# PyMTL syntax errors
#-------------------------------------------------------------------------

def test_L2_call_bool( do_test ):
  with expected_failure( PyMTLSyntaxError, "function is not found" ):
    do_test( CaseExplicitBoolComp )

def test_L2_tmp_var_used_before_assignement( do_test ):
  with expected_failure( PyMTLSyntaxError, "tmpvar u used before assignment" ):
    do_test( CaseTmpVarUsedBeforeAssignmentComp )

def test_L2_for_else( do_test ):
  with expected_failure( PyMTLSyntaxError, "for loops cannot have 'else' branch" ):
    do_test( CaseForLoopElseComp )

def test_L2_for_index_signal( do_test ):
  with expected_failure( UpdateBlockWriteError, "@=" ):
    do_test( CaseSignalAsLoopIndexComp )

def test_L2_for_index_redefined( do_test ):
  with expected_failure( PyMTLSyntaxError, "Redefinition of loop index i" ):
    do_test( CaseRedefLoopIndexComp )

def test_L2_for_iter_name( do_test ):
  with expected_failure( PyMTLSyntaxError, "only use range() after 'in'" ):
    do_test( CaseSignalAfterInComp )

def test_L2_for_iter_call_non_range( do_test ):
  with expected_failure( PyMTLSyntaxError, "only use range() after 'in'" ):
    do_test( CaseFuncCallAfterInComp )

def test_L2_for_iter_range_arg_0( do_test ):
  with expected_failure( PyMTLSyntaxError, "1~3 arguments should be given to range" ):
    do_test( CaseNoArgsToRangeComp )

def test_L2_for_iter_range_arg_4( do_test ):
  with expected_failure( PyMTLSyntaxError, "1~3 arguments should be given to range" ):
    do_test( CaseTooManyArgsToRangeComp )

def test_L2_invalid_op_is( do_test ):
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( CaseInvalidIsComp )

def test_L2_invalid_op_is_not( do_test ):
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( CaseInvalidIsNotComp )

def test_L2_invalid_op_in( do_test ):
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( CaseInvalidInComp )

def test_L2_invalid_op_not_in( do_test ):
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( CaseInvalidNotInComp )

def test_L2_invalid_op_floor_div( do_test ):
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( CaseInvalidDivComp )

def test_L2_compare_terms( do_test ):
  with expected_failure( PyMTLSyntaxError, "Comparison can only have 2 operands" ):
    do_test( CaseMultiOpComparisonComp )

#-------------------------------------------------------------------------
# PyMTL syntax errors for unsupported Python syntax
#-------------------------------------------------------------------------

def test_Break( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: break" ):
    do_test( CaseInvalidBreakComp )

def test_Continue( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: continue" ):
    do_test( CaseInvalidContinueComp )

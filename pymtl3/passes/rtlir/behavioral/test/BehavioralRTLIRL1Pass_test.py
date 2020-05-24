#=========================================================================
# BehavioralRTLIRL1Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 1 behavioral RTLIR passes.

The L1 generation, L1 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

import sys

import pytest

from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL1Pass import (
    BehavioralRTLIRGenL1Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL1Pass import (
    BehavioralRTLIRTypeCheckL1Pass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    CaseAssignMultiTargetComp,
    CaseAttributeSignalComp,
    CaseBits64TruncInComp,
    CaseBitsArgsComp,
    CaseBitSelOutOfRangeComp,
    CaseClassdefComp,
    CaseComponentBaseIndexComp,
    CaseComponentHigherSliceComp,
    CaseComponentInIndexComp,
    CaseComponentLowerSliceComp,
    CaseConcatComponentComp,
    CaseConcatNoArgsComp,
    CaseCopyArgsComp,
    CaseDeepcopyArgsComp,
    CaseDeleteComp,
    CaseDictComp,
    CaseDictComprehensionComp,
    CaseDoubleStarArgsComp,
    CaseDroppedAttributeComp,
    CaseExecComp,
    CaseExtendedSubscriptComp,
    CaseExtSliceComp,
    CaseFuncNotFoundComp,
    CaseGeneratorExprComp,
    CaseGlobalComp,
    CaseImportComp,
    CaseImportFromComp,
    CaseIndexOnStructComp,
    CaseIndexOutOfRangeComp,
    CaseKwArgsComp,
    CaseL1UnsupportedSubCompAttrComp,
    CaseLambdaFuncComp,
    CaseLHSComponentComp,
    CaseLHSConstComp,
    CaseListComp,
    CaseListComprehensionComp,
    CaseNonNameCalledComp,
    CasePassComp,
    CaseRaiseComp,
    CaseReprComp,
    CaseRHSComponentComp,
    CaseSetComp,
    CaseSetComprehensionComp,
    CaseSextOnComponentComp,
    CaseSextSmallNbitsComp,
    CaseSextTwoArgsComp,
    CaseSextVaribleNbitsComp,
    CaseSizeCastComponentComp,
    CaseSliceBoundLowerComp,
    CaseSliceOnComponentComp,
    CaseSliceOnStructComp,
    CaseSliceOutOfRangeComp,
    CaseSliceVariableBoundComp,
    CaseSliceWithStepsComp,
    CaseStandaloneExprComp,
    CaseStarArgsComp,
    CaseStrComp,
    CaseStructBitsUnagreeableComp,
    CaseTmpComponentComp,
    CaseTruncLargeNbitsComp,
    CaseTruncVaribleNbitsComp,
    CaseTryExceptComp,
    CaseTryFinallyComp,
    CaseTupleComp,
    CaseUnrecognizedFuncComp,
    CaseUntypedTmpComp,
    CaseUpblkArgComp,
    CaseWhileComp,
    CaseWithComp,
    CaseYieldComp,
    CaseZextOnComponentComp,
    CaseZextSmallNbitsComp,
    CaseZextTwoArgsComp,
    CaseZextVaribleNbitsComp,
)

# TODO: fix all tests with this mark, including in other files (grep!).
# (we use the mark instead of allowing failure more generally because this
#  prevents regressions in all the other tests that *pass* on Python 3)
# If a test passes despite the mark, just remove it from that test!
if sys.version_info[0] == 3:
  XFAIL_ON_PY3 = pytest.mark.xfail(strict=True)
else:
  XFAIL_ON_PY3 = lambda f: f


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m = m.DUT()
  m.elaborate()
  m.apply( BehavioralRTLIRGenL1Pass( m ) )
  m.apply( BehavioralRTLIRTypeCheckL1Pass( m ) )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m.get_metadata( BehavioralRTLIRGenL1Pass.rtlir_upblks )[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

def test_L1_call_name( do_test ):
  do_test( CaseNonNameCalledComp )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L1_assign_unagreeable( do_test ):
  with expected_failure( PyMTLTypeError, "Unagreeable types" ):
    do_test( CaseStructBitsUnagreeableComp )

def test_L1_concat_component( do_test ):
  with expected_failure( PyMTLTypeError, "not a signal" ):
    do_test( CaseConcatComponentComp )

def test_L1_zext_variable_nbits( do_test ):
  with expected_failure( PyMTLSyntaxError, "not a constant int or BitsN type" ):
    do_test( CaseZextVaribleNbitsComp )

def test_L1_zext_small_nbits( do_test ):
  with expected_failure( PyMTLTypeError, "less than the bitwidth of the operand" ):
    do_test( CaseZextSmallNbitsComp )

def test_L1_sext_variable_nbits( do_test ):
  with expected_failure( PyMTLSyntaxError, "not a constant int or BitsN type" ):
    do_test( CaseSextVaribleNbitsComp )

def test_L1_sext_small_nbits( do_test ):
  with expected_failure( PyMTLTypeError, "less than the bitwidth of the operand" ):
    do_test( CaseSextSmallNbitsComp )

def test_L1_trunc_variable_nbits( do_test ):
  with expected_failure( PyMTLSyntaxError, "not a constant int or BitsN type" ):
    do_test( CaseTruncVaribleNbitsComp )

def test_L1_trunc_large_nbits( do_test ):
  with expected_failure( PyMTLTypeError, "larger than the bitwidth of the operand" ):
    do_test( CaseTruncLargeNbitsComp )

def test_L1_wrong_attribute( do_test ):
  with expected_failure( PyMTLTypeError, "does not have attribute in_" ):
    do_test( CaseDroppedAttributeComp )

def test_L1_unsupported_attr( do_test ):
  with expected_failure( PyMTLTypeError, "not supported at L1" ):
    do_test( CaseL1UnsupportedSubCompAttrComp )

def test_L1_array_index_out_of_range( do_test ):
  with expected_failure( PyMTLTypeError, "array index out of range" ):
    do_test( CaseIndexOutOfRangeComp )

@pytest.mark.xfail( reason = "PyMTL DSL already threw InvalidIndexError" )
def test_L1_bit_sel_index_out_of_range( do_test ):
  with expected_failure( PyMTLTypeError, "bit selection index out of range" ):
    do_test( CaseBitSelOutOfRangeComp )

@pytest.mark.xfail( reason = "PyMTL DSL already threw InvalidIndexError" )
def test_L1_index_on_struct( do_test ):
  with expected_failure( PyMTLTypeError, "cannot perform index on Struct" ):
    do_test( CaseIndexOnStructComp )

@pytest.mark.xfail( reason = "PyMTL DSL already threw InvalidIndexError" )
def test_L1_slice_on_struct( do_test ):
  with expected_failure( PyMTLTypeError, "cannot perform slicing on type Struct" ):
    do_test( CaseSliceOnStructComp )

@pytest.mark.xfail( reason = "PyMTL DSL already threw InvalidIndexError" )
def test_L1_slice_l_ngt_r( do_test ):
  with expected_failure( PyMTLTypeError, "must be larger than the lower bound" ):
    do_test( CaseSliceBoundLowerComp )

def test_L1_slice_variable_bound( do_test ):
  with expected_failure( PyMTLTypeError, "slice bounds must be constant" ):
    do_test( CaseSliceVariableBoundComp )

@pytest.mark.xfail( reason = "PyMTL DSL already threw InvalidIndexError" )
def test_L1_slice_out_of_range( do_test ):
  with expected_failure( PyMTLTypeError, "slice out of width of signal" ):
    do_test( CaseSliceOutOfRangeComp )

#-------------------------------------------------------------------------
# PyMTL type errors: unexpected types
#-------------------------------------------------------------------------

def test_L1_assign_lhs_const( do_test ):
  with expected_failure( PyMTLTypeError, "must be a signal" ):
    do_test( CaseLHSConstComp )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_assign_lhs_component( do_test ):
  with expected_failure( PyMTLTypeError, "must be a signal" ):
    do_test( CaseLHSComponentComp )

def test_L1_assign_rhs_component( do_test ):
  with expected_failure( PyMTLTypeError, "signal or const" ):
    do_test( CaseRHSComponentComp )

def test_L1_zext_component( do_test ):
  with expected_failure( PyMTLTypeError, "only applies to signals" ):
    do_test( CaseZextOnComponentComp )

def test_L1_sext_component( do_test ):
  with expected_failure( PyMTLTypeError, "only applies to signals" ):
    do_test( CaseSextOnComponentComp )

def test_L1_size_cast_component( do_test ):
  with expected_failure( PyMTLTypeError, "size casting only applies to signals/consts" ):
    do_test( CaseSizeCastComponentComp )

def test_L1_attr_signal( do_test ):
  with expected_failure( PyMTLTypeError, "base of an attribute must be a component" ):
    do_test( CaseAttributeSignalComp )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_index_component( do_test ):
  with expected_failure( PyMTLTypeError, "signal or constant expression" ):
    do_test( CaseComponentInIndexComp )

def test_L1_index_base_component( do_test ):
  with expected_failure( PyMTLTypeError, "base of an index must be an array or signal" ):
    do_test( CaseComponentBaseIndexComp )

def test_L1_slice_lower_component( do_test ):
  with expected_failure( PyMTLTypeError, "constant expression" ):
    do_test( CaseComponentLowerSliceComp )

def test_L1_slice_upper_component( do_test ):
  with expected_failure( PyMTLTypeError, "constant expression" ):
    do_test( CaseComponentHigherSliceComp )

def test_L1_slice_component( do_test ):
  with expected_failure( PyMTLTypeError, "base of a slice must be a signal" ):
    do_test( CaseSliceOnComponentComp )

#-------------------------------------------------------------------------
# PyMTL syntax errors
#-------------------------------------------------------------------------

def test_L1_upblk_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "not have arguments" ):
    do_test( CaseUpblkArgComp )

def test_L1_multi_assign( do_test ):
  # Multiple assignment is now valid
  with expected_failure( PyMTLSyntaxError, "not supported at L1!" ):
    do_test( CaseAssignMultiTargetComp )

def test_L1_copy_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "takes exactly 1 argument" ):
    do_test( CaseCopyArgsComp )

def test_L1_deepcopy_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "takes exactly 1 argument" ):
    do_test( CaseDeepcopyArgsComp )

def test_L1_slice_step( do_test ):
  with expected_failure( PyMTLSyntaxError, "Slice with steps" ):
    do_test( CaseSliceWithStepsComp )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_illegal_subscript( do_test ):
  with expected_failure( PyMTLSyntaxError, "Illegal subscript" ):
    do_test( CaseExtendedSubscriptComp )

def test_L1_closure_freevar( do_test ):
  with expected_failure( PyMTLSyntaxError, "not a sub-component" ):
    do_test( CaseTmpComponentComp )

def test_L1_tmpvar( do_test ):
  with expected_failure( PyMTLSyntaxError, "Temporary variable" ):
    do_test( CaseUntypedTmpComp )

#-------------------------------------------------------------------------
# Call-related syntax errors
#-------------------------------------------------------------------------

@XFAIL_ON_PY3
def test_L1_call_star_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "star argument" ):
    do_test( CaseStarArgsComp )

@XFAIL_ON_PY3
def test_L1_call_double_star_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "double-star argument" ):
    do_test( CaseDoubleStarArgsComp )

def test_L1_call_keyword_arg( do_test ):
  with expected_failure( PyMTLSyntaxError, "keyword argument" ):
    do_test( CaseKwArgsComp )

def test_L1_call_not_found( do_test ):
  with expected_failure( PyMTLSyntaxError, "function is not found" ):
    do_test( CaseFuncNotFoundComp )

def test_L1_call_Bits_args( do_test ):
  with expected_failure( PyMTLSyntaxError, "exactly one or zero argument" ):
    do_test( CaseBitsArgsComp )

def test_L1_call_concat_args( do_test ):
  with expected_failure( PyMTLSyntaxError, "at least one argument" ):
    do_test( CaseConcatNoArgsComp )

def test_L1_call_zext_num_args( do_test ):
  with expected_failure( PyMTLSyntaxError, "exactly two arguments" ):
    do_test( CaseZextTwoArgsComp )

def test_L1_call_sext_num_args( do_test ):
  with expected_failure( PyMTLSyntaxError, "exactly two arguments" ):
    do_test( CaseSextTwoArgsComp )

def test_L1_call_unrecognized( do_test ):
  with expected_failure( PyMTLSyntaxError, "function is not found" ):
    do_test( CaseUnrecognizedFuncComp )

#-------------------------------------------------------------------------
# PyMTL syntax errors for unsupported Python syntax
#-------------------------------------------------------------------------

def test_Expr( do_test ):
  with expected_failure( PyMTLSyntaxError, "Stand-alone expression" ):
    do_test( CaseStandaloneExprComp )

def test_Lambda( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: lambda function" ):
    do_test( CaseLambdaFuncComp )

def test_Dict( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid type: dict" ):
    do_test( CaseDictComp )

def test_Set( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid type: set" ):
    do_test( CaseSetComp )

def test_List( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid type: list" ):
    do_test( CaseListComp )

def test_Tuple( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid type: tuple" ):
    do_test( CaseTupleComp )

def test_ListComp( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: list comprehension" ):
    do_test( CaseListComprehensionComp )

def test_SetComp( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: set comprehension" ):
    do_test( CaseSetComprehensionComp )

def test_DictComp( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: dict comprehension" ):
    do_test( CaseDictComprehensionComp )

def test_GeneratorExp( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: generator expression" ):
    do_test( CaseGeneratorExprComp )

def test_Yield( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: yield" ):
    do_test( CaseYieldComp )

@pytest.mark.xfail( reason = "Syntax not compatible with Python 3" )
def test_Repr( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: repr" ):
    do_test( CaseReprComp )

def test_Str( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: str" ):
    do_test( CaseStrComp )

def test_Classdef( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: classdef" ):
    do_test( CaseClassdefComp )

def test_Delete( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: delete" ):
    do_test( CaseDeleteComp )

def test_With( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: with" ):
    do_test( CaseWithComp )

def test_Raise( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: raise" ):
    do_test( CaseRaiseComp )

@XFAIL_ON_PY3
def test_TryExcept( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: try-except" ):
    do_test( CaseTryExceptComp )

@XFAIL_ON_PY3
def test_TryFinally( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: try-finally" ):
    do_test( CaseTryFinallyComp )

def test_Import( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: import" ):
    do_test( CaseImportComp )

def test_ImportFrom( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: import-from" ):
    do_test( CaseImportFromComp )

@pytest.mark.xfail( reason = "Syntax not compatible with Python 3" )
def test_Exec( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: exec" ):
    do_test( CaseExecComp )

def test_Global( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: global" ):
    do_test( CaseGlobalComp )

def test_Pass( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: pass" ):
    do_test( CasePassComp )

def test_While( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: while" ):
    do_test( CaseWhileComp )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_ExtSlice( do_test ):
  with expected_failure( PyMTLSyntaxError, "invalid operation: extslice" ):
    do_test( CaseExtSliceComp )

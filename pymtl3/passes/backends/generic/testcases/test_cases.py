"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository for the generic backend.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from pymtl3.testcases import add_attributes
from pymtl3.testcases import CaseBits32ClosureConstruct, \
    CaseBits32ArrayClosureConstruct, CaseTwoUpblksSliceComp, \
    CaseTwoUpblksFreevarsComp, CaseBits32TmpWireComp, \
    CaseBits32TmpWireAliasComp, CaseBits32MultiTmpWireComp, \
    CaseBits32FreeVarToTmpVarComp, CaseBits32ConstBitsToTmpVarComp, \
    CaseBits32ConstIntToTmpVarComp, CaseStructTmpWireComp, \
    CaseTwoUpblksStructTmpWireComp, CaseBits32IfcTmpVarOutComp, \
    CaseStructIfcTmpVarOutComp, CaseSubCompTmpDrivenComp, \
    CaseSubCompFreeVarDrivenComp

CaseBits32ClosureConstruct = add_attributes( CaseBits32ClosureConstruct,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: foo
    '''
)

CaseBits32ArrayClosureConstruct = add_attributes( CaseBits32ArrayClosureConstruct,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: foo
    '''
)

CaseTwoUpblksSliceComp = add_attributes( CaseTwoUpblksSliceComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    'freevars:\n'
)

CaseTwoUpblksFreevarsComp = add_attributes( CaseTwoUpblksFreevarsComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: STATE_IDLE
          freevar: STATE_WORK
    '''
)

CaseBits32TmpWireComp = add_attributes( CaseBits32TmpWireComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseBits32TmpWireAliasComp = add_attributes( CaseBits32TmpWireAliasComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in multi_upblks_1 of Vector32
          tmpvar: u in multi_upblks_2 of Vector32
    '''
)

CaseBits32MultiTmpWireComp = add_attributes( CaseBits32MultiTmpWireComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
          tmpvar: v in upblk of Vector32
    '''
)

CaseBits32FreeVarToTmpVarComp = add_attributes( CaseBits32FreeVarToTmpVarComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: STATE_IDLE
    ''',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseBits32ConstBitsToTmpVarComp = add_attributes( CaseBits32ConstBitsToTmpVarComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseBits32ConstIntToTmpVarComp = add_attributes( CaseBits32ConstIntToTmpVarComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseStructTmpWireComp = add_attributes( CaseStructTmpWireComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Struct Bits32Foo
    '''
)

CaseTwoUpblksStructTmpWireComp = add_attributes( CaseTwoUpblksStructTmpWireComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in multi_upblks_1 of Struct Bits32Foo
          tmpvar: u in multi_upblks_2 of Struct Bits32Bar
    '''
)

CaseBits32IfcTmpVarOutComp = add_attributes( CaseBits32IfcTmpVarOutComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseStructIfcTmpVarOutComp = add_attributes( CaseStructIfcTmpVarOutComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Struct Bits32Foo
    '''
)

CaseSubCompTmpDrivenComp = add_attributes( CaseSubCompTmpDrivenComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_TMPVAR',
    '''\
        tmpvars:
          tmpvar: u in upblk of Vector32
    '''
)

CaseSubCompFreeVarDrivenComp = add_attributes( CaseSubCompFreeVarDrivenComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: STATE_IDLE
          freevar: STATE_WORK
    ''',
    'REF_TMPVAR',
    'tmpvars:\n'
)

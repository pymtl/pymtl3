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
    CaseSubCompFreeVarDrivenComp, CaseBits32PortOnly, \
    CaseBits32x5PortOnly, CaseWiresDrivenComp, \
    CaseBits32Wirex5DrivenComp, CaseBits32ClosureConstruct, \
    CaseBits32ArrayClosureConstruct, CaseConnectBitSelToOutComp, \
    CaseConnectSliceToOutComp, CaseConnectPortIndexComp, \
    CaseConnectInToWireComp, CaseConnectConstToOutComp

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

CaseComponentArgsComp = add_attributes( CaseComponentArgsComp,
    'REF_NAME',
    'DUT__foo_0__bar_002a',
    'REF_SRC',
    '''\
        component A__foo_0__bar_002a
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    '''
)

CaseComponentDefaultArgsComp = add_attributes( CaseComponentDefaultArgsComp,
    'REF_NAME',
    'DUT__foo_0__bar_002a',
    'REF_SRC',
    '''\
        component A__foo_0__bar_002a
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    '''
)

CaseMixedDefaultArgsComp = add_attributes( CaseMixedDefaultArgsComp,
    'REF_NAME',
    'DUT__foo_0__bar_002a__woo_00000000',
    'REF_SRC',
    '''\
        component A__foo_0__bar_002a__woo_00000000
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    '''
)

CaseBits32PortOnly = add_attributes( CaseBits32PortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Vector32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    'connections:\n',
    'REF_VECTOR',
    [ (rdt.Vector(1), 'Vector1'), (rdt.Vector(32), 'Vector32') ],
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    '''
)

CaseBits32x5PortOnly = add_attributes( CaseBits32x5PortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: foo Array[5] of Port
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Array[5] of Port
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    '''
)

CaseWiresDrivenComp = add_attributes( CaseWiresDrivenComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    'port_decls:\n',
    'REF_WIRE',
    '''\
        wire_decls:
          wire_decl: bar Wire of Vector4
          wire_decl: foo Wire foo Vector32
    '''
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
          wire_decl: bar Wire of Vector4
          wire_decl: foo Wire foo Vector32
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32Wirex5DrivenComp = add_attributes( CaseBits32Wirex5DrivenComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    'port_decls:\n',
    'REF_WIRE',
    '''\
        wire_decls:
          wire_decl: foo Array[5] of Wire
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
          wire_decl: foo Array[5] of Wire
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32ClosureConstruct = add_attributes( CaseBits32ClosureConstruct,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: out Port of Vector32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    '''\
        const_decls:
          const_decl: fvar_ref Const of Vector32
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
          const_decl: fvar_ref Const of Vector32
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32ArrayClosureConstruct = add_attributes( CaseBits32ArrayClosureConstruct,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: out Port of Vector32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    '''\
        const_decls:
          const_decl: foo Array[5] of Const
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
          const_decl: foo Array[5] of Const
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseConnectBitSelToOutComp = add_attributes( CaseConnectBitSelToOutComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector1
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: PartSel CurCompAttr in_ 1 2 -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector1
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: PartSel CurCompAttr in_ 1 2 -> CurCompAttr out

        endcomponent
    '''
)

CaseConnectSliceToOutComp = add_attributes( CaseConnectSliceToOutComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector4
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: PartSel CurCompAttr in_ 0 4 -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector4
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: PartSel CurCompAttr in_ 0 4 -> CurCompAttr out

        endcomponent
    '''
)

CaseConnectPortIndexComp = add_attributes( CaseConnectPortIndexComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Array[5] of Port
          port_decl: out Port of Vector32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: PortArrayIdx CurCompAttr in_ 2 -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Array[5] of Port
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: PortArrayIdx CurCompAttr in_ 2 -> CurCompAttr out

        endcomponent
    '''
)

CaseConnectInToWireComp = add_attributes( CaseConnectInToWireComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Array[5] of Port
          port_decl: out Port of Vector32
    ''',
    'REF_WIRE',
    '''\
        wire_decls:
          wire_decl: wire Array[5] of Wire
    ''',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: WireArrayIdx CurCompAttr wire 2 -> CurCompAttr out
          connection: PortArrayIdx CurCompAttr in_ 0 -> WireArrayIdx CurCompAttr wire 0
          connection: PortArrayIdx CurCompAttr in_ 1 -> WireArrayIdx CurCompAttr wire 1
          connection: PortArrayIdx CurCompAttr in_ 2 -> WireArrayIdx CurCompAttr wire 2
          connection: PortArrayIdx CurCompAttr in_ 3 -> WireArrayIdx CurCompAttr wire 3
          connection: PortArrayIdx CurCompAttr in_ 4 -> WireArrayIdx CurCompAttr wire 4
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Array[5] of Port
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
          wire_decl: wire Array[5] of Wire
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: WireArrayIdx CurCompAttr wire 2 -> CurCompAttr out
          connection: PortArrayIdx CurCompAttr in_ 0 -> WireArrayIdx CurCompAttr wire 0
          connection: PortArrayIdx CurCompAttr in_ 1 -> WireArrayIdx CurCompAttr wire 1
          connection: PortArrayIdx CurCompAttr in_ 2 -> WireArrayIdx CurCompAttr wire 2
          connection: PortArrayIdx CurCompAttr in_ 3 -> WireArrayIdx CurCompAttr wire 3
          connection: PortArrayIdx CurCompAttr in_ 4 -> WireArrayIdx CurCompAttr wire 4

        endcomponent
    '''
)

CaseConnectConstToOutComp = add_attributes( CaseConnectConstToOutComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: out Port of Vector32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    '''\
        const_decls:
          const_decl: const Array[5] of Const
    ''',
    'REF_CONN',
    '''\
        connections:
          connection: Bits32(0) -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
          const_decl: const Array[5] of Const
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: Bits32(0) -> CurCompAttr out

        endcomponent
    '''
)

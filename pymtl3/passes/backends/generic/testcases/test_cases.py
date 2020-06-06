"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository for the generic backend.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.testcases import (
    Bits32Foo,
    Bits32x5Foo,
    CaseArrayBits32IfcInComp,
    CaseBits32ArrayClosureConstruct,
    CaseBits32ClosureConstruct,
    CaseBits32ConnectSubCompAttrComp,
    CaseBits32ConstBitsToTmpVarComp,
    CaseBits32ConstIntToTmpVarComp,
    CaseBits32FreeVarToTmpVarComp,
    CaseBits32IfcTmpVarOutComp,
    CaseBits32MultiTmpWireComp,
    CaseBits32PortOnly,
    CaseBits32TmpWireAliasComp,
    CaseBits32TmpWireComp,
    CaseBits32Wirex5DrivenComp,
    CaseBits32x5PortOnly,
    CaseBitSelOverBitSelComp,
    CaseBitSelOverPartSelComp,
    CaseComponentArgsComp,
    CaseComponentDefaultArgsComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectPortIndexComp,
    CaseConnectSliceToOutComp,
    CaseConnectSubCompIfcHierarchyComp,
    CaseConnectValRdyIfcComp,
    CaseDoubleStarArgComp,
    CaseMixedDefaultArgsComp,
    CaseNestedPackedArrayStructComp,
    CaseNestedStructPortOnly,
    CasePartSelOverBitSelComp,
    CasePartSelOverPartSelComp,
    CaseStarArgComp,
    CaseStructConstComp,
    CaseStructIfcTmpVarOutComp,
    CaseStructPortOnly,
    CaseStructTmpWireComp,
    CaseStructWireDrivenComp,
    CaseStructx5PortOnly,
    CaseSubCompFreeVarDrivenComp,
    CaseSubCompTmpDrivenComp,
    CaseTwoUpblksFreevarsComp,
    CaseTwoUpblksSliceComp,
    CaseTwoUpblksStructTmpWireComp,
    CaseUpdateffMixAssignComp,
    CaseWiresDrivenComp,
    NestedBits32Foo,
    NestedStructPackedArray,
    set_attributes,
)

CaseTwoUpblksSliceComp = set_attributes( CaseTwoUpblksSliceComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    'freevars:\n',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector4
          port_decl: out Port of Vector8
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
        connections:

        endcomponent
    '''
)

CaseTwoUpblksFreevarsComp = set_attributes( CaseTwoUpblksFreevarsComp,
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: STATE_IDLE_at_multi_upblks_1
          freevar: STATE_WORK_at_multi_upblks_2
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Array[2] of Port
        interface_decls:
        );
        const_decls:
        freevars:
          freevar: STATE_IDLE_at_multi_upblks_1
          freevar: STATE_WORK_at_multi_upblks_2
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
        connections:

        endcomponent
    '''
)

CaseBits32TmpWireComp = set_attributes( CaseBits32TmpWireComp,
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
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32TmpWireAliasComp = set_attributes( CaseBits32TmpWireAliasComp,
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
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Array[5] of Port
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in multi_upblks_1 of Vector32
          tmpvar: u in multi_upblks_2 of Vector32
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
        connections:

        endcomponent
    '''
)

CaseBits32MultiTmpWireComp = set_attributes( CaseBits32MultiTmpWireComp,
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
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Vector32
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector32
          tmpvar: v in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32FreeVarToTmpVarComp = set_attributes( CaseBits32FreeVarToTmpVarComp,
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
          tmpvar: u in upblk of Vector1
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
        freevars:
          freevar: STATE_IDLE
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector1
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32ConstBitsToTmpVarComp = set_attributes( CaseBits32ConstBitsToTmpVarComp,
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
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32ConstIntToTmpVarComp = set_attributes( CaseBits32ConstIntToTmpVarComp,
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
          tmpvar: u in upblk of Vector1
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
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector1
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseStructTmpWireComp = set_attributes( CaseStructTmpWireComp,
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
          tmpvar: u in upblk of Struct Bits32Foo__foo_32
    ''',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Struct Bits32Foo__foo_32
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Bits32Foo__foo_32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseTwoUpblksStructTmpWireComp = set_attributes( CaseTwoUpblksStructTmpWireComp,
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
          tmpvar: u in multi_upblks_1 of Struct Bits32Foo__foo_32
          tmpvar: u in multi_upblks_2 of Struct Bits32Bar__bar_32
    ''',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        struct Bits32Bar__bar_32
        component DUT
        (
        port_decls:
          port_decl: in_bar Port of Struct Bits32Bar__bar_32
          port_decl: in_foo Port of Struct Bits32Foo__foo_32
          port_decl: out_bar Port of Vector32
          port_decl: out_foo Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in multi_upblks_1 of Bits32Foo__foo_32
          tmpvar: u in multi_upblks_2 of Bits32Bar__bar_32
        upblk_srcs:
          upblk_src: multi_upblks_1
          upblk_src: multi_upblks_2
        connections:

        endcomponent
    '''
)

CaseBits32IfcTmpVarOutComp = set_attributes( CaseBits32IfcTmpVarOutComp,
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
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
          interface_decl: ifc InterfaceView Bits32OutIfc
            interface_ports:
              interface_port: foo Port of Vector32
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseStructIfcTmpVarOutComp = set_attributes( CaseStructIfcTmpVarOutComp,
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
          tmpvar: u in upblk of Struct Bits32Foo__foo_32
    ''',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
          interface_decl: ifc InterfaceView Bits32FooInIfc
            interface_ports:
              interface_port: foo Port of Struct Bits32Foo__foo_32
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Bits32Foo__foo_32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseSubCompTmpDrivenComp = set_attributes( CaseSubCompTmpDrivenComp,
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
    ''',
    'REF_SRC',
    '''\
        component Bits32OutTmpDrivenComp
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
          tmpvar: u in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent

        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
          component_decl: subcomp Component Bits32OutTmpDrivenComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
        tmpvars:
          tmpvar: u in upblk of Vector32
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
'''
)

CaseSubCompFreeVarDrivenComp = set_attributes( CaseSubCompFreeVarDrivenComp,
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
    'tmpvars:\n',
    'REF_SRC',
    '''\
        component Bits32OutFreeVarDrivenComp
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
          freevar: STATE_IDLE
          freevar: STATE_WORK
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent

        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
          freevar: STATE_IDLE
        wire_decls:
        component_decls:
          component_decl: subcomp Component Bits32OutFreeVarDrivenComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseComponentArgsComp = set_attributes( CaseComponentArgsComp,
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

CaseComponentDefaultArgsComp = set_attributes( CaseComponentDefaultArgsComp,
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

CaseMixedDefaultArgsComp = set_attributes( CaseMixedDefaultArgsComp,
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

CaseBits32PortOnly = set_attributes( CaseBits32PortOnly,
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

CaseBits32x5PortOnly = set_attributes( CaseBits32x5PortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Array[5] of Port
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

CaseWiresDrivenComp = set_attributes( CaseWiresDrivenComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    'port_decls:\n',
    'REF_WIRE',
    '''\
        wire_decls:
          wire_decl: bar Wire of Vector4
          wire_decl: foo Wire of Vector32
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
          wire_decl: bar Wire of Vector4
          wire_decl: foo Wire of Vector32
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    '''
)

CaseBits32Wirex5DrivenComp = set_attributes( CaseBits32Wirex5DrivenComp,
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

CaseBits32ClosureConstruct = set_attributes( CaseBits32ClosureConstruct,
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
    # Note that const_decls become emtpy because the constant s.fvar_ref
    # was not used in any upblks!
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
          freevar: foo_at_upblk
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    ''',
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    '''\
        freevars:
          freevar: foo_at_upblk
    '''
)

CaseBits32ArrayClosureConstruct = set_attributes( CaseBits32ArrayClosureConstruct,
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
    'const_decls:\n',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    ''',
    'REF_UPBLK',
    '''\
        upblk_srcs:
          upblk_src: upblk
    ''',
    'REF_FREEVAR',
    'freevars:\n'
)

CaseConnectBitSelToOutComp = set_attributes( CaseConnectBitSelToOutComp,
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
          connection: PartSel CurCompAttr in_ 0 1 -> CurCompAttr out
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
          connection: PartSel CurCompAttr in_ 0 1 -> CurCompAttr out

        endcomponent
    '''
)

CaseConnectSliceToOutComp = set_attributes( CaseConnectSliceToOutComp,
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
          connection: PartSel CurCompAttr in_ 4 8 -> CurCompAttr out
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
          connection: PartSel CurCompAttr in_ 4 8 -> CurCompAttr out

        endcomponent
    '''
)

CaseConnectPortIndexComp = set_attributes( CaseConnectPortIndexComp,
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

CaseConnectInToWireComp = set_attributes( CaseConnectInToWireComp,
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
          wire_decl: wire_ Array[5] of Wire
    ''',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: WireArrayIdx CurCompAttr wire_ 2 -> CurCompAttr out
          connection: PortArrayIdx CurCompAttr in_ 0 -> WireArrayIdx CurCompAttr wire_ 0
          connection: PortArrayIdx CurCompAttr in_ 1 -> WireArrayIdx CurCompAttr wire_ 1
          connection: PortArrayIdx CurCompAttr in_ 2 -> WireArrayIdx CurCompAttr wire_ 2
          connection: PortArrayIdx CurCompAttr in_ 3 -> WireArrayIdx CurCompAttr wire_ 3
          connection: PortArrayIdx CurCompAttr in_ 4 -> WireArrayIdx CurCompAttr wire_ 4
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
          wire_decl: wire_ Array[5] of Wire
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: WireArrayIdx CurCompAttr wire_ 2 -> CurCompAttr out
          connection: PortArrayIdx CurCompAttr in_ 0 -> WireArrayIdx CurCompAttr wire_ 0
          connection: PortArrayIdx CurCompAttr in_ 1 -> WireArrayIdx CurCompAttr wire_ 1
          connection: PortArrayIdx CurCompAttr in_ 2 -> WireArrayIdx CurCompAttr wire_ 2
          connection: PortArrayIdx CurCompAttr in_ 3 -> WireArrayIdx CurCompAttr wire_ 3
          connection: PortArrayIdx CurCompAttr in_ 4 -> WireArrayIdx CurCompAttr wire_ 4

        endcomponent
    '''
)

CaseConnectConstToOutComp = set_attributes( CaseConnectConstToOutComp,
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
          const_decl: const_ Array[5] of Const
    ''',
    'REF_CONN',
    '''\
        connections:
          connection: Bits32(42) -> CurCompAttr out
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
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: Bits32(42) -> CurCompAttr out

        endcomponent
    '''
)

CaseStructPortOnly = set_attributes( CaseStructPortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Struct Bits32Foo__foo_32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    'connections:\n',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Struct Bits32Foo__foo_32
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
    ''',
    'REF_STRUCT',
    [(rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}), 'Bits32Foo__foo_32')]
)

CaseStructWireDrivenComp = set_attributes( CaseStructWireDrivenComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    'port_decls:\n',
    'REF_WIRE',
    '''\
        wire_decls:
          wire_decl: foo Wire of Struct Bits32Foo__foo_32
    ''',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    'connections:\n',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        component DUT
        (
        port_decls:
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
          wire_decl: foo Wire of Struct Bits32Foo__foo_32
        component_decls:
        tmpvars:
        upblk_srcs:
          upblk_src: upblk
        connections:

        endcomponent
    ''',
    'REF_STRUCT',
    [(rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}), 'Bits32Foo__foo_32')]
)

CaseStructConstComp = set_attributes( CaseStructConstComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    'port_decls:\n',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    '''\
        const_decls:
          const_decl: struct_const Const of Struct Bits32Foo__foo_32
    ''',
    'REF_CONN',
    'connections:\n',
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
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:

        endcomponent
    ''',
    'REF_STRUCT',
    [(rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}), 'Bits32Foo__foo_32')]
)

CaseStructx5PortOnly = set_attributes( CaseStructx5PortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Array[5] of Port
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    'connections:\n',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
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
    ''',
    'REF_STRUCT',
    [(rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}), 'Bits32Foo__foo_32')]
)

CaseNestedStructPortOnly = set_attributes( CaseNestedStructPortOnly,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Struct NestedBits32Foo__foo_Bits32Foo__foo_32
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    'connections:\n',
    'REF_SRC',
    '''\
        struct Bits32Foo__foo_32
        struct NestedBits32Foo__foo_Bits32Foo__foo_32
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Struct NestedBits32Foo__foo_Bits32Foo__foo_32
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
    ''',
    'REF_STRUCT',
    [
      (rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}), 'Bits32Foo__foo_32'),
      (rdt.Struct(NestedBits32Foo, {'foo':rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)})}), 'NestedBits32Foo__foo_Bits32Foo__foo_32'),
    ]
)

CaseNestedPackedArrayStructComp = set_attributes( CaseNestedPackedArrayStructComp,
    'REF_NAME',
    'DUT',
    'REF_PORT',
    '''\
        port_decls:
          port_decl: in_ Port of Struct NestedStructPackedArray__foo_Bits32x5Foo__foo_32x5x5
          port_decl: out Port of Struct Bits32x5Foo__foo_32x5
    ''',
    'REF_WIRE',
    'wire_decls:\n',
    'REF_CONST',
    'const_decls:\n',
    'REF_CONN',
    '''\
        connections:
          connection: PackedIndex StructAttr CurCompAttr in_ foo 1 -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        struct Bits32x5Foo__foo_32x5
        struct NestedStructPackedArray__foo_Bits32x5Foo__foo_32x5x5
        component DUT
        (
        port_decls:
          port_decl: in_ Port of Struct NestedStructPackedArray__foo_Bits32x5Foo__foo_32x5x5
          port_decl: out Port of Struct Bits32x5Foo__foo_32x5
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: PackedIndex StructAttr CurCompAttr in_ foo 1 -> CurCompAttr out

        endcomponent
    ''',
    'REF_STRUCT',
    [
      (rdt.Struct(Bits32x5Foo, {'foo':rdt.PackedArray([5], rdt.Vector(32))}), 'Bits32x5Foo__foo_32x5'),
      (rdt.Struct(NestedStructPackedArray, {'foo':rdt.PackedArray([5], rdt.Struct(Bits32x5Foo, {'foo':rdt.PackedArray([5], rdt.Vector(32))}))}), 'NestedStructPackedArray__foo_Bits32x5Foo__foo_32x5x5'),
    ]
)

CaseConnectValRdyIfcComp = set_attributes( CaseConnectValRdyIfcComp,
    'REF_NAME',
    'DUT',
    'REF_IFC',
    '''\
        interface_decls:
          interface_decl: in_ InterfaceView Bits32InValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
          interface_decl: out InterfaceView Bits32OutValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
    ''',
    'REF_CONN',
    '''\
        connections:
          connection: IfcAttr CurCompAttr in_ msg -> IfcAttr CurCompAttr out msg
          connection: IfcAttr CurCompAttr out rdy -> IfcAttr CurCompAttr in_ rdy
          connection: IfcAttr CurCompAttr in_ val -> IfcAttr CurCompAttr out val
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
        interface_decls:
          interface_decl: in_ InterfaceView Bits32InValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
          interface_decl: out InterfaceView Bits32OutValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: IfcAttr CurCompAttr in_ msg -> IfcAttr CurCompAttr out msg
          connection: IfcAttr CurCompAttr out rdy -> IfcAttr CurCompAttr in_ rdy
          connection: IfcAttr CurCompAttr in_ val -> IfcAttr CurCompAttr out val

        endcomponent
    ''',
)

CaseArrayBits32IfcInComp = set_attributes( CaseArrayBits32IfcInComp,
    'REF_NAME',
    'DUT',
    'REF_IFC',
    '''\
        interface_decls:
          interface_decl: in_ Array[2] of InterfaceView Bits32InIfc
            interface_ports:
              interface_port: foo Port of Vector32
    ''',
    'REF_CONN',
    '''\
        connections:
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 foo -> CurCompAttr out
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
          interface_decl: in_ Array[2] of InterfaceView Bits32InIfc
            interface_ports:
              interface_port: foo Port of Vector32
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 foo -> CurCompAttr out

        endcomponent
    ''',
)

CaseConnectArrayNestedIfcComp = set_attributes( CaseConnectArrayNestedIfcComp,
    'REF_NAME',
    'DUT',
    'REF_IFC',
    '''\
        interface_decls:
          interface_decl: in_ Array[2] of InterfaceView MemReqIfc
            interface_ports:
              interface_port: ctrl_foo Port of Vector1
              interface_port: memifc InterfaceView ReqIfc
          interface_decl: out Array[2] of InterfaceView MemRespIfc
            interface_ports:
              interface_port: ctrl_foo Port of Vector1
              interface_port: memifc InterfaceView RespIfc
    ''',
    'REF_CONN',
    '''\
        connections:
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 ctrl_foo -> IfcAttr IfcArrayIdx CurCompAttr out 0 ctrl_foo
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc msg -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc msg
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc rdy -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc rdy
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc val -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc val
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 ctrl_foo -> IfcAttr IfcArrayIdx CurCompAttr out 1 ctrl_foo
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc msg -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc msg
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc rdy -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc rdy
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc val -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc val
    ''',
    'REF_SRC',
    '''\
        component DUT
        (
        port_decls:
        interface_decls:
          interface_decl: in_ Array[2] of InterfaceView MemReqIfc
            interface_ports:
              interface_port: ctrl_foo Port of Vector1
              interface_port: memifc InterfaceView ReqIfc
          interface_decl: out Array[2] of InterfaceView MemRespIfc
            interface_ports:
              interface_port: ctrl_foo Port of Vector1
              interface_port: memifc InterfaceView RespIfc
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 ctrl_foo -> IfcAttr IfcArrayIdx CurCompAttr out 0 ctrl_foo
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc msg -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc msg
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc rdy -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc rdy
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 0 memifc val -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 0 memifc val
          connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 ctrl_foo -> IfcAttr IfcArrayIdx CurCompAttr out 1 ctrl_foo
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc msg -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc msg
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc rdy -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc rdy
          connection: IfcAttr IfcAttr IfcArrayIdx CurCompAttr in_ 1 memifc val -> IfcAttr IfcAttr IfcArrayIdx CurCompAttr out 1 memifc val

        endcomponent
    ''',
)

CaseBits32ConnectSubCompAttrComp = set_attributes( CaseBits32ConnectSubCompAttrComp,
    'REF_NAME',
    'DUT',
    'REF_CONN',
    '''\
        connections:
          connection: SubCompAttr CurCompAttr b out -> CurCompAttr out
    ''',
    'REF_COMP',
    '''\
        component_decls:
          component_decl: b Component Bits32OutDrivenComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
    ''',
    'REF_SRC',
    '''\
        component Bits32OutDrivenComp
        (
        port_decls:
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
          connection: Bits32(42) -> CurCompAttr out

        endcomponent

        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
          component_decl: b Component Bits32OutDrivenComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
        tmpvars:
        upblk_srcs:
        connections:
          connection: SubCompAttr CurCompAttr b out -> CurCompAttr out

        endcomponent
    ''',
)

CaseConnectSubCompIfcHierarchyComp = set_attributes( CaseConnectSubCompIfcHierarchyComp,
    'REF_NAME',
    'DUT',
    'REF_CONN',
    '''\
        connections:
          connection: SubCompAttr CurCompAttr subcomp out -> CurCompAttr out
          connection: IfcAttr SubCompAttr CurCompAttr subcomp ifc msg -> IfcAttr CurCompAttr ifc msg
          connection: IfcAttr CurCompAttr ifc rdy -> IfcAttr SubCompAttr CurCompAttr subcomp ifc rdy
          connection: IfcAttr SubCompAttr CurCompAttr subcomp ifc val -> IfcAttr CurCompAttr ifc val
    ''',
    'REF_COMP',
    '''\
        component_decls:
          component_decl: subcomp Component Bits32OutDrivenSubComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
              component_ifc: ifc InterfaceView Bits32OutValRdyIfc
                component_ifc_ports:
                  component_ifc_port: msg Port of Vector32
                  component_ifc_port: rdy Port of Vector1
                  component_ifc_port: val Port of Vector1
    ''',
    'REF_SRC',
    '''\
        component Bits32OutDrivenSubComp
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
          interface_decl: ifc InterfaceView Bits32OutValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
        tmpvars:
        upblk_srcs:
        connections:
          connection: Bits32(42) -> CurCompAttr out
          connection: Bits32(42) -> IfcAttr CurCompAttr ifc msg
          connection: Bits1(1) -> IfcAttr CurCompAttr ifc val

        endcomponent

        component DUT
        (
        port_decls:
          port_decl: out Port of Vector32
        interface_decls:
          interface_decl: ifc InterfaceView Bits32OutValRdyIfc
            interface_ports:
              interface_port: msg Port of Vector32
              interface_port: rdy Port of Vector1
              interface_port: val Port of Vector1
        );
        const_decls:
        freevars:
        wire_decls:
        component_decls:
          component_decl: subcomp Component Bits32OutDrivenSubComp
            component_ports:
              component_port: out Port of Vector32
            component_ifcs:
              component_ifc: ifc InterfaceView Bits32OutValRdyIfc
                component_ifc_ports:
                  component_ifc_port: msg Port of Vector32
                  component_ifc_port: rdy Port of Vector1
                  component_ifc_port: val Port of Vector1
        tmpvars:
        upblk_srcs:
        connections:
          connection: SubCompAttr CurCompAttr subcomp out -> CurCompAttr out
          connection: IfcAttr SubCompAttr CurCompAttr subcomp ifc msg -> IfcAttr CurCompAttr ifc msg
          connection: IfcAttr CurCompAttr ifc rdy -> IfcAttr SubCompAttr CurCompAttr subcomp ifc rdy
          connection: IfcAttr SubCompAttr CurCompAttr subcomp ifc val -> IfcAttr CurCompAttr ifc val

        endcomponent
    ''',
)

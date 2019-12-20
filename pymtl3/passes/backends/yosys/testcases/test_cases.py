CaseBits32x2ConcatUnpackedSignalComp = add_attributes( CaseBits32x2ConcatUnpackedSignalComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          output logic [63:0] out,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:1];

          always_comb begin : upblk
            out = { in_[0], in_[1] };
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;

        endmodule
    '''
)

CaseConnectConstToOutComp = add_attributes( CaseConnectConstToOutComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule
    '''
)

CaseForRangeLowerUpperStepPassThroughComp = add_attributes( CaseForRangeLowerUpperStepPassThroughComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 2 )
              out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
            for ( __loopvar__upblk_i = 1; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 2 )
              out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfExpInForStmtComp = add_attributes( CaseIfExpInForStmtComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
              out[__loopvar__upblk_i] = ( __loopvar__upblk_i == 1 ) ? in_[__loopvar__upblk_i] : in_[0];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfExpUnaryOpInForStmtComp = add_attributes( CaseIfExpUnaryOpInForStmtComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
              out[__loopvar__upblk_i] = ( __loopvar__upblk_i == 1 ) ? ~in_[__loopvar__upblk_i] : in_[0];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfBoolOpInForStmtComp = add_attributes( CaseIfBoolOpInForStmtComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
              if ( in_[__loopvar__upblk_i] && ( ( __loopvar__upblk_i < 5 ) ? in_[__loopvar__upblk_i + 1] : in_[4] ) ) begin
                out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
              end
              else
                out[__loopvar__upblk_i] = 32'd0;
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfTmpVarInForStmtComp = add_attributes( CaseIfTmpVarInForStmtComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];
          logic [31:0] __tmpvar__upblk_tmpvar;

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 ) begin
              if ( in_[__loopvar__upblk_i] && ( ( __loopvar__upblk_i < 5 ) ? in_[__loopvar__upblk_i + 1] : in_[4] ) ) begin
                __tmpvar__upblk_tmpvar = in_[__loopvar__upblk_i];
              end
              else
                __tmpvar__upblk_tmpvar = 32'd0;
              out[__loopvar__upblk_i] = __tmpvar__upblk_tmpvar;
            end
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseFixedSizeSliceComp = add_attributes( CaseFixedSizeSliceComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [15:0] in_,
          output logic [7:0] out__0,
          output logic [7:0] out__1,
          input logic [0:0] reset
        );
          logic [31:0] out [0:1];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 2; __loopvar__upblk_i = __loopvar__upblk_i + 1 ) begin
              out[__loopvar__upblk_i] = in_[__tmpvar__upblk_tmpvar * 8 +: 8];
            end
          end

          assign out__0 = out[0];
          assign out__1 = out[1];

        endmodule
    '''
)

CaseBits32FooInBits32OutComp = add_attributes( CaseBits32FooInBits32OutComp,
    'REF_SRC',
    '''\
        module DUT
        (
          input logic [0:0] clk,
          input logic [31:0] in___foo,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [31:0] in_;

          always_comb begin : upblk
            out = in___foo;
          end

          assign in_[31:0] = in___foo;

        endmodule
    '''
)

CaseConstStructInstComp = add_attributes( CaseConstStructInstComp,
    'REF_SRC',
    '''\
    '''
)

CaseStructPackedArrayUpblkComp = add_attributes( CaseStructPackedArrayUpblkComp,
    'REF_SRC',
    '''\
    '''
)

CaseNestedStructPackedArrayUpblkComp = add_attributes( CaseNestedStructPackedArrayUpblkComp,
    'REF_SRC',
    '''\
    '''
)

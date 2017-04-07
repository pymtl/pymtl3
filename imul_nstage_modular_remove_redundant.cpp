#include <cstdio>
#include <ctime>

int A_MUX_SEL_IN  = 0;
int A_MUX_SEL_SUB = 1;
int A_MUX_SEL_B   = 2;
int A_MUX_SEL_X   = 0;
int B_MUX_SEL_A   = 0;
int B_MUX_SEL_IN  = 1;
int B_MUX_SEL_X   = 0;

template<int BW>
class Reg
{
public:
  int in_;
  int out;
  Reg()
  {
    in_ = 0;
    out = 0;
  }
  void up_reg()
  {
    out = in_;
  }
};

template<int BW>
class RegEn
{
public:
  int en;
  int in_;
  int out;
  RegEn()
  {
    en  = 0;
    in_ = 0;
    out = 0;
  }
  void up_regen()
  {
    if (en) out = in_;
  }
};

template<int BW, int NB>
class Mux
{
public:
  int in_[1<<NB];
  int out;
  int sel;
  Mux()
  {
    for (int i=0;i<1<<NB;++i) in_[i] = 0;
    out = 0;
    sel = 0;
  }
  void up_mux()
  {
    out = in_[sel];
  }
};

template<int BW>
class ZeroComp
{
public:
  int in_;
  int out;
  ZeroComp()
  {
    in_ = 0;
    out = 0;
  }
  void up_zerocomp()
  {
    out = (in_ == 0);
  }
};

template<int BW>
class LTComp
{
public:
  int in0;
  int in1;
  int out;
  LTComp()
  {
    in0 = 0;
    in1 = 0;
    out = 0;
  }
  void up_ltcomp()
  {
    out = (in0 < in1);
  }
};

template<int BW>
class Subtractor
{
public:
  int in0;
  int in1;
  int out;
  Subtractor()
  {
    in0 = 0;
    in1 = 0;
    out = 0;
  }
  void up_subtractor()
  {
    out = in0 - in1;
  }
};

template<int BW>
class Adder
{
public:
  int in0;
  int in1;
  int out;
  Adder()
  {
    in0 = 0;
    in1 = 0;
    out = 0;
  }
  void up_adder()
  {
    out = in0 + in1;
  }
};

template<int BW>
class LShifter
{
public:
  int in_;
  int shamt;
  int out;
  LShifter()
  {
    in_ = 0;
    shamt = 1;
    out = 0;
  }
  void up_lshifter()
  {
    out = in_ << shamt;
  }
};

template<int BW>
class RShifter
{
public:
  int in_;
  int shamt;
  int out;
  RShifter()
  {
    in_ = 0;
    shamt = 1;
    out = 0;
  }
  void up_rshifter()
  {
    out = in_ >> shamt;
  }
};

template<int M>
class ValRdyBundle
{
public:
  int val;
  int rdy;
  unsigned long long msg;
};

class StreamSource
{
public:
  ValRdyBundle<2> out;
  unsigned long long ts;
  StreamSource(): ts(0) {}
  void up_src()
  {
    out.msg = ts+95827*(ts&1) | ((ts+(19182)*(ts&1))<<32);
    out.val = 1;
    ts += 1;
  }
};

class StreamSink
{
public:
  ValRdyBundle<1> in_;
  StreamSink() {}
  void up_sink()
  {
    in_.rdy = 1;
  }
};

class StepIfc
{
public:
  int val;
  int a;
  int b;
  int res;
};

class IntMulNstageStep
{
public:
  StepIfc in_;
  StepIfc out;
  LShifter<32> a_lsh;
  RShifter<32> b_rsh;
  Adder<32> adder;
  Mux<32, 1> mux;

  void up_muxsel()
  {
    mux.sel = in_.b & 1;
  }
};

class IntMulNstage
{
public:
  IntMulNstageStep steps[32];
  RegEn<32>        a_preg[16];
  RegEn<32>        b_preg[16];
  RegEn<1>         val_preg[16];
  RegEn<1>         res_preg[16];

  ValRdyBundle<2> req;
  ValRdyBundle<1> resp;
};

class TestHarness
{
public:
  StreamSource src;
  IntMulNstage imul;
  StreamSink   sink;
  void top_imul_steps_1__mux_out_FANOUT_2()
  {
     imul.res_preg[1].in_ = imul.steps[1].mux.out;
  }
  void top_imul_val_preg_4__out_FANOUT_5()
  {
     imul.val_preg[5].in_ = imul.val_preg[4].out;
  }
  void top_imul_steps_24__a_lsh_out_FANOUT_4()
  {
     imul.steps[25].a_lsh.in_ = imul.steps[24].a_lsh.out;
     imul.steps[25].adder.in0 = imul.steps[24].a_lsh.out;
  }
  void top_imul_a_preg_4__out_FANOUT_3()
  {
     imul.steps[8].a_lsh.in_ = imul.a_preg[4].out;
     imul.steps[8].adder.in0 = imul.a_preg[4].out;
  }
  void top_imul_steps_10__in__b_0_1__FANOUT_1()
  {
     imul.steps[10].mux.sel = imul.steps[10].in_.b & 1;
  }
  void top_imul_steps_20__mux_out_FANOUT_4()
  {
     imul.steps[21].adder.in1 = imul.steps[20].mux.out;
     imul.steps[21].mux.in_[0] = imul.steps[20].mux.out;
  }
  void top_imul_req_msg_0_32__FANOUT_1()
  {
     imul.a_preg[0].in_ = imul.req.msg & 4294967295;
  }
  void top_imul_steps_17__mux_out_FANOUT_2()
  {
     imul.res_preg[9].in_ = imul.steps[17].mux.out;
  }
  void top_imul_b_preg_9__out_FANOUT_2()
  {
     imul.steps[18].in_.b = imul.b_preg[9].out;
     imul.steps[18].b_rsh.in_ = imul.b_preg[9].out;
  }
  void top_imul_res_preg_15__out_FANOUT_3()
  {
     imul.steps[30].adder.in1 = imul.res_preg[15].out;
     imul.steps[30].mux.in_[0] = imul.res_preg[15].out;
  }
  void top_imul_steps_6__adder_out_FANOUT_1()
  {
     imul.steps[6].mux.in_[1] = imul.steps[6].adder.out;
  }
  void top_imul_a_preg_12__out_FANOUT_3()
  {
     imul.steps[24].a_lsh.in_ = imul.a_preg[12].out;
     imul.steps[24].adder.in0 = imul.a_preg[12].out;
  }
  void top_imul_steps_9__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[5].in_ = imul.steps[9].b_rsh.out;
  }
  void top_imul_steps_18__in__b_0_1__FANOUT_1()
  {
     imul.steps[18].mux.sel = imul.steps[18].in_.b & 1;
  }
  void top_imul_steps_13__mux_out_FANOUT_2()
  {
     imul.res_preg[7].in_ = imul.steps[13].mux.out;
  }
  void top_imul_val_preg_8__out_FANOUT_5()
  {
     imul.val_preg[9].in_ = imul.val_preg[8].out;
  }
  void top_imul_steps_24__adder_out_FANOUT_1()
  {
     imul.steps[24].mux.in_[1] = imul.steps[24].adder.out;
  }
  void top_imul_steps_1__in__b_0_1__FANOUT_1()
  {
     imul.steps[1].mux.sel = imul.steps[1].in_.b & 1;
  }
  void top_imul_steps_3__adder_out_FANOUT_1()
  {
     imul.steps[3].mux.in_[1] = imul.steps[3].adder.out;
  }
  void top_imul_steps_15__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[8].in_ = imul.steps[15].a_lsh.out;
  }
  void top_imul_steps_29__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[15].in_ = imul.steps[29].b_rsh.out;
  }
  void top_imul_steps_20__in__b_0_1__FANOUT_1()
  {
     imul.steps[20].mux.sel = imul.steps[20].in_.b & 1;
  }
  void top_imul_steps_17__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[9].in_ = imul.steps[17].a_lsh.out;
  }
  void top_imul_res_preg_6__out_FANOUT_3()
  {
     imul.steps[12].adder.in1 = imul.res_preg[6].out;
     imul.steps[12].mux.in_[0] = imul.res_preg[6].out;
  }
  void top_imul_req_msg_32_64__FANOUT_1()
  {
     imul.b_preg[0].in_ = imul.req.msg >> 32;
  }
  void top_imul_b_preg_13__out_FANOUT_2()
  {
     imul.steps[26].in_.b = imul.b_preg[13].out;
     imul.steps[26].b_rsh.in_ = imul.b_preg[13].out;
  }
  void top_imul_steps_14__b_rsh_out_FANOUT_3()
  {
     imul.steps[15].in_.b = imul.steps[14].b_rsh.out;
     imul.steps[15].b_rsh.in_ = imul.steps[14].b_rsh.out;
  }
  void top_imul_steps_21__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[11].in_ = imul.steps[21].b_rsh.out;
  }
  void top_imul_steps_7__in__b_0_1__FANOUT_1()
  {
     imul.steps[7].mux.sel = imul.steps[7].in_.b & 1;
  }
  void top_imul_steps_25__mux_out_FANOUT_2()
  {
     imul.res_preg[13].in_ = imul.steps[25].mux.out;
  }
  void top_imul_steps_22__mux_out_FANOUT_4()
  {
     imul.steps[23].adder.in1 = imul.steps[22].mux.out;
     imul.steps[23].mux.in_[0] = imul.steps[22].mux.out;
  }
  void top_imul_a_preg_9__out_FANOUT_3()
  {
     imul.steps[18].a_lsh.in_ = imul.a_preg[9].out;
     imul.steps[18].adder.in0 = imul.a_preg[9].out;
  }
  void top_imul_steps_30__in__b_0_1__FANOUT_1()
  {
     imul.steps[30].mux.sel = imul.steps[30].in_.b & 1;
  }
  void top_imul_steps_27__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[14].in_ = imul.steps[27].a_lsh.out;
  }
  void top_imul_a_preg_1__out_FANOUT_3()
  {
     imul.steps[2].a_lsh.in_ = imul.a_preg[1].out;
     imul.steps[2].adder.in0 = imul.a_preg[1].out;
  }
  void top_imul_steps_25__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[13].in_ = imul.steps[25].b_rsh.out;
  }
  void top_imul_steps_30__mux_out_FANOUT_4()
  {
     imul.steps[31].adder.in1 = imul.steps[30].mux.out;
     imul.steps[31].mux.in_[0] = imul.steps[30].mux.out;
  }
  void top_imul_steps_6__a_lsh_out_FANOUT_4()
  {
     imul.steps[7].a_lsh.in_ = imul.steps[6].a_lsh.out;
     imul.steps[7].adder.in0 = imul.steps[6].a_lsh.out;
  }
  void top_imul_val_preg_12__out_FANOUT_5()
  {
     imul.val_preg[13].in_ = imul.val_preg[12].out;
  }
  void top_imul_steps_13__in__b_0_1__FANOUT_1()
  {
     imul.steps[13].mux.sel = imul.steps[13].in_.b & 1;
  }
  void top_imul_steps_23__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[12].in_ = imul.steps[23].b_rsh.out;
  }
  void top_imul_val_preg_10__out_FANOUT_5()
  {
     imul.val_preg[11].in_ = imul.val_preg[10].out;
  }
  void top_imul_steps_17__adder_out_FANOUT_1()
  {
     imul.steps[17].mux.in_[1] = imul.steps[17].adder.out;
  }
  void top_imul_val_preg_15__out_FANOUT_6()
  {
     sink.in_.val = imul.val_preg[15].out;
     imul.resp.val = imul.val_preg[15].out;
  }
  void top_imul_res_preg_10__out_FANOUT_3()
  {
     imul.steps[20].adder.in1 = imul.res_preg[10].out;
     imul.steps[20].mux.in_[0] = imul.res_preg[10].out;
  }
  void top_imul_val_preg_1__out_FANOUT_5()
  {
     imul.val_preg[2].in_ = imul.val_preg[1].out;
  }
  void top_imul_steps_12__a_lsh_out_FANOUT_4()
  {
     imul.steps[13].a_lsh.in_ = imul.steps[12].a_lsh.out;
     imul.steps[13].adder.in0 = imul.steps[12].a_lsh.out;
  }
  void top_imul_steps_17__in__b_0_1__FANOUT_1()
  {
     imul.steps[17].mux.sel = imul.steps[17].in_.b & 1;
  }
  void top_imul_a_preg_11__out_FANOUT_3()
  {
     imul.steps[22].a_lsh.in_ = imul.a_preg[11].out;
     imul.steps[22].adder.in0 = imul.a_preg[11].out;
  }
  void top_imul_steps_14__mux_out_FANOUT_4()
  {
     imul.steps[15].adder.in1 = imul.steps[14].mux.out;
     imul.steps[15].mux.in_[0] = imul.steps[14].mux.out;
  }
  void top_imul_steps_23__adder_out_FANOUT_1()
  {
     imul.steps[23].mux.in_[1] = imul.steps[23].adder.out;
  }
  void top_imul_steps_16__mux_out_FANOUT_4()
  {
     imul.steps[17].adder.in1 = imul.steps[16].mux.out;
     imul.steps[17].mux.in_[0] = imul.steps[16].mux.out;
  }
  void top_imul_steps_2__in__b_0_1__FANOUT_1()
  {
     imul.steps[2].mux.sel = imul.steps[2].in_.b & 1;
  }
  void top_imul_val_preg_3__out_FANOUT_5()
  {
     imul.val_preg[4].in_ = imul.val_preg[3].out;
  }
  void top_imul_b_preg_2__out_FANOUT_2()
  {
     imul.steps[4].in_.b = imul.b_preg[2].out;
     imul.steps[4].b_rsh.in_ = imul.b_preg[2].out;
  }
  void top_imul_steps_27__in__b_0_1__FANOUT_1()
  {
     imul.steps[27].mux.sel = imul.steps[27].in_.b & 1;
  }
  void top_imul_steps_0__in__b_0_1__FANOUT_1()
  {
     imul.steps[0].mux.sel = imul.steps[0].in_.b & 1;
  }
  void top_imul_steps_20__b_rsh_out_FANOUT_3()
  {
     imul.steps[21].in_.b = imul.steps[20].b_rsh.out;
     imul.steps[21].b_rsh.in_ = imul.steps[20].b_rsh.out;
  }
  void top_imul_steps_12__adder_out_FANOUT_1()
  {
     imul.steps[12].mux.in_[1] = imul.steps[12].adder.out;
  }
  void top_imul_b_preg_8__out_FANOUT_2()
  {
     imul.steps[16].in_.b = imul.b_preg[8].out;
     imul.steps[16].b_rsh.in_ = imul.b_preg[8].out;
  }
  void top_imul_res_preg_14__out_FANOUT_3()
  {
     imul.steps[28].adder.in1 = imul.res_preg[14].out;
     imul.steps[28].mux.in_[0] = imul.res_preg[14].out;
  }
  void top_src_out_msg_FANOUT_1()
  {
     imul.req.msg = src.out.msg;
  }
  void top_imul_steps_7__mux_out_FANOUT_2()
  {
     imul.res_preg[4].in_ = imul.steps[7].mux.out;
  }
  void top_imul_steps_30__b_rsh_out_FANOUT_3()
  {
     imul.steps[31].in_.b = imul.steps[30].b_rsh.out;
     imul.steps[31].b_rsh.in_ = imul.steps[30].b_rsh.out;
  }
  void top_imul_a_preg_13__out_FANOUT_3()
  {
     imul.steps[26].a_lsh.in_ = imul.a_preg[13].out;
     imul.steps[26].adder.in0 = imul.a_preg[13].out;
  }
  void top_imul_res_preg_1__out_FANOUT_3()
  {
     imul.steps[2].adder.in1 = imul.res_preg[1].out;
     imul.steps[2].mux.in_[0] = imul.res_preg[1].out;
  }
  void top_imul_steps_6__mux_out_FANOUT_4()
  {
     imul.steps[7].adder.in1 = imul.steps[6].mux.out;
     imul.steps[7].mux.in_[0] = imul.steps[6].mux.out;
  }
  void top_imul_steps_9__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[5].in_ = imul.steps[9].a_lsh.out;
  }
  void top_imul_steps_29__adder_out_FANOUT_1()
  {
     imul.steps[29].mux.in_[1] = imul.steps[29].adder.out;
  }
  void top_imul_val_preg_7__out_FANOUT_5()
  {
     imul.val_preg[8].in_ = imul.val_preg[7].out;
  }
  void top_imul_steps_11__mux_out_FANOUT_2()
  {
     imul.res_preg[6].in_ = imul.steps[11].mux.out;
  }
  void top_imul_steps_16__in__b_0_1__FANOUT_1()
  {
     imul.steps[16].mux.sel = imul.steps[16].in_.b & 1;
  }
  void top_imul_steps_26__mux_out_FANOUT_4()
  {
     imul.steps[27].adder.in1 = imul.steps[26].mux.out;
     imul.steps[27].mux.in_[0] = imul.steps[26].mux.out;
  }
  void top_imul_steps_13__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[7].in_ = imul.steps[13].b_rsh.out;
  }
  void top_imul_steps_0__adder_out_FANOUT_1()
  {
     imul.steps[0].mux.in_[1] = imul.steps[0].adder.out;
  }
  void top_imul_steps_0__b_rsh_out_FANOUT_3()
  {
     imul.steps[1].in_.b = imul.steps[0].b_rsh.out;
     imul.steps[1].b_rsh.in_ = imul.steps[0].b_rsh.out;
  }
  void top_imul_val_preg_9__out_FANOUT_5()
  {
     imul.val_preg[10].in_ = imul.val_preg[9].out;
  }
  void top_imul_res_preg_5__out_FANOUT_3()
  {
     imul.steps[10].adder.in1 = imul.res_preg[5].out;
     imul.steps[10].mux.in_[0] = imul.res_preg[5].out;
  }
  void top_imul_b_preg_12__out_FANOUT_2()
  {
     imul.steps[24].in_.b = imul.b_preg[12].out;
     imul.steps[24].b_rsh.in_ = imul.b_preg[12].out;
  }
  void top_imul_steps_14__a_lsh_out_FANOUT_4()
  {
     imul.steps[15].a_lsh.in_ = imul.steps[14].a_lsh.out;
     imul.steps[15].adder.in0 = imul.steps[14].a_lsh.out;
  }
  void top_imul_res_preg_9__out_FANOUT_3()
  {
     imul.steps[18].adder.in1 = imul.res_preg[9].out;
     imul.steps[18].mux.in_[0] = imul.res_preg[9].out;
  }
  void top_imul_steps_0__a_lsh_out_FANOUT_4()
  {
     imul.steps[1].a_lsh.in_ = imul.steps[0].a_lsh.out;
     imul.steps[1].adder.in0 = imul.steps[0].a_lsh.out;
  }
  void top_imul_steps_14__in__b_0_1__FANOUT_1()
  {
     imul.steps[14].mux.sel = imul.steps[14].in_.b & 1;
  }
  void top_imul_steps_5__mux_out_FANOUT_2()
  {
     imul.res_preg[3].in_ = imul.steps[5].mux.out;
  }
  void top_imul_steps_21__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[11].in_ = imul.steps[21].a_lsh.out;
  }
  void top_imul_steps_19__mux_out_FANOUT_2()
  {
     imul.res_preg[10].in_ = imul.steps[19].mux.out;
  }
  void top_imul_a_preg_15__out_FANOUT_3()
  {
     imul.steps[30].a_lsh.in_ = imul.a_preg[15].out;
     imul.steps[30].adder.in0 = imul.a_preg[15].out;
  }
  void top_imul_steps_2__mux_out_FANOUT_4()
  {
     imul.steps[3].adder.in1 = imul.steps[2].mux.out;
     imul.steps[3].mux.in_[0] = imul.steps[2].mux.out;
  }
  void top_imul_steps_4__mux_out_FANOUT_4()
  {
     imul.steps[5].adder.in1 = imul.steps[4].mux.out;
     imul.steps[5].mux.in_[0] = imul.steps[4].mux.out;
  }
  void top_imul_val_preg_11__out_FANOUT_5()
  {
     imul.val_preg[12].in_ = imul.val_preg[11].out;
  }
  void top_imul_steps_12__b_rsh_out_FANOUT_3()
  {
     imul.steps[13].in_.b = imul.steps[12].b_rsh.out;
     imul.steps[13].b_rsh.in_ = imul.steps[12].b_rsh.out;
  }
  void top_imul_steps_25__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[13].in_ = imul.steps[25].a_lsh.out;
  }
  void top_imul_b_preg_6__out_FANOUT_2()
  {
     imul.steps[12].in_.b = imul.b_preg[6].out;
     imul.steps[12].b_rsh.in_ = imul.b_preg[6].out;
  }
  void top_imul_steps_31__mux_out_FANOUT_3()
  {
     sink.in_.msg = imul.steps[31].mux.out;
     imul.resp.msg = imul.steps[31].mux.out;
  }
  void top_imul_steps_23__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[12].in_ = imul.steps[23].a_lsh.out;
  }
  void top_imul_steps_23__in__b_0_1__FANOUT_1()
  {
     imul.steps[23].mux.sel = imul.steps[23].in_.b & 1;
  }
  void top_imul_steps_29__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[15].in_ = imul.steps[29].a_lsh.out;
  }
  void top_imul_steps_19__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[10].in_ = imul.steps[19].a_lsh.out;
  }
  void top_imul_val_preg_0__out_FANOUT_5()
  {
     imul.val_preg[1].in_ = imul.val_preg[0].out;
  }
  void top_imul_steps_10__mux_out_FANOUT_4()
  {
     imul.steps[11].adder.in1 = imul.steps[10].mux.out;
     imul.steps[11].mux.in_[0] = imul.steps[10].mux.out;
  }
  void top_imul_steps_3__mux_out_FANOUT_2()
  {
     imul.res_preg[2].in_ = imul.steps[3].mux.out;
  }
  void top_imul_steps_30__adder_out_FANOUT_1()
  {
     imul.steps[30].mux.in_[1] = imul.steps[30].adder.out;
  }
  void top_imul_steps_18__mux_out_FANOUT_4()
  {
     imul.steps[19].adder.in1 = imul.steps[18].mux.out;
     imul.steps[19].mux.in_[0] = imul.steps[18].mux.out;
  }
  void top_imul_steps_21__adder_out_FANOUT_1()
  {
     imul.steps[21].mux.in_[1] = imul.steps[21].adder.out;
  }
  void top_imul_steps_15__in__b_0_1__FANOUT_1()
  {
     imul.steps[15].mux.sel = imul.steps[15].in_.b & 1;
  }
  void top_imul_steps_8__b_rsh_out_FANOUT_3()
  {
     imul.steps[9].in_.b = imul.steps[8].b_rsh.out;
     imul.steps[9].b_rsh.in_ = imul.steps[8].b_rsh.out;
  }
  void top_imul_steps_4__adder_out_FANOUT_1()
  {
     imul.steps[4].mux.in_[1] = imul.steps[4].adder.out;
  }
  void top_imul_val_preg_2__out_FANOUT_5()
  {
     imul.val_preg[3].in_ = imul.val_preg[2].out;
  }
  void top_imul_steps_16__b_rsh_out_FANOUT_3()
  {
     imul.steps[17].in_.b = imul.steps[16].b_rsh.out;
     imul.steps[17].b_rsh.in_ = imul.steps[16].b_rsh.out;
  }
  void top_imul_steps_25__adder_out_FANOUT_1()
  {
     imul.steps[25].mux.in_[1] = imul.steps[25].adder.out;
  }
  void top_imul_a_preg_5__out_FANOUT_3()
  {
     imul.steps[10].a_lsh.in_ = imul.a_preg[5].out;
     imul.steps[10].adder.in0 = imul.a_preg[5].out;
  }
  void top_imul_steps_13__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[7].in_ = imul.steps[13].a_lsh.out;
  }
  void top_imul_res_preg_2__out_FANOUT_3()
  {
     imul.steps[4].adder.in1 = imul.res_preg[2].out;
     imul.steps[4].mux.in_[0] = imul.res_preg[2].out;
  }
  void top_imul_steps_1__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[1].in_ = imul.steps[1].a_lsh.out;
  }
  void top_imul_steps_28__adder_out_FANOUT_1()
  {
     imul.steps[28].mux.in_[1] = imul.steps[28].adder.out;
  }
  void top_imul_res_preg_0__out_FANOUT_3()
  {
     imul.steps[0].adder.in1 = imul.res_preg[0].out;
     imul.steps[0].mux.in_[0] = imul.res_preg[0].out;
  }
  void top_imul_b_preg_7__out_FANOUT_2()
  {
     imul.steps[14].in_.b = imul.b_preg[7].out;
     imul.steps[14].b_rsh.in_ = imul.b_preg[7].out;
  }
  void top_imul_res_preg_8__out_FANOUT_3()
  {
     imul.steps[16].adder.in1 = imul.res_preg[8].out;
     imul.steps[16].mux.in_[0] = imul.res_preg[8].out;
  }
  void top_imul_steps_11__in__b_0_1__FANOUT_1()
  {
     imul.steps[11].mux.sel = imul.steps[11].in_.b & 1;
  }
  void top_imul_steps_8__in__b_0_1__FANOUT_1()
  {
     imul.steps[8].mux.sel = imul.steps[8].in_.b & 1;
  }
  void top_imul_steps_18__a_lsh_out_FANOUT_4()
  {
     imul.steps[19].a_lsh.in_ = imul.steps[18].a_lsh.out;
     imul.steps[19].adder.in0 = imul.steps[18].a_lsh.out;
  }
  void top_imul_steps_5__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[3].in_ = imul.steps[5].b_rsh.out;
  }
  void top_src_out_val_FANOUT_2()
  {
     imul.req.val = src.out.val;
     imul.val_preg[0].in_ = src.out.val;
  }
  void top_imul_steps_8__a_lsh_out_FANOUT_4()
  {
     imul.steps[9].a_lsh.in_ = imul.steps[8].a_lsh.out;
     imul.steps[9].adder.in0 = imul.steps[8].a_lsh.out;
  }
  void top_imul_steps_30__a_lsh_out_FANOUT_4()
  {
     imul.steps[31].a_lsh.in_ = imul.steps[30].a_lsh.out;
     imul.steps[31].adder.in0 = imul.steps[30].a_lsh.out;
  }
  void top_imul_steps_26__b_rsh_out_FANOUT_3()
  {
     imul.steps[27].in_.b = imul.steps[26].b_rsh.out;
     imul.steps[27].b_rsh.in_ = imul.steps[26].b_rsh.out;
  }
  void top_imul_steps_21__in__b_0_1__FANOUT_1()
  {
     imul.steps[21].mux.sel = imul.steps[21].in_.b & 1;
  }
  void top_imul_val_preg_6__out_FANOUT_5()
  {
     imul.val_preg[7].in_ = imul.val_preg[6].out;
  }
  void top_imul_steps_18__adder_out_FANOUT_1()
  {
     imul.steps[18].mux.in_[1] = imul.steps[18].adder.out;
  }
  void top_imul_a_preg_8__out_FANOUT_3()
  {
     imul.steps[16].a_lsh.in_ = imul.a_preg[8].out;
     imul.steps[16].adder.in0 = imul.a_preg[8].out;
  }
  void top_imul_steps_11__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[6].in_ = imul.steps[11].b_rsh.out;
  }
  void top_imul_steps_28__a_lsh_out_FANOUT_4()
  {
     imul.steps[29].a_lsh.in_ = imul.steps[28].a_lsh.out;
     imul.steps[29].adder.in0 = imul.steps[28].a_lsh.out;
  }
  void top_imul_steps_1__adder_out_FANOUT_1()
  {
     imul.steps[1].mux.in_[1] = imul.steps[1].adder.out;
  }
  void top_imul_res_preg_4__out_FANOUT_3()
  {
     imul.steps[8].adder.in1 = imul.res_preg[4].out;
     imul.steps[8].mux.in_[0] = imul.res_preg[4].out;
  }
  void top_imul_b_preg_11__out_FANOUT_2()
  {
     imul.steps[22].in_.b = imul.b_preg[11].out;
     imul.steps[22].b_rsh.in_ = imul.b_preg[11].out;
  }
  void top_imul_steps_20__adder_out_FANOUT_1()
  {
     imul.steps[20].mux.in_[1] = imul.steps[20].adder.out;
  }
  void top_imul_b_preg_14__out_FANOUT_2()
  {
     imul.steps[28].in_.b = imul.b_preg[14].out;
     imul.steps[28].b_rsh.in_ = imul.b_preg[14].out;
  }
  void top_imul_a_preg_6__out_FANOUT_3()
  {
     imul.steps[12].a_lsh.in_ = imul.a_preg[6].out;
     imul.steps[12].adder.in0 = imul.a_preg[6].out;
  }
  void top_imul_steps_7__adder_out_FANOUT_1()
  {
     imul.steps[7].mux.in_[1] = imul.steps[7].adder.out;
  }
  void top_imul_steps_24__mux_out_FANOUT_4()
  {
     imul.steps[25].adder.in1 = imul.steps[24].mux.out;
     imul.steps[25].mux.in_[0] = imul.steps[24].mux.out;
  }
  void top_imul_steps_22__in__b_0_1__FANOUT_1()
  {
     imul.steps[22].mux.sel = imul.steps[22].in_.b & 1;
  }
  void top_imul_steps_9__adder_out_FANOUT_1()
  {
     imul.steps[9].mux.in_[1] = imul.steps[9].adder.out;
  }
  void top_imul_steps_19__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[10].in_ = imul.steps[19].b_rsh.out;
  }
  void top_imul_steps_26__in__b_0_1__FANOUT_1()
  {
     imul.steps[26].mux.sel = imul.steps[26].in_.b & 1;
  }
  void top_imul_steps_8__mux_out_FANOUT_4()
  {
     imul.steps[9].adder.in1 = imul.steps[8].mux.out;
     imul.steps[9].mux.in_[0] = imul.steps[8].mux.out;
  }
  void top_imul_steps_2__b_rsh_out_FANOUT_3()
  {
     imul.steps[3].in_.b = imul.steps[2].b_rsh.out;
     imul.steps[3].b_rsh.in_ = imul.steps[2].b_rsh.out;
  }
  void top_imul_steps_28__in__b_0_1__FANOUT_1()
  {
     imul.steps[28].mux.sel = imul.steps[28].in_.b & 1;
  }
  void top_imul_steps_28__mux_out_FANOUT_4()
  {
     imul.steps[29].adder.in1 = imul.steps[28].mux.out;
     imul.steps[29].mux.in_[0] = imul.steps[28].mux.out;
  }
  void top_imul_a_preg_10__out_FANOUT_3()
  {
     imul.steps[20].a_lsh.in_ = imul.a_preg[10].out;
     imul.steps[20].adder.in0 = imul.a_preg[10].out;
  }
  void top_imul_steps_27__mux_out_FANOUT_2()
  {
     imul.res_preg[14].in_ = imul.steps[27].mux.out;
  }
  void top_imul_res_preg_7__out_FANOUT_3()
  {
     imul.steps[14].adder.in1 = imul.res_preg[7].out;
     imul.steps[14].mux.in_[0] = imul.res_preg[7].out;
  }
  void top_sink_in__rdy_FANOUT_67()
  {
     src.out.rdy = sink.in_.rdy;
     imul.resp.rdy = sink.in_.rdy;
     imul.a_preg[0].en = sink.in_.rdy;
     imul.b_preg[0].en = sink.in_.rdy;
     imul.val_preg[0].en = sink.in_.rdy;
     imul.res_preg[0].en = sink.in_.rdy;
     imul.a_preg[1].en = sink.in_.rdy;
     imul.b_preg[1].en = sink.in_.rdy;
     imul.val_preg[1].en = sink.in_.rdy;
     imul.res_preg[1].en = sink.in_.rdy;
     imul.a_preg[2].en = sink.in_.rdy;
     imul.b_preg[2].en = sink.in_.rdy;
     imul.val_preg[2].en = sink.in_.rdy;
     imul.res_preg[2].en = sink.in_.rdy;
     imul.a_preg[3].en = sink.in_.rdy;
     imul.b_preg[3].en = sink.in_.rdy;
     imul.val_preg[3].en = sink.in_.rdy;
     imul.res_preg[3].en = sink.in_.rdy;
     imul.a_preg[4].en = sink.in_.rdy;
     imul.b_preg[4].en = sink.in_.rdy;
     imul.val_preg[4].en = sink.in_.rdy;
     imul.res_preg[4].en = sink.in_.rdy;
     imul.a_preg[5].en = sink.in_.rdy;
     imul.b_preg[5].en = sink.in_.rdy;
     imul.val_preg[5].en = sink.in_.rdy;
     imul.res_preg[5].en = sink.in_.rdy;
     imul.a_preg[6].en = sink.in_.rdy;
     imul.b_preg[6].en = sink.in_.rdy;
     imul.val_preg[6].en = sink.in_.rdy;
     imul.res_preg[6].en = sink.in_.rdy;
     imul.a_preg[7].en = sink.in_.rdy;
     imul.b_preg[7].en = sink.in_.rdy;
     imul.val_preg[7].en = sink.in_.rdy;
     imul.res_preg[7].en = sink.in_.rdy;
     imul.a_preg[8].en = sink.in_.rdy;
     imul.b_preg[8].en = sink.in_.rdy;
     imul.val_preg[8].en = sink.in_.rdy;
     imul.res_preg[8].en = sink.in_.rdy;
     imul.a_preg[9].en = sink.in_.rdy;
     imul.b_preg[9].en = sink.in_.rdy;
     imul.val_preg[9].en = sink.in_.rdy;
     imul.res_preg[9].en = sink.in_.rdy;
     imul.a_preg[10].en = sink.in_.rdy;
     imul.b_preg[10].en = sink.in_.rdy;
     imul.val_preg[10].en = sink.in_.rdy;
     imul.res_preg[10].en = sink.in_.rdy;
     imul.a_preg[11].en = sink.in_.rdy;
     imul.b_preg[11].en = sink.in_.rdy;
     imul.val_preg[11].en = sink.in_.rdy;
     imul.res_preg[11].en = sink.in_.rdy;
     imul.a_preg[12].en = sink.in_.rdy;
     imul.b_preg[12].en = sink.in_.rdy;
     imul.val_preg[12].en = sink.in_.rdy;
     imul.res_preg[12].en = sink.in_.rdy;
     imul.a_preg[13].en = sink.in_.rdy;
     imul.b_preg[13].en = sink.in_.rdy;
     imul.val_preg[13].en = sink.in_.rdy;
     imul.res_preg[13].en = sink.in_.rdy;
     imul.a_preg[14].en = sink.in_.rdy;
     imul.b_preg[14].en = sink.in_.rdy;
     imul.val_preg[14].en = sink.in_.rdy;
     imul.res_preg[14].en = sink.in_.rdy;
     imul.a_preg[15].en = sink.in_.rdy;
     imul.b_preg[15].en = sink.in_.rdy;
     imul.val_preg[15].en = sink.in_.rdy;
     imul.res_preg[15].en = sink.in_.rdy;
     imul.req.rdy = sink.in_.rdy;
  }
  void top_imul_steps_24__in__b_0_1__FANOUT_1()
  {
     imul.steps[24].mux.sel = imul.steps[24].in_.b & 1;
  }
  void top_imul_steps_10__b_rsh_out_FANOUT_3()
  {
     imul.steps[11].in_.b = imul.steps[10].b_rsh.out;
     imul.steps[11].b_rsh.in_ = imul.steps[10].b_rsh.out;
  }
  void top_imul_b_preg_5__out_FANOUT_2()
  {
     imul.steps[10].in_.b = imul.b_preg[5].out;
     imul.steps[10].b_rsh.in_ = imul.b_preg[5].out;
  }
  void top_imul_steps_31__in__b_0_1__FANOUT_1()
  {
     imul.steps[31].mux.sel = imul.steps[31].in_.b & 1;
  }
  void top_imul_a_preg_2__out_FANOUT_3()
  {
     imul.steps[4].a_lsh.in_ = imul.a_preg[2].out;
     imul.steps[4].adder.in0 = imul.a_preg[2].out;
  }
  void top_imul_steps_3__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[2].in_ = imul.steps[3].a_lsh.out;
  }
  void top_imul_steps_7__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[4].in_ = imul.steps[7].b_rsh.out;
  }
  void top_imul_b_preg_1__out_FANOUT_2()
  {
     imul.steps[2].in_.b = imul.b_preg[1].out;
     imul.steps[2].b_rsh.in_ = imul.b_preg[1].out;
  }
  void top_imul_steps_12__mux_out_FANOUT_4()
  {
     imul.steps[13].adder.in1 = imul.steps[12].mux.out;
     imul.steps[13].mux.in_[0] = imul.steps[12].mux.out;
  }
  void top_imul_steps_26__a_lsh_out_FANOUT_4()
  {
     imul.steps[27].a_lsh.in_ = imul.steps[26].a_lsh.out;
     imul.steps[27].adder.in0 = imul.steps[26].a_lsh.out;
  }
  void top_imul_steps_19__in__b_0_1__FANOUT_1()
  {
     imul.steps[19].mux.sel = imul.steps[19].in_.b & 1;
  }
  void top_imul_steps_16__a_lsh_out_FANOUT_4()
  {
     imul.steps[17].a_lsh.in_ = imul.steps[16].a_lsh.out;
     imul.steps[17].adder.in0 = imul.steps[16].a_lsh.out;
  }
  void top_imul_steps_27__adder_out_FANOUT_1()
  {
     imul.steps[27].mux.in_[1] = imul.steps[27].adder.out;
  }
  void top_imul_res_preg_12__out_FANOUT_3()
  {
     imul.steps[24].adder.in1 = imul.res_preg[12].out;
     imul.steps[24].mux.in_[0] = imul.res_preg[12].out;
  }
  void top_imul_a_preg_7__out_FANOUT_3()
  {
     imul.steps[14].a_lsh.in_ = imul.a_preg[7].out;
     imul.steps[14].adder.in0 = imul.a_preg[7].out;
  }
  void top_imul_steps_6__in__b_0_1__FANOUT_1()
  {
     imul.steps[6].mux.sel = imul.steps[6].in_.b & 1;
  }
  void top_imul_steps_7__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[4].in_ = imul.steps[7].a_lsh.out;
  }
  void top_imul_steps_29__in__b_0_1__FANOUT_1()
  {
     imul.steps[29].mux.sel = imul.steps[29].in_.b & 1;
  }
  void top_imul_steps_31__adder_out_FANOUT_1()
  {
     imul.steps[31].mux.in_[1] = imul.steps[31].adder.out;
  }
  void top_imul_steps_22__b_rsh_out_FANOUT_3()
  {
     imul.steps[23].in_.b = imul.steps[22].b_rsh.out;
     imul.steps[23].b_rsh.in_ = imul.steps[22].b_rsh.out;
  }
  void top_imul_steps_24__b_rsh_out_FANOUT_3()
  {
     imul.steps[25].in_.b = imul.steps[24].b_rsh.out;
     imul.steps[25].b_rsh.in_ = imul.steps[24].b_rsh.out;
  }
  void top_imul_steps_3__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[2].in_ = imul.steps[3].b_rsh.out;
  }
  void top_imul_val_preg_5__out_FANOUT_5()
  {
     imul.val_preg[6].in_ = imul.val_preg[5].out;
  }
  void top_imul_steps_25__in__b_0_1__FANOUT_1()
  {
     imul.steps[25].mux.sel = imul.steps[25].in_.b & 1;
  }
  void top_imul_b_preg_3__out_FANOUT_2()
  {
     imul.steps[6].in_.b = imul.b_preg[3].out;
     imul.steps[6].b_rsh.in_ = imul.b_preg[3].out;
  }
  void top_imul_steps_12__in__b_0_1__FANOUT_1()
  {
     imul.steps[12].mux.sel = imul.steps[12].in_.b & 1;
  }
  void top_imul_steps_14__adder_out_FANOUT_1()
  {
     imul.steps[14].mux.in_[1] = imul.steps[14].adder.out;
  }
  void top_imul_steps_16__adder_out_FANOUT_1()
  {
     imul.steps[16].mux.in_[1] = imul.steps[16].adder.out;
  }
  void top_imul_steps_20__a_lsh_out_FANOUT_4()
  {
     imul.steps[21].a_lsh.in_ = imul.steps[20].a_lsh.out;
     imul.steps[21].adder.in0 = imul.steps[20].a_lsh.out;
  }
  void top_imul_res_preg_3__out_FANOUT_3()
  {
     imul.steps[6].adder.in1 = imul.res_preg[3].out;
     imul.steps[6].mux.in_[0] = imul.res_preg[3].out;
  }
  void top_imul_b_preg_10__out_FANOUT_2()
  {
     imul.steps[20].in_.b = imul.b_preg[10].out;
     imul.steps[20].b_rsh.in_ = imul.b_preg[10].out;
  }
  void top_imul_steps_11__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[6].in_ = imul.steps[11].a_lsh.out;
  }
  void top_imul_steps_5__a_lsh_out_FANOUT_2()
  {
     imul.a_preg[3].in_ = imul.steps[5].a_lsh.out;
  }
  void top_imul_steps_15__mux_out_FANOUT_2()
  {
     imul.res_preg[8].in_ = imul.steps[15].mux.out;
  }
  void top_imul_steps_3__in__b_0_1__FANOUT_1()
  {
     imul.steps[3].mux.sel = imul.steps[3].in_.b & 1;
  }
  void top_imul_steps_15__adder_out_FANOUT_1()
  {
     imul.steps[15].mux.in_[1] = imul.steps[15].adder.out;
  }
  void top_imul_steps_5__in__b_0_1__FANOUT_1()
  {
     imul.steps[5].mux.sel = imul.steps[5].in_.b & 1;
  }
  void top_imul_a_preg_14__out_FANOUT_3()
  {
     imul.steps[28].a_lsh.in_ = imul.a_preg[14].out;
     imul.steps[28].adder.in0 = imul.a_preg[14].out;
  }
  void top_imul_steps_9__mux_out_FANOUT_2()
  {
     imul.res_preg[5].in_ = imul.steps[9].mux.out;
  }
  void top_imul_b_preg_0__out_FANOUT_2()
  {
     imul.steps[0].in_.b = imul.b_preg[0].out;
     imul.steps[0].b_rsh.in_ = imul.b_preg[0].out;
  }
  void top_imul_steps_5__adder_out_FANOUT_1()
  {
     imul.steps[5].mux.in_[1] = imul.steps[5].adder.out;
  }
  void top_imul_steps_15__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[8].in_ = imul.steps[15].b_rsh.out;
  }
  void top_imul_steps_17__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[9].in_ = imul.steps[17].b_rsh.out;
  }
  void top_imul_steps_1__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[1].in_ = imul.steps[1].b_rsh.out;
  }
  void top_imul_steps_26__adder_out_FANOUT_1()
  {
     imul.steps[26].mux.in_[1] = imul.steps[26].adder.out;
  }
  void top_imul_steps_28__b_rsh_out_FANOUT_3()
  {
     imul.steps[29].in_.b = imul.steps[28].b_rsh.out;
     imul.steps[29].b_rsh.in_ = imul.steps[28].b_rsh.out;
  }
  void top_imul_steps_21__mux_out_FANOUT_2()
  {
     imul.res_preg[11].in_ = imul.steps[21].mux.out;
  }
  void top_imul_steps_2__a_lsh_out_FANOUT_4()
  {
     imul.steps[3].a_lsh.in_ = imul.steps[2].a_lsh.out;
     imul.steps[3].adder.in0 = imul.steps[2].a_lsh.out;
  }
  void top_imul_steps_4__a_lsh_out_FANOUT_4()
  {
     imul.steps[5].a_lsh.in_ = imul.steps[4].a_lsh.out;
     imul.steps[5].adder.in0 = imul.steps[4].a_lsh.out;
  }
  void top_imul_steps_2__adder_out_FANOUT_1()
  {
     imul.steps[2].mux.in_[1] = imul.steps[2].adder.out;
  }
  void top_imul_steps_11__adder_out_FANOUT_1()
  {
     imul.steps[11].mux.in_[1] = imul.steps[11].adder.out;
  }
  void top_imul_steps_0__mux_out_FANOUT_4()
  {
     imul.steps[1].adder.in1 = imul.steps[0].mux.out;
     imul.steps[1].mux.in_[0] = imul.steps[0].mux.out;
  }
  void top_imul_steps_4__in__b_0_1__FANOUT_1()
  {
     imul.steps[4].mux.sel = imul.steps[4].in_.b & 1;
  }
  void top_imul_steps_27__b_rsh_out_FANOUT_2()
  {
     imul.b_preg[14].in_ = imul.steps[27].b_rsh.out;
  }
  void top_imul_steps_23__mux_out_FANOUT_2()
  {
     imul.res_preg[12].in_ = imul.steps[23].mux.out;
  }
  void top_imul_steps_10__adder_out_FANOUT_1()
  {
     imul.steps[10].mux.in_[1] = imul.steps[10].adder.out;
  }
  void top_imul_steps_22__a_lsh_out_FANOUT_4()
  {
     imul.steps[23].a_lsh.in_ = imul.steps[22].a_lsh.out;
     imul.steps[23].adder.in0 = imul.steps[22].a_lsh.out;
  }
  void top_imul_steps_6__b_rsh_out_FANOUT_3()
  {
     imul.steps[7].in_.b = imul.steps[6].b_rsh.out;
     imul.steps[7].b_rsh.in_ = imul.steps[6].b_rsh.out;
  }
  void top_imul_steps_10__a_lsh_out_FANOUT_4()
  {
     imul.steps[11].a_lsh.in_ = imul.steps[10].a_lsh.out;
     imul.steps[11].adder.in0 = imul.steps[10].a_lsh.out;
  }
  void top_imul_steps_31__a_lsh_out_FANOUT_1()
  {
  }
  void top_imul_steps_22__adder_out_FANOUT_1()
  {
     imul.steps[22].mux.in_[1] = imul.steps[22].adder.out;
  }
  void top_imul_steps_29__mux_out_FANOUT_2()
  {
     imul.res_preg[15].in_ = imul.steps[29].mux.out;
  }
  void top_imul_val_preg_13__out_FANOUT_5()
  {
     imul.val_preg[14].in_ = imul.val_preg[13].out;
  }
  void top_imul_res_preg_13__out_FANOUT_3()
  {
     imul.steps[26].adder.in1 = imul.res_preg[13].out;
     imul.steps[26].mux.in_[0] = imul.res_preg[13].out;
  }
  void top_imul_b_preg_15__out_FANOUT_2()
  {
     imul.steps[30].in_.b = imul.b_preg[15].out;
     imul.steps[30].b_rsh.in_ = imul.b_preg[15].out;
  }
  void top_imul_steps_18__b_rsh_out_FANOUT_3()
  {
     imul.steps[19].in_.b = imul.steps[18].b_rsh.out;
     imul.steps[19].b_rsh.in_ = imul.steps[18].b_rsh.out;
  }
  void top_imul_steps_19__adder_out_FANOUT_1()
  {
     imul.steps[19].mux.in_[1] = imul.steps[19].adder.out;
  }
  void top_imul_steps_13__adder_out_FANOUT_1()
  {
     imul.steps[13].mux.in_[1] = imul.steps[13].adder.out;
  }
  void top_imul_val_preg_14__out_FANOUT_5()
  {
     imul.val_preg[15].in_ = imul.val_preg[14].out;
  }
  void top_imul_a_preg_0__out_FANOUT_3()
  {
     imul.steps[0].a_lsh.in_ = imul.a_preg[0].out;
     imul.steps[0].adder.in0 = imul.a_preg[0].out;
  }
  void top_imul_res_preg_11__out_FANOUT_3()
  {
     imul.steps[22].adder.in1 = imul.res_preg[11].out;
     imul.steps[22].mux.in_[0] = imul.res_preg[11].out;
  }
  void top_imul_steps_9__in__b_0_1__FANOUT_1()
  {
     imul.steps[9].mux.sel = imul.steps[9].in_.b & 1;
  }
  void top_imul_b_preg_4__out_FANOUT_2()
  {
     imul.steps[8].in_.b = imul.b_preg[4].out;
     imul.steps[8].b_rsh.in_ = imul.b_preg[4].out;
  }
  void top_imul_a_preg_3__out_FANOUT_3()
  {
     imul.steps[6].a_lsh.in_ = imul.a_preg[3].out;
     imul.steps[6].adder.in0 = imul.a_preg[3].out;
  }
  void top_imul_steps_4__b_rsh_out_FANOUT_3()
  {
     imul.steps[5].in_.b = imul.steps[4].b_rsh.out;
     imul.steps[5].b_rsh.in_ = imul.steps[4].b_rsh.out;
  }
  void top_imul_steps_8__adder_out_FANOUT_1()
  {
     imul.steps[8].mux.in_[1] = imul.steps[8].adder.out;
  }
  void tick_schedule()
  {
    imul.a_preg[13].up_regen();
    imul.res_preg[3].up_regen();
    imul.b_preg[14].up_regen();
    imul.res_preg[1].up_regen();
    imul.val_preg[7].up_regen();
    imul.a_preg[9].up_regen();
    imul.res_preg[14].up_regen();
    imul.val_preg[10].up_regen();
    imul.b_preg[1].up_regen();
    imul.a_preg[1].up_regen();
    imul.a_preg[4].up_regen();
    imul.val_preg[14].up_regen();
    imul.res_preg[6].up_regen();
    imul.b_preg[5].up_regen();
    imul.res_preg[13].up_regen();
    imul.res_preg[8].up_regen();
    imul.res_preg[2].up_regen();
    imul.b_preg[9].up_regen();
    imul.b_preg[8].up_regen();
    imul.b_preg[13].up_regen();
    imul.a_preg[3].up_regen();
    imul.b_preg[10].up_regen();
    imul.val_preg[1].up_regen();
    imul.a_preg[8].up_regen();
    imul.res_preg[9].up_regen();
    imul.val_preg[5].up_regen();
    imul.a_preg[12].up_regen();
    imul.val_preg[9].up_regen();
    imul.b_preg[0].up_regen();
    imul.val_preg[13].up_regen();
    imul.b_preg[4].up_regen();
    sink.up_sink();
    src.up_src();
    imul.res_preg[5].up_regen();
    imul.b_preg[12].up_regen();
    imul.a_preg[2].up_regen();
    imul.val_preg[8].up_regen();
    imul.val_preg[0].up_regen();
    imul.a_preg[6].up_regen();
    imul.res_preg[0].up_regen();
    imul.a_preg[15].up_regen();
    imul.a_preg[7].up_regen();
    imul.val_preg[4].up_regen();
    imul.a_preg[11].up_regen();
    imul.res_preg[12].up_regen();
    imul.b_preg[3].up_regen();
    imul.a_preg[0].up_regen();
    imul.val_preg[12].up_regen();
    imul.b_preg[11].up_regen();
    imul.val_preg[2].up_regen();
    imul.b_preg[15].up_regen();
    imul.a_preg[5].up_regen();
    imul.res_preg[10].up_regen();
    imul.res_preg[4].up_regen();
    imul.res_preg[7].up_regen();
    imul.val_preg[3].up_regen();
    imul.a_preg[10].up_regen();
    imul.res_preg[11].up_regen();
    imul.a_preg[14].up_regen();
    imul.b_preg[7].up_regen();
    imul.res_preg[15].up_regen();
    imul.val_preg[11].up_regen();
    imul.b_preg[2].up_regen();
    imul.val_preg[6].up_regen();
    imul.val_preg[15].up_regen();
    imul.b_preg[6].up_regen();
    top_imul_a_preg_13__out_FANOUT_3();
    top_imul_res_preg_3__out_FANOUT_3();
    top_imul_b_preg_14__out_FANOUT_2();
    top_imul_res_preg_1__out_FANOUT_3();
    top_imul_a_preg_9__out_FANOUT_3();
    top_imul_res_preg_14__out_FANOUT_3();
    top_imul_b_preg_1__out_FANOUT_2();
    top_imul_a_preg_1__out_FANOUT_3();
    top_imul_a_preg_4__out_FANOUT_3();
    top_imul_res_preg_6__out_FANOUT_3();
    top_imul_b_preg_5__out_FANOUT_2();
    top_imul_res_preg_13__out_FANOUT_3();
    top_imul_res_preg_8__out_FANOUT_3();
    top_imul_res_preg_2__out_FANOUT_3();
    top_imul_b_preg_9__out_FANOUT_2();
    top_imul_b_preg_8__out_FANOUT_2();
    top_imul_b_preg_13__out_FANOUT_2();
    top_imul_a_preg_3__out_FANOUT_3();
    top_imul_b_preg_10__out_FANOUT_2();
    top_imul_a_preg_8__out_FANOUT_3();
    top_imul_res_preg_9__out_FANOUT_3();
    top_imul_a_preg_12__out_FANOUT_3();
    top_imul_val_preg_9__out_FANOUT_5();
    top_imul_b_preg_0__out_FANOUT_2();
    top_imul_val_preg_13__out_FANOUT_5();
    top_imul_b_preg_4__out_FANOUT_2();
    top_src_out_msg_FANOUT_1();
    top_imul_res_preg_5__out_FANOUT_3();
    top_imul_b_preg_12__out_FANOUT_2();
    top_imul_a_preg_2__out_FANOUT_3();
    top_imul_val_preg_7__out_FANOUT_5();
    top_imul_val_preg_8__out_FANOUT_5();
    top_imul_val_preg_0__out_FANOUT_5();
    top_src_out_val_FANOUT_2();
    top_imul_a_preg_6__out_FANOUT_3();
    top_imul_res_preg_0__out_FANOUT_3();
    top_imul_a_preg_15__out_FANOUT_3();
    top_imul_a_preg_7__out_FANOUT_3();
    top_imul_val_preg_4__out_FANOUT_5();
    top_imul_a_preg_11__out_FANOUT_3();
    top_imul_res_preg_12__out_FANOUT_3();
    top_imul_b_preg_3__out_FANOUT_2();
    top_imul_a_preg_0__out_FANOUT_3();
    top_imul_val_preg_12__out_FANOUT_5();
    top_imul_b_preg_11__out_FANOUT_2();
    top_imul_val_preg_1__out_FANOUT_5();
    top_imul_b_preg_15__out_FANOUT_2();
    top_imul_a_preg_5__out_FANOUT_3();
    top_imul_res_preg_10__out_FANOUT_3();
    top_imul_res_preg_4__out_FANOUT_3();
    top_imul_res_preg_7__out_FANOUT_3();
    top_imul_val_preg_3__out_FANOUT_5();
    top_imul_val_preg_2__out_FANOUT_5();
    top_imul_a_preg_10__out_FANOUT_3();
    top_imul_res_preg_11__out_FANOUT_3();
    top_imul_a_preg_14__out_FANOUT_3();
    top_imul_b_preg_7__out_FANOUT_2();
    top_imul_res_preg_15__out_FANOUT_3();
    top_imul_val_preg_10__out_FANOUT_5();
    top_imul_val_preg_11__out_FANOUT_5();
    top_imul_b_preg_2__out_FANOUT_2();
    top_imul_val_preg_6__out_FANOUT_5();
    top_imul_val_preg_5__out_FANOUT_5();
    top_imul_val_preg_14__out_FANOUT_5();
    top_imul_val_preg_15__out_FANOUT_6();
    top_imul_b_preg_6__out_FANOUT_2();
    top_sink_in__rdy_FANOUT_67();
    imul.steps[26].a_lsh.up_lshifter();
    imul.steps[28].b_rsh.up_rshifter();
    top_imul_steps_28__in__b_0_1__FANOUT_1();
    imul.steps[18].a_lsh.up_lshifter();
    top_imul_steps_2__in__b_0_1__FANOUT_1();
    imul.steps[2].b_rsh.up_rshifter();
    imul.steps[2].a_lsh.up_lshifter();
    imul.steps[2].adder.up_adder();
    imul.steps[8].a_lsh.up_lshifter();
    imul.steps[10].b_rsh.up_rshifter();
    top_imul_steps_10__in__b_0_1__FANOUT_1();
    imul.steps[26].adder.up_adder();
    imul.steps[18].b_rsh.up_rshifter();
    top_imul_steps_18__in__b_0_1__FANOUT_1();
    imul.steps[16].b_rsh.up_rshifter();
    top_imul_steps_16__in__b_0_1__FANOUT_1();
    imul.steps[26].b_rsh.up_rshifter();
    top_imul_steps_26__in__b_0_1__FANOUT_1();
    imul.steps[6].a_lsh.up_lshifter();
    imul.steps[6].adder.up_adder();
    top_imul_steps_20__in__b_0_1__FANOUT_1();
    imul.steps[20].b_rsh.up_rshifter();
    imul.steps[16].adder.up_adder();
    imul.steps[16].a_lsh.up_lshifter();
    imul.steps[18].adder.up_adder();
    imul.steps[24].a_lsh.up_lshifter();
    imul.steps[0].b_rsh.up_rshifter();
    top_imul_steps_0__in__b_0_1__FANOUT_1();
    top_imul_steps_8__in__b_0_1__FANOUT_1();
    imul.steps[8].b_rsh.up_rshifter();
    top_imul_req_msg_32_64__FANOUT_1();
    top_imul_req_msg_0_32__FANOUT_1();
    top_imul_steps_24__in__b_0_1__FANOUT_1();
    imul.steps[24].b_rsh.up_rshifter();
    imul.steps[4].a_lsh.up_lshifter();
    imul.steps[4].adder.up_adder();
    imul.steps[12].adder.up_adder();
    imul.steps[12].a_lsh.up_lshifter();
    imul.steps[30].a_lsh.up_lshifter();
    imul.steps[14].a_lsh.up_lshifter();
    imul.steps[22].a_lsh.up_lshifter();
    imul.steps[24].adder.up_adder();
    top_imul_steps_6__in__b_0_1__FANOUT_1();
    imul.steps[6].b_rsh.up_rshifter();
    imul.steps[0].adder.up_adder();
    imul.steps[0].a_lsh.up_lshifter();
    imul.steps[22].b_rsh.up_rshifter();
    top_imul_steps_22__in__b_0_1__FANOUT_1();
    top_imul_steps_30__in__b_0_1__FANOUT_1();
    imul.steps[30].b_rsh.up_rshifter();
    imul.steps[10].adder.up_adder();
    imul.steps[10].a_lsh.up_lshifter();
    imul.steps[8].adder.up_adder();
    imul.steps[14].adder.up_adder();
    imul.steps[20].adder.up_adder();
    imul.steps[20].a_lsh.up_lshifter();
    imul.steps[22].adder.up_adder();
    imul.steps[28].adder.up_adder();
    imul.steps[28].a_lsh.up_lshifter();
    imul.steps[14].b_rsh.up_rshifter();
    top_imul_steps_14__in__b_0_1__FANOUT_1();
    imul.steps[30].adder.up_adder();
    imul.steps[4].b_rsh.up_rshifter();
    top_imul_steps_4__in__b_0_1__FANOUT_1();
    imul.steps[12].b_rsh.up_rshifter();
    top_imul_steps_12__in__b_0_1__FANOUT_1();
    top_imul_steps_26__a_lsh_out_FANOUT_4();
    top_imul_steps_28__b_rsh_out_FANOUT_3();
    top_imul_steps_18__a_lsh_out_FANOUT_4();
    top_imul_steps_2__b_rsh_out_FANOUT_3();
    top_imul_steps_2__a_lsh_out_FANOUT_4();
    top_imul_steps_2__adder_out_FANOUT_1();
    top_imul_steps_8__a_lsh_out_FANOUT_4();
    top_imul_steps_10__b_rsh_out_FANOUT_3();
    top_imul_steps_26__adder_out_FANOUT_1();
    top_imul_steps_18__b_rsh_out_FANOUT_3();
    top_imul_steps_16__b_rsh_out_FANOUT_3();
    top_imul_steps_26__b_rsh_out_FANOUT_3();
    top_imul_steps_6__a_lsh_out_FANOUT_4();
    top_imul_steps_6__adder_out_FANOUT_1();
    top_imul_steps_20__b_rsh_out_FANOUT_3();
    top_imul_steps_16__adder_out_FANOUT_1();
    top_imul_steps_16__a_lsh_out_FANOUT_4();
    top_imul_steps_18__adder_out_FANOUT_1();
    top_imul_steps_24__a_lsh_out_FANOUT_4();
    top_imul_steps_0__b_rsh_out_FANOUT_3();
    top_imul_steps_8__b_rsh_out_FANOUT_3();
    top_imul_steps_24__b_rsh_out_FANOUT_3();
    top_imul_steps_4__a_lsh_out_FANOUT_4();
    top_imul_steps_4__adder_out_FANOUT_1();
    top_imul_steps_12__adder_out_FANOUT_1();
    top_imul_steps_12__a_lsh_out_FANOUT_4();
    top_imul_steps_30__a_lsh_out_FANOUT_4();
    top_imul_steps_14__a_lsh_out_FANOUT_4();
    top_imul_steps_22__a_lsh_out_FANOUT_4();
    top_imul_steps_24__adder_out_FANOUT_1();
    top_imul_steps_6__b_rsh_out_FANOUT_3();
    top_imul_steps_0__adder_out_FANOUT_1();
    top_imul_steps_0__a_lsh_out_FANOUT_4();
    top_imul_steps_22__b_rsh_out_FANOUT_3();
    top_imul_steps_30__b_rsh_out_FANOUT_3();
    top_imul_steps_10__adder_out_FANOUT_1();
    top_imul_steps_10__a_lsh_out_FANOUT_4();
    top_imul_steps_8__adder_out_FANOUT_1();
    top_imul_steps_14__adder_out_FANOUT_1();
    top_imul_steps_20__adder_out_FANOUT_1();
    top_imul_steps_20__a_lsh_out_FANOUT_4();
    top_imul_steps_22__adder_out_FANOUT_1();
    top_imul_steps_28__adder_out_FANOUT_1();
    top_imul_steps_28__a_lsh_out_FANOUT_4();
    top_imul_steps_14__b_rsh_out_FANOUT_3();
    top_imul_steps_30__adder_out_FANOUT_1();
    top_imul_steps_4__b_rsh_out_FANOUT_3();
    top_imul_steps_12__b_rsh_out_FANOUT_3();
    imul.steps[27].a_lsh.up_lshifter();
    imul.steps[29].b_rsh.up_rshifter();
    top_imul_steps_29__in__b_0_1__FANOUT_1();
    imul.steps[19].a_lsh.up_lshifter();
    imul.steps[3].b_rsh.up_rshifter();
    top_imul_steps_3__in__b_0_1__FANOUT_1();
    imul.steps[3].a_lsh.up_lshifter();
    imul.steps[2].mux.up_mux();
    imul.steps[9].a_lsh.up_lshifter();
    imul.steps[11].b_rsh.up_rshifter();
    top_imul_steps_11__in__b_0_1__FANOUT_1();
    imul.steps[26].mux.up_mux();
    imul.steps[19].b_rsh.up_rshifter();
    top_imul_steps_19__in__b_0_1__FANOUT_1();
    imul.steps[17].b_rsh.up_rshifter();
    top_imul_steps_17__in__b_0_1__FANOUT_1();
    top_imul_steps_27__in__b_0_1__FANOUT_1();
    imul.steps[27].b_rsh.up_rshifter();
    imul.steps[7].a_lsh.up_lshifter();
    imul.steps[6].mux.up_mux();
    top_imul_steps_21__in__b_0_1__FANOUT_1();
    imul.steps[21].b_rsh.up_rshifter();
    imul.steps[16].mux.up_mux();
    imul.steps[17].a_lsh.up_lshifter();
    imul.steps[18].mux.up_mux();
    imul.steps[25].a_lsh.up_lshifter();
    top_imul_steps_1__in__b_0_1__FANOUT_1();
    imul.steps[1].b_rsh.up_rshifter();
    top_imul_steps_9__in__b_0_1__FANOUT_1();
    imul.steps[9].b_rsh.up_rshifter();
    top_imul_steps_25__in__b_0_1__FANOUT_1();
    imul.steps[25].b_rsh.up_rshifter();
    imul.steps[5].a_lsh.up_lshifter();
    imul.steps[4].mux.up_mux();
    imul.steps[12].mux.up_mux();
    imul.steps[13].a_lsh.up_lshifter();
    imul.steps[31].a_lsh.up_lshifter();
    imul.steps[15].a_lsh.up_lshifter();
    imul.steps[23].a_lsh.up_lshifter();
    imul.steps[24].mux.up_mux();
    imul.steps[7].b_rsh.up_rshifter();
    top_imul_steps_7__in__b_0_1__FANOUT_1();
    imul.steps[0].mux.up_mux();
    imul.steps[1].a_lsh.up_lshifter();
    imul.steps[23].b_rsh.up_rshifter();
    top_imul_steps_23__in__b_0_1__FANOUT_1();
    imul.steps[31].b_rsh.up_rshifter();
    top_imul_steps_31__in__b_0_1__FANOUT_1();
    imul.steps[10].mux.up_mux();
    imul.steps[11].a_lsh.up_lshifter();
    imul.steps[8].mux.up_mux();
    imul.steps[14].mux.up_mux();
    imul.steps[20].mux.up_mux();
    imul.steps[21].a_lsh.up_lshifter();
    imul.steps[22].mux.up_mux();
    imul.steps[28].mux.up_mux();
    imul.steps[29].a_lsh.up_lshifter();
    top_imul_steps_15__in__b_0_1__FANOUT_1();
    imul.steps[15].b_rsh.up_rshifter();
    imul.steps[30].mux.up_mux();
    top_imul_steps_5__in__b_0_1__FANOUT_1();
    imul.steps[5].b_rsh.up_rshifter();
    top_imul_steps_13__in__b_0_1__FANOUT_1();
    imul.steps[13].b_rsh.up_rshifter();
    top_imul_steps_27__a_lsh_out_FANOUT_2();
    top_imul_steps_29__b_rsh_out_FANOUT_2();
    top_imul_steps_19__a_lsh_out_FANOUT_2();
    top_imul_steps_3__b_rsh_out_FANOUT_2();
    top_imul_steps_3__a_lsh_out_FANOUT_2();
    top_imul_steps_2__mux_out_FANOUT_4();
    top_imul_steps_9__a_lsh_out_FANOUT_2();
    top_imul_steps_11__b_rsh_out_FANOUT_2();
    top_imul_steps_26__mux_out_FANOUT_4();
    top_imul_steps_19__b_rsh_out_FANOUT_2();
    top_imul_steps_17__b_rsh_out_FANOUT_2();
    top_imul_steps_27__b_rsh_out_FANOUT_2();
    top_imul_steps_7__a_lsh_out_FANOUT_2();
    top_imul_steps_6__mux_out_FANOUT_4();
    top_imul_steps_21__b_rsh_out_FANOUT_2();
    top_imul_steps_16__mux_out_FANOUT_4();
    top_imul_steps_17__a_lsh_out_FANOUT_2();
    top_imul_steps_18__mux_out_FANOUT_4();
    top_imul_steps_25__a_lsh_out_FANOUT_2();
    top_imul_steps_1__b_rsh_out_FANOUT_2();
    top_imul_steps_9__b_rsh_out_FANOUT_2();
    top_imul_steps_25__b_rsh_out_FANOUT_2();
    top_imul_steps_5__a_lsh_out_FANOUT_2();
    top_imul_steps_4__mux_out_FANOUT_4();
    top_imul_steps_12__mux_out_FANOUT_4();
    top_imul_steps_13__a_lsh_out_FANOUT_2();
    top_imul_steps_31__a_lsh_out_FANOUT_1();
    top_imul_steps_15__a_lsh_out_FANOUT_2();
    top_imul_steps_23__a_lsh_out_FANOUT_2();
    top_imul_steps_24__mux_out_FANOUT_4();
    top_imul_steps_7__b_rsh_out_FANOUT_2();
    top_imul_steps_0__mux_out_FANOUT_4();
    top_imul_steps_1__a_lsh_out_FANOUT_2();
    top_imul_steps_23__b_rsh_out_FANOUT_2();
    top_imul_steps_10__mux_out_FANOUT_4();
    top_imul_steps_11__a_lsh_out_FANOUT_2();
    top_imul_steps_8__mux_out_FANOUT_4();
    top_imul_steps_14__mux_out_FANOUT_4();
    top_imul_steps_20__mux_out_FANOUT_4();
    top_imul_steps_21__a_lsh_out_FANOUT_2();
    top_imul_steps_22__mux_out_FANOUT_4();
    top_imul_steps_28__mux_out_FANOUT_4();
    top_imul_steps_29__a_lsh_out_FANOUT_2();
    top_imul_steps_15__b_rsh_out_FANOUT_2();
    top_imul_steps_30__mux_out_FANOUT_4();
    top_imul_steps_5__b_rsh_out_FANOUT_2();
    top_imul_steps_13__b_rsh_out_FANOUT_2();
    imul.steps[3].adder.up_adder();
    imul.steps[27].adder.up_adder();
    imul.steps[7].adder.up_adder();
    imul.steps[17].adder.up_adder();
    imul.steps[19].adder.up_adder();
    imul.steps[5].adder.up_adder();
    imul.steps[13].adder.up_adder();
    imul.steps[25].adder.up_adder();
    imul.steps[1].adder.up_adder();
    imul.steps[11].adder.up_adder();
    imul.steps[9].adder.up_adder();
    imul.steps[15].adder.up_adder();
    imul.steps[21].adder.up_adder();
    imul.steps[23].adder.up_adder();
    imul.steps[29].adder.up_adder();
    imul.steps[31].adder.up_adder();
    top_imul_steps_3__adder_out_FANOUT_1();
    top_imul_steps_27__adder_out_FANOUT_1();
    top_imul_steps_7__adder_out_FANOUT_1();
    top_imul_steps_17__adder_out_FANOUT_1();
    top_imul_steps_19__adder_out_FANOUT_1();
    top_imul_steps_5__adder_out_FANOUT_1();
    top_imul_steps_13__adder_out_FANOUT_1();
    top_imul_steps_25__adder_out_FANOUT_1();
    top_imul_steps_1__adder_out_FANOUT_1();
    top_imul_steps_11__adder_out_FANOUT_1();
    top_imul_steps_9__adder_out_FANOUT_1();
    top_imul_steps_15__adder_out_FANOUT_1();
    top_imul_steps_21__adder_out_FANOUT_1();
    top_imul_steps_23__adder_out_FANOUT_1();
    top_imul_steps_29__adder_out_FANOUT_1();
    top_imul_steps_31__adder_out_FANOUT_1();
    imul.steps[3].mux.up_mux();
    imul.steps[27].mux.up_mux();
    imul.steps[7].mux.up_mux();
    imul.steps[17].mux.up_mux();
    imul.steps[19].mux.up_mux();
    imul.steps[5].mux.up_mux();
    imul.steps[13].mux.up_mux();
    imul.steps[25].mux.up_mux();
    imul.steps[1].mux.up_mux();
    imul.steps[11].mux.up_mux();
    imul.steps[9].mux.up_mux();
    imul.steps[15].mux.up_mux();
    imul.steps[21].mux.up_mux();
    imul.steps[23].mux.up_mux();
    imul.steps[29].mux.up_mux();
    imul.steps[31].mux.up_mux();
    top_imul_steps_3__mux_out_FANOUT_2();
    top_imul_steps_27__mux_out_FANOUT_2();
    top_imul_steps_7__mux_out_FANOUT_2();
    top_imul_steps_17__mux_out_FANOUT_2();
    top_imul_steps_19__mux_out_FANOUT_2();
    top_imul_steps_5__mux_out_FANOUT_2();
    top_imul_steps_13__mux_out_FANOUT_2();
    top_imul_steps_25__mux_out_FANOUT_2();
    top_imul_steps_1__mux_out_FANOUT_2();
    top_imul_steps_11__mux_out_FANOUT_2();
    top_imul_steps_9__mux_out_FANOUT_2();
    top_imul_steps_15__mux_out_FANOUT_2();
    top_imul_steps_21__mux_out_FANOUT_2();
    top_imul_steps_23__mux_out_FANOUT_2();
    top_imul_steps_29__mux_out_FANOUT_2();
    top_imul_steps_31__mux_out_FANOUT_3();
  }
};


int main()
{
  TestHarness *top = new TestHarness();
  printf("%d %d %d\n",sizeof(TestHarness),sizeof(IntMulNstage), sizeof(IntMulNstageStep));
  unsigned long long total_cycle = 20000000;
  time_t start = clock();
  for (unsigned long long cycle=0; cycle<total_cycle; ++cycle)
  {
    top->tick_schedule();
  }
  time_t end = clock();
  printf("req val:%d rdy:%d a:%6d b:%6d ", top->imul.req.val, top->imul.req.rdy, top->imul.req.msg & 4294967295, top->imul.req.msg >> 32);
  printf("resp val:%d rdy:%d imul:%12x", top->imul.resp.val, top->imul.resp.rdy, top->imul.resp.msg);
  puts("");

  printf("Total cycles   : %lld million cycles\n", total_cycle/1000000LL);
  printf("Execution time : %.3lf seconds\n",(end-start)/(double)CLOCKS_PER_SEC);
  printf("Cycle/second   : %.3lf million cps\n",total_cycle/1000000LL/((end-start)/(double)CLOCKS_PER_SEC));
  delete top;
  return 0;
}

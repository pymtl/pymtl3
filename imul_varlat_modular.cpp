#include <cstdio>
#include <ctime>

const int A_MUX_SEL_NBITS      = 1;
const int A_MUX_SEL_LSH        = 0;
const int A_MUX_SEL_LD         = 1;
const int A_MUX_SEL_X          = 0;

const int B_MUX_SEL_NBITS      = 1;
const int B_MUX_SEL_RSH        = 0;
const int B_MUX_SEL_LD         = 1;
const int B_MUX_SEL_X          = 0;

const int RESULT_MUX_SEL_NBITS = 1;
const int RESULT_MUX_SEL_ADD   = 0;
const int RESULT_MUX_SEL_0     = 1;
const int RESULT_MUX_SEL_X     = 0;

const int ADD_MUX_SEL_NBITS    = 1;
const int ADD_MUX_SEL_ADD      = 0;
const int ADD_MUX_SEL_RESULT   = 1;
const int ADD_MUX_SEL_X        = 0;

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
    out = en?in_:out;
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


class CalcShamt
{
public:
  int in_;
  int out;
  void up_calc_shamt()
  {
    if      (!in_      ) out = 8;
    else if ( in_ & 1  ) out = 1;
    else if ( in_ & 2  ) out = 1;
    else if ( in_ & 4  ) out = 2;
    else if ( in_ & 8  ) out = 3;
    else if ( in_ & 16 ) out = 4;
    else if ( in_ & 32 ) out = 5;
    else if ( in_ & 64 ) out = 6;
    else if ( in_ & 128) out = 7;
  }
};

class IntMulCS
{
public:
  int a_mux_sel;
  int b_mux_sel;
  int res_mux_sel;
  int res_reg_en;
  int add_mux_sel;
  int b_lsb;
  int is_b_zero;
};

class IntMulVarLatDpath
{
public:
  unsigned long long req_msg;
  int resp_msg;
  IntMulCS cs;
  Mux<32, B_MUX_SEL_NBITS> b_mux;
  Reg<32> b_reg;
  CalcShamt calc_sh;
  ZeroComp<32> b_zcp;
  RShifter<32> b_rsh;
  Mux<32, A_MUX_SEL_NBITS> a_mux;
  Reg<32> a_reg;
  LShifter<32> a_lsh;
  Mux<32, RESULT_MUX_SEL_NBITS> res_mux;
  RegEn<32> res_reg;
  Adder<32> res_add;
  Mux<32, ADD_MUX_SEL_NBITS> add_mux;
};

class IntMulVarLatCtrl
{
public:
  static const int STATE_IDLE = 0;
  static const int STATE_CALC = 1;
  static const int STATE_DONE = 2;
  int req_val;
  int req_rdy;
  int resp_val;
  int resp_rdy;
  IntMulCS cs;
  Reg<2> state;
  void state_transitions()
  {
    int curr_state = state.out;

    if (curr_state == STATE_IDLE)
    {
      if (req_val && req_rdy)
      {
        state.in_ = STATE_CALC;
      }
    }
    else
    if (curr_state == STATE_CALC)
    {
      if (cs.is_b_zero)
      {
        state.in_ = STATE_DONE;
      }
    }
    else
    if (curr_state == STATE_DONE)
    {
      if (resp_val && resp_rdy)
      {
        state.in_ = STATE_IDLE;
      }
    }
  }
  void state_outputs()
  {
    int curr_state = state.out;

    req_rdy        = 0;
    resp_val       = 0;
    cs.a_mux_sel   = 0;
    cs.b_mux_sel   = 0;
    cs.add_mux_sel = 0;
    cs.res_mux_sel = 0;
    cs.res_reg_en  = 0;

    if (curr_state == STATE_IDLE)
    {
      req_rdy        = 1;
      resp_val       = 0;

      cs.a_mux_sel   = A_MUX_SEL_LD;
      cs.b_mux_sel   = B_MUX_SEL_LD;
      cs.res_mux_sel = RESULT_MUX_SEL_0;
      cs.res_reg_en  = 1;
      cs.add_mux_sel = ADD_MUX_SEL_X;
    }
    else
    if (curr_state == STATE_CALC)
    {
      req_rdy        = 0;
      resp_val       = 0;

      cs.a_mux_sel   = A_MUX_SEL_LSH;
      cs.b_mux_sel   = B_MUX_SEL_RSH;
      cs.res_mux_sel = RESULT_MUX_SEL_ADD;
      cs.res_reg_en  = 1;
      if (cs.b_lsb)
      {
        cs.add_mux_sel = ADD_MUX_SEL_ADD;
      }
      else
      {
        cs.add_mux_sel = ADD_MUX_SEL_RESULT;
      }
    }
    else
    if (curr_state == STATE_DONE)
    {
      req_rdy        = 0;
      resp_val       = 1;

      cs.a_mux_sel   = A_MUX_SEL_X;
      cs.b_mux_sel   = A_MUX_SEL_X;
      cs.res_mux_sel = A_MUX_SEL_X;
      cs.add_mux_sel = A_MUX_SEL_X;
      cs.res_reg_en  = 0;
    }
  }
};

class IntMulVarLat
{
public:
  ValRdyBundle<64> req;
  ValRdyBundle<32> resp;

  IntMulVarLatDpath dpath;
  IntMulVarLatCtrl  ctrl;
};

class TestHarness
{
public:
  StreamSource src;
  IntMulVarLat imul;
  StreamSink   sink;
  void top_imul_dpath_a_reg_out_FANOUT_2()
  {
    imul.dpath.a_lsh.in_ = imul.dpath.a_reg.out;
    imul.dpath.res_add.in0 = imul.dpath.a_reg.out;
  }
  void top_src_out_val_FANOUT_2()
  {
    imul.ctrl.req_val = src.out.val;
    imul.req.val = src.out.val;
  }
  void top_imul_dpath_b_reg_out_FANOUT_2()
  {
    imul.dpath.b_zcp.in_ = imul.dpath.b_reg.out;
    imul.dpath.b_rsh.in_ = imul.dpath.b_reg.out;
  }
  void top_imul_ctrl_cs_a_mux_sel_FANOUT_2()
  {
    imul.dpath.cs.a_mux_sel = imul.ctrl.cs.a_mux_sel;
    imul.dpath.a_mux.sel = imul.ctrl.cs.a_mux_sel;
  }
  void top_imul_ctrl_cs_b_mux_sel_FANOUT_2()
  {
    imul.dpath.cs.b_mux_sel = imul.ctrl.cs.b_mux_sel;
    imul.dpath.b_mux.sel = imul.ctrl.cs.b_mux_sel;
  }
  void top_imul_ctrl_cs_res_mux_sel_FANOUT_2()
  {
    imul.dpath.cs.res_mux_sel = imul.ctrl.cs.res_mux_sel;
    imul.dpath.res_mux.sel = imul.ctrl.cs.res_mux_sel;
  }
  void top_imul_ctrl_cs_res_reg_en_FANOUT_2()
  {
    imul.dpath.cs.res_reg_en = imul.ctrl.cs.res_reg_en;
    imul.dpath.res_reg.en = imul.ctrl.cs.res_reg_en;
  }
  void top_imul_ctrl_cs_add_mux_sel_FANOUT_2()
  {
    imul.dpath.cs.add_mux_sel = imul.ctrl.cs.add_mux_sel;
    imul.dpath.add_mux.sel = imul.ctrl.cs.add_mux_sel;
  }
  void top_imul_dpath_b_reg_out_0_1__FANOUT_2()
  {
    imul.ctrl.cs.b_lsb = imul.dpath.b_reg.out & 1;
    imul.dpath.cs.b_lsb = imul.dpath.b_reg.out & 1;
  }
  void top_imul_dpath_b_zcp_out_FANOUT_2()
  {
    imul.ctrl.cs.is_b_zero = imul.dpath.b_zcp.out;
    imul.dpath.cs.is_b_zero = imul.dpath.b_zcp.out;
  }
  void top_imul_dpath_add_mux_out_FANOUT_1()
  {
    imul.dpath.res_mux.in_[0] = imul.dpath.add_mux.out;
  }
  void top_imul_dpath_res_mux_out_FANOUT_1()
  {
    imul.dpath.res_reg.in_ = imul.dpath.res_mux.out;
  }
  void top_imul_dpath_b_mux_out_FANOUT_1()
  {
    imul.dpath.b_reg.in_ = imul.dpath.b_mux.out;
  }
  void top_src_out_msg_FANOUT_2()
  {
    imul.dpath.req_msg = src.out.msg;
    imul.req.msg = src.out.msg;
  }
  void top_imul_dpath_b_reg_out_0_8__FANOUT_1()
  {
    imul.dpath.calc_sh.in_ = imul.dpath.b_reg.out & 255;
  }
  void top_imul_ctrl_resp_val_FANOUT_2()
  {
    sink.in_.val = imul.ctrl.resp_val;
    imul.resp.val = imul.ctrl.resp_val;
  }
  void top_imul_ctrl_req_rdy_FANOUT_2()
  {
    src.out.rdy = imul.ctrl.req_rdy;
    imul.req.rdy = imul.ctrl.req_rdy;
  }
  void top_imul_dpath_res_add_out_FANOUT_1()
  {
    imul.dpath.add_mux.in_[0] = imul.dpath.res_add.out;
  }
  void top_imul_dpath_b_rsh_out_FANOUT_1()
  {
    imul.dpath.b_mux.in_[0] = imul.dpath.b_rsh.out;
  }
  void top_imul_dpath_res_reg_out_FANOUT_5()
  {
    sink.in_.msg = imul.dpath.res_reg.out;
    imul.dpath.resp_msg = imul.dpath.res_reg.out;
    imul.dpath.res_add.in1 = imul.dpath.res_reg.out;
    imul.dpath.add_mux.in_[1] = imul.dpath.res_reg.out;
    imul.resp.msg = imul.dpath.res_reg.out;
  }
  void top_imul_dpath_a_lsh_out_FANOUT_1()
  {
    imul.dpath.a_mux.in_[0] = imul.dpath.a_lsh.out;
  }
  void top_sink_in__rdy_FANOUT_2()
  {
    imul.ctrl.resp_rdy = sink.in_.rdy;
    imul.resp.rdy = sink.in_.rdy;
  }
  void top_imul_dpath_calc_sh_out_FANOUT_2()
  {
    imul.dpath.b_rsh.shamt = imul.dpath.calc_sh.out;
    imul.dpath.a_lsh.shamt = imul.dpath.calc_sh.out;
  }
  void top_imul_dpath_a_mux_out_FANOUT_1()
  {
    imul.dpath.a_reg.in_ = imul.dpath.a_mux.out;
  }
  void top_imul_dpath_req_msg_0_32__FANOUT_1()
  {
    imul.dpath.a_mux.in_[1] = imul.dpath.req_msg >> 32;
  }
  void top_imul_dpath_req_msg_32_64__FANOUT_1()
  {
    imul.dpath.b_mux.in_[1] = imul.dpath.req_msg & 4294967295;
  }
  void tick_schedule()
  {
    imul.dpath.res_reg.up_regen();
    imul.dpath.a_reg.up_reg();
    imul.dpath.b_reg.up_reg();
    sink.up_sink();
    imul.ctrl.state.up_reg();
    src.up_src();
    top_imul_dpath_res_reg_out_FANOUT_5();
    top_imul_dpath_a_reg_out_FANOUT_2();
    top_imul_dpath_b_reg_out_0_1__FANOUT_2();
    top_imul_dpath_b_reg_out_FANOUT_2();
    top_imul_dpath_b_reg_out_0_8__FANOUT_1();
    top_sink_in__rdy_FANOUT_2();
    top_src_out_msg_FANOUT_2();
    top_src_out_val_FANOUT_2();
    imul.dpath.res_add.up_adder();
    imul.ctrl.state_outputs();
    imul.dpath.b_zcp.up_zerocomp();
    imul.dpath.calc_sh.up_calc_shamt();
    top_imul_dpath_req_msg_0_32__FANOUT_1();
    top_imul_dpath_req_msg_32_64__FANOUT_1();
    top_imul_dpath_res_add_out_FANOUT_1();
    top_imul_ctrl_cs_a_mux_sel_FANOUT_2();
    top_imul_ctrl_cs_b_mux_sel_FANOUT_2();
    top_imul_ctrl_cs_res_mux_sel_FANOUT_2();
    top_imul_ctrl_cs_add_mux_sel_FANOUT_2();
    top_imul_ctrl_req_rdy_FANOUT_2();
    top_imul_ctrl_cs_res_reg_en_FANOUT_2();
    top_imul_ctrl_resp_val_FANOUT_2();
    top_imul_dpath_b_zcp_out_FANOUT_2();
    top_imul_dpath_calc_sh_out_FANOUT_2();
    imul.dpath.add_mux.up_mux();
    imul.ctrl.state_transitions();
    imul.dpath.b_rsh.up_rshifter();
    imul.dpath.a_lsh.up_lshifter();
    top_imul_dpath_add_mux_out_FANOUT_1();
    top_imul_dpath_b_rsh_out_FANOUT_1();
    top_imul_dpath_a_lsh_out_FANOUT_1();
    imul.dpath.res_mux.up_mux();
    imul.dpath.b_mux.up_mux();
    imul.dpath.a_mux.up_mux();
    top_imul_dpath_res_mux_out_FANOUT_1();
    top_imul_dpath_b_mux_out_FANOUT_1();
    top_imul_dpath_a_mux_out_FANOUT_1();
  }
};

int main()
{
  TestHarness *__restrict__ top = new TestHarness();
  printf("%d %d\n",sizeof(TestHarness),sizeof(IntMulVarLat));
  unsigned long long total_cycle = 200000000;
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


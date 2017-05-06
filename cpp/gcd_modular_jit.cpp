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

template<int M>
class ValRdyBundle
{
public:
  int val;
  int rdy;
  int msg[M];
};

class StreamSource
{
public:
  ValRdyBundle<2> out;
  unsigned long long ts;
  StreamSource(): ts(0) {}
  void up_src()
  {
    out.msg[0] = ts+95827*(ts&1);
    out.msg[1] = ts+(19182)*(ts&1);
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

class GcdUnitCS
{
public:
  int a_mux_sel;
  int a_reg_en;
  int b_mux_sel;
  int b_reg_en;
  int is_b_zero; 
  int is_a_lt_b;
};

class GcdUnitDpath
{
public:
  int req_msg_a;
  int req_msg_b;
  int resp_msg;
  int sub_out;
  GcdUnitCS cs;
  RegEn<32> a_reg;
  RegEn<32> b_reg;
  Mux<32, 2> a_mux;
  Mux<32, 1> b_mux;
  ZeroComp<32> b_zcp;
  LTComp<32> b_ltc;
  Subtractor<32> b_sub;
};

int STATE_IDLE=0;
int STATE_CALC=1;
int STATE_DONE=2;

class GcdUnitCtrl
{
public:
  int req_val;
  int req_rdy;
  int resp_val;
  int resp_rdy;
  Reg<32> state;
  GcdUnitCS cs;

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
    else if (curr_state == STATE_CALC)
    {
      if (!cs.is_a_lt_b && cs.is_b_zero)
      {
        state.in_ = STATE_DONE;
      }
    }
    else if (curr_state == STATE_DONE)
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
    req_rdy  = 0;
    resp_val = 0;
    cs.a_mux_sel = 0;
    cs.a_reg_en  = 0;
    cs.b_mux_sel = 0;
    cs.b_reg_en  = 0;

    //  In IDLE state we simply wait for inputs to arrive and latch them

    if (curr_state == STATE_IDLE)
    {
      req_rdy  = 1;
      resp_val = 0;

      cs.a_mux_sel = A_MUX_SEL_IN;
      cs.b_mux_sel = B_MUX_SEL_IN;
      cs.a_reg_en  = 1;
      cs.b_reg_en  = 1;

      // In CALC state we iteratively swap/sub to calculate GCD
    }
    else if (curr_state == STATE_CALC)
    {
      req_rdy   = 0;
      resp_val  = 0;
      if (cs.is_a_lt_b)
      {
        cs.a_mux_sel = A_MUX_SEL_B;
      }
      else
      {
        cs.a_mux_sel = A_MUX_SEL_SUB;
      }
      cs.a_reg_en  = 1;
      cs.b_mux_sel = B_MUX_SEL_A;
      cs.b_reg_en  = cs.is_a_lt_b;
    }
      // In DONE state we simply wait for output transaction to occur

    else if (curr_state == STATE_DONE)
    {
      req_rdy   = 0;
      resp_val  = 1;
      cs.a_mux_sel = A_MUX_SEL_X;
      cs.b_mux_sel = B_MUX_SEL_X;
      cs.a_reg_en  = 0;
      cs.b_reg_en  = 0;
    }
  }
};

class GcdUnit
{
public:
  GcdUnitDpath dpath;
  GcdUnitCtrl  ctrl;

  ValRdyBundle<2> req;
  ValRdyBundle<1> resp;
};

class TestHarness
{
public:
  StreamSource src;
  GcdUnit      gcd;
  StreamSink   sink;
  
  void top_src_out_msg_0__FANOUT_3()
  {
    gcd.req.msg[0] = src.out.msg[0];
    gcd.dpath.req_msg_a = src.out.msg[0];
    gcd.dpath.a_mux.in_[0] = src.out.msg[0];
  }

  void top_src_out_msg_1__FANOUT_3()
  {
    gcd.req.msg[1] = src.out.msg[1];
    gcd.dpath.req_msg_b = src.out.msg[1];
    gcd.dpath.b_mux.in_[1] = src.out.msg[1];
  }

  void top_src_out_val_FANOUT_2()
  {
    gcd.req.val = src.out.val;
    gcd.ctrl.req_val = src.out.val;
  }

  void top_gcd_ctrl_req_rdy_FANOUT_2()
  {
    src.out.rdy = gcd.ctrl.req_rdy;
    gcd.req.rdy = gcd.ctrl.req_rdy;
  }

  void top_gcd_dpath_b_sub_out_FANOUT_5()
  {
    sink.in_.msg[0] = gcd.dpath.b_sub.out;
    gcd.dpath.resp_msg = gcd.dpath.b_sub.out;
    gcd.dpath.sub_out = gcd.dpath.b_sub.out;
    gcd.dpath.a_mux.in_[1] = gcd.dpath.b_sub.out;
    gcd.resp.msg[0] = gcd.dpath.b_sub.out;
  }

  void top_gcd_ctrl_resp_val_FANOUT_2()
  {
    sink.in_.val = gcd.ctrl.resp_val;
    gcd.resp.val = gcd.ctrl.resp_val;
  }

  void top_sink_in__rdy_FANOUT_2()
  {
    gcd.resp.rdy = sink.in_.rdy;
    gcd.ctrl.resp_rdy = sink.in_.rdy;
  }

  void top_gcd_ctrl_cs_a_mux_sel_FANOUT_2()
  {
    gcd.dpath.cs.a_mux_sel = gcd.ctrl.cs.a_mux_sel;
    gcd.dpath.a_mux.sel = gcd.ctrl.cs.a_mux_sel;
  }

  void top_gcd_ctrl_cs_a_reg_en_FANOUT_2()
  {
    gcd.dpath.cs.a_reg_en = gcd.ctrl.cs.a_reg_en;
    gcd.dpath.a_reg.en = gcd.ctrl.cs.a_reg_en;
  }

  void top_gcd_ctrl_cs_b_mux_sel_FANOUT_2()
  {
    gcd.dpath.cs.b_mux_sel = gcd.ctrl.cs.b_mux_sel;
    gcd.dpath.b_mux.sel = gcd.ctrl.cs.b_mux_sel;
  }

  void top_gcd_ctrl_cs_b_reg_en_FANOUT_2()
  {
    gcd.dpath.cs.b_reg_en = gcd.ctrl.cs.b_reg_en;
    gcd.dpath.b_reg.en = gcd.ctrl.cs.b_reg_en;
  }

  void top_gcd_dpath_b_zcp_out_FANOUT_2()
  {
    gcd.ctrl.cs.is_b_zero = gcd.dpath.b_zcp.out;
    gcd.dpath.cs.is_b_zero = gcd.dpath.b_zcp.out;
  }

  void top_gcd_dpath_b_ltc_out_FANOUT_2()
  {
    gcd.ctrl.cs.is_a_lt_b = gcd.dpath.b_ltc.out;
    gcd.dpath.cs.is_a_lt_b = gcd.dpath.b_ltc.out;
  }

  void top_gcd_dpath_a_mux_out_FANOUT_1()
  {
    gcd.dpath.a_reg.in_ = gcd.dpath.a_mux.out;
  }

  void top_gcd_dpath_a_reg_out_FANOUT_3()
  {
    gcd.dpath.b_mux.in_[0] = gcd.dpath.a_reg.out;
    gcd.dpath.b_ltc.in0 = gcd.dpath.a_reg.out;
    gcd.dpath.b_sub.in0 = gcd.dpath.a_reg.out;
  }

  void top_gcd_dpath_b_mux_out_FANOUT_1()
  {
    gcd.dpath.b_reg.in_ = gcd.dpath.b_mux.out;
  }

  void top_gcd_dpath_b_reg_out_FANOUT_4()
  {
    gcd.dpath.a_mux.in_[2] = gcd.dpath.b_reg.out;
    gcd.dpath.b_zcp.in_ = gcd.dpath.b_reg.out;
    gcd.dpath.b_ltc.in1 = gcd.dpath.b_reg.out;
    gcd.dpath.b_sub.in1 = gcd.dpath.b_reg.out;
  }
  void tick_schedule()
  {
    src.up_src();
    gcd.dpath.a_reg.up_regen();
    gcd.dpath.b_reg.up_regen();
    gcd.ctrl.state.up_reg();
    sink.up_sink();
    top_src_out_msg_0__FANOUT_3();
    top_src_out_msg_1__FANOUT_3();
    top_src_out_val_FANOUT_2();
    top_gcd_dpath_a_reg_out_FANOUT_3();
    top_gcd_dpath_b_reg_out_FANOUT_4();
    top_sink_in__rdy_FANOUT_2();
    gcd.dpath.b_zcp.up_zerocomp();
    gcd.dpath.b_ltc.up_ltcomp();
    gcd.dpath.b_sub.up_subtractor();
    top_gcd_dpath_b_zcp_out_FANOUT_2();
    top_gcd_dpath_b_ltc_out_FANOUT_2();
    top_gcd_dpath_b_sub_out_FANOUT_5();
    gcd.ctrl.state_outputs();
    gcd.ctrl.state_transitions();
    top_gcd_ctrl_req_rdy_FANOUT_2();
    top_gcd_ctrl_resp_val_FANOUT_2();
    top_gcd_ctrl_cs_a_mux_sel_FANOUT_2();
    top_gcd_ctrl_cs_a_reg_en_FANOUT_2();
    top_gcd_ctrl_cs_b_mux_sel_FANOUT_2();
    top_gcd_ctrl_cs_b_reg_en_FANOUT_2();
    gcd.dpath.a_mux.up_mux();
    gcd.dpath.b_mux.up_mux();
    top_gcd_dpath_a_mux_out_FANOUT_1();
    top_gcd_dpath_b_mux_out_FANOUT_1();
  }
};

int main()
{
  TestHarness *__restrict__ top = new TestHarness();
  printf("%d\n",sizeof(TestHarness));
  unsigned long long total_cycle = 1000000000;
  time_t start = clock();
  for (unsigned long long cycle=0; cycle<total_cycle; ++cycle)
  {
    top->tick_schedule();

  }
  time_t end = clock();
  printf("req val:%d rdy:%d a:%6d b:%6d ", top->gcd.req.val, top->gcd.req.rdy, top->gcd.req.msg[0], top->gcd.req.msg[1]);
  printf("[en:%1d|%6d > %6d] ", top->gcd.dpath.a_reg.en, top->gcd.dpath.a_reg.in_, top->gcd.dpath.a_reg.out);
  printf("[en:%1d|%6d > %6d] ", top->gcd.dpath.b_reg.en, top->gcd.dpath.b_reg.in_, top->gcd.dpath.b_reg.out);
  printf("resp val:%d rdy:%d gcd:%6d", top->gcd.resp.val, top->gcd.resp.rdy, top->gcd.resp.msg[0]);
  puts("");

  printf("Total cycles   : %lld million cycles\n", total_cycle/1000000LL);
  printf("Execution time : %.3lf seconds\n",(end-start)/(double)CLOCKS_PER_SEC);
  printf("Cycle/second   : %.3lf million cps\n",total_cycle/1000000LL/((end-start)/(double)CLOCKS_PER_SEC));
  delete top;
  return 0;
}

#include "stdio.h"

// GCD Unit

int A_MUX_SEL_IN  = 0;
int A_MUX_SEL_SUB = 1;
int A_MUX_SEL_B   = 2;
int A_MUX_SEL_X   = 0;
int B_MUX_SEL_A   = 0;
int B_MUX_SEL_IN  = 1;
int B_MUX_SEL_X   = 0;

int top_req_rdy = 0, top_req_val = 0, top_req_msg_a = 0, top_req_msg_b = 0;
int top_resp_rdy = 0, top_resp_val = 0, top_resp_msg = 0;

// GCD Dpath

int top_dpath_req_msg_a = 0, top_dpath_req_msg_b = 0, top_dpath_resp_msg = 0;
int top_dpath_a_mux_sel = 0, top_dpath_a_reg_en = 0;
int top_dpath_b_mux_sel = 0, top_dpath_b_reg_en = 0;
int top_dpath_sub_out = 0;
int top_dpath_a_reg_in_ = 0, top_dpath_a_reg_out = 0;
int top_dpath_b_reg_in_ = 0, top_dpath_b_reg_out = 0;

int top_dpath_a_mux_in_[3], top_dpath_a_mux_out = 0;
int top_dpath_b_mux_in_[2], top_dpath_b_mux_out = 0;
int top_dpath_is_b_zero = 0, top_dpath_is_a_lt_b = 0;

// GCD Ctrl
int top_ctrl_req_val = 0, top_ctrl_req_rdy = 0;
int top_ctrl_resp_val = 0, top_ctrl_resp_rdy = 0;
int top_ctrl_state_in_ = 0, top_ctrl_state_out = 0;

int top_ctrl_STATE_IDLE = 0;
int top_ctrl_STATE_CALC = 1;
int top_ctrl_STATE_DONE = 2;

int top_ctrl_is_b_zero = 0, top_ctrl_is_a_lt_b = 0;
int top_ctrl_a_mux_sel = 0, top_ctrl_a_reg_en  = 0;
int top_ctrl_b_mux_sel = 0, top_ctrl_b_reg_en  = 0;

void tick_batch_schedule()
{
  // Batch 1
  // up_reg_en
  if (top_dpath_a_reg_en)
  {
    top_dpath_a_reg_out = top_dpath_a_reg_in_;
  }

  // up_reg_en
  if (top_dpath_b_reg_en)
  {
    top_dpath_b_reg_out = top_dpath_b_reg_in_;
  }

  // up_reg
  top_ctrl_state_out = top_ctrl_state_in_;

  // Batch 2
  // up_subtract
  top_dpath_sub_out = top_dpath_resp_msg = top_dpath_a_reg_out - top_dpath_b_reg_out;

  // up_comparisons
  top_dpath_is_b_zero = ( top_dpath_b_reg_out == 0 );
  top_dpath_is_a_lt_b = ( top_dpath_a_reg_out < top_dpath_b_reg_out );

  // Batch 3
  // up_connect_ctrl
  top_ctrl_is_b_zero  = top_dpath_is_b_zero;
  top_ctrl_is_a_lt_b  = top_dpath_is_a_lt_b;

  // Batch 4
  // state_outputs
  
  int curr_state_0 = top_ctrl_state_out;

  top_ctrl_req_rdy   = top_ctrl_resp_val = 0;
  top_ctrl_a_mux_sel = top_ctrl_a_reg_en = 0;
  top_ctrl_b_mux_sel = top_ctrl_b_reg_en  = 0;

  if (curr_state_0 == top_ctrl_STATE_IDLE)
  {
    top_ctrl_req_rdy   = 1;
    top_ctrl_resp_val  = 0;

    top_ctrl_a_mux_sel = A_MUX_SEL_IN;
    top_ctrl_b_mux_sel = B_MUX_SEL_IN;
    top_ctrl_a_reg_en  = top_ctrl_b_reg_en  = 1;
  }
  else if (curr_state_0 == top_ctrl_STATE_CALC)
  {
    top_ctrl_req_rdy   = top_ctrl_resp_val  = 0;
    if (top_ctrl_is_a_lt_b)
    {
      top_ctrl_a_mux_sel = A_MUX_SEL_B;
    }
    else
    {
      top_ctrl_a_mux_sel = A_MUX_SEL_SUB;
    }
    top_ctrl_a_reg_en  = 1;
    top_ctrl_b_mux_sel = B_MUX_SEL_A;
    top_ctrl_b_reg_en  = top_ctrl_is_a_lt_b;
  }
  else if (curr_state_0 == top_ctrl_STATE_DONE)
  {
    top_ctrl_req_rdy   = 0;
    top_ctrl_resp_val  = 1;
    top_ctrl_a_mux_sel = top_ctrl_b_mux_sel = A_MUX_SEL_X;
    top_ctrl_a_reg_en  = top_ctrl_b_reg_en = 0;
  }

  // Batch 5
  // up_connect_valrdy
  top_ctrl_req_val    = top_req_val;
  top_req_rdy         = top_ctrl_req_rdy;
  top_dpath_req_msg_a = top_req_msg_a;
  top_dpath_req_msg_b = top_req_msg_b;

  top_resp_val        = top_ctrl_resp_val;
  top_ctrl_resp_rdy   = top_resp_rdy;
  top_resp_msg        = top_dpath_resp_msg;

  // up_connect_dpath
  top_dpath_a_mux_sel = top_ctrl_a_mux_sel;
  top_dpath_b_mux_sel = top_ctrl_b_mux_sel;

  top_dpath_a_reg_en  = top_ctrl_a_reg_en;
  top_dpath_b_reg_en  = top_ctrl_b_reg_en;

  // Batch 6
  // state_transitions
  int curr_state_1 = top_ctrl_state_out;

  if (curr_state_1 == top_ctrl_STATE_IDLE)
  {
    if (top_ctrl_req_val && top_ctrl_req_rdy)
    {
      top_ctrl_state_in_ = top_ctrl_STATE_CALC;
    }
  }
  else if (curr_state_1 == top_ctrl_STATE_CALC)
  {
    if (!top_ctrl_is_a_lt_b && top_ctrl_is_b_zero)
    {
      top_ctrl_state_in_ = top_ctrl_STATE_DONE;
    }
  }
  else if (curr_state_1 == top_ctrl_STATE_DONE)
  {
    if (top_ctrl_resp_val && top_ctrl_resp_rdy)
    {
      top_ctrl_state_in_ = top_ctrl_STATE_IDLE;
    }
  }
  // up_connect_to_a_mux
  top_dpath_a_mux_in_[A_MUX_SEL_IN]  = top_dpath_req_msg_a;
  top_dpath_a_mux_in_[A_MUX_SEL_SUB] = top_dpath_sub_out;
  top_dpath_a_mux_in_[A_MUX_SEL_B]   = top_dpath_b_reg_out;
  top_dpath_a_mux_sel = top_dpath_a_mux_sel;

  // up_connect_to_b_mux
  top_dpath_b_mux_in_[B_MUX_SEL_A]  = top_dpath_a_reg_out;
  top_dpath_b_mux_in_[B_MUX_SEL_IN] = top_dpath_req_msg_b;
  top_dpath_b_mux_sel = top_dpath_b_mux_sel;

  // up_regs_enable
  top_dpath_a_reg_en = top_dpath_a_reg_en;
  top_dpath_b_reg_en = top_dpath_b_reg_en;

  // Batch 7
  // up_mux
  top_dpath_a_mux_out = top_dpath_a_mux_in_[ top_dpath_a_mux_sel ];

  // up_mux
  top_dpath_b_mux_out = top_dpath_b_mux_in_[ top_dpath_b_mux_sel ];

  // Batch 8
  // up_connect_from_a_mux
  top_dpath_a_reg_in_ = top_dpath_a_mux_out;

  // up_connect_from_b_mux
  top_dpath_b_reg_in_ = top_dpath_b_mux_out;
}

int main()
{
  int cycle;
  top_req_val = 1;
  top_resp_rdy = 1;
  for (cycle=0; cycle<100000000; ++cycle)
  {
    top_req_msg_a = cycle+95827*(cycle&1);
    top_req_msg_b = cycle+(19182)*(cycle&1);

    tick_batch_schedule();

    // printf("req val:%d rdy:%d a:%6d b:%6d ", top_req_val, top_req_rdy, top_req_msg_a, top_req_msg_b);
    // printf("[en:%1d|%6d > %6d] ", top_dpath_a_reg_en, top_dpath_a_reg_in_, top_dpath_a_reg_out);
    // printf("[en:%1d|%6d > %6d] ", top_dpath_b_reg_en, top_dpath_b_reg_in_, top_dpath_b_reg_out);
    // printf("resp val:%d rdy:%d gcd:%6d", top_resp_val, top_resp_rdy, top_resp_msg);
    // puts("");
  }
  return 0;
}

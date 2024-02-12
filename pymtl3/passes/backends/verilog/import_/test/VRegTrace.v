`include "trace.v"

module test_VRegTrace(
  input  logic          clk,
  input  logic          reset,
  output logic [32-1:0] q,
  input  logic [32-1:0] d
);
  always_ff @(posedge clk) begin
    q <= d;
  end

  logic [`VC_TRACE_NBITS-1:0] str;
  logic [512*8-1:0] q_str;
  `VC_TRACE_BEGIN
  begin
    // PP: we should not use $ system tasks because
    // they seem to be generating segfaults at end of pytest??
    /* $display("q = %d\n", q); */
    $sformat(q_str, "%d", q);
    vc_trace.append_str( trace_str, "q = " );
    vc_trace.append_str( trace_str, q_str );
  end
  `VC_TRACE_END

endmodule

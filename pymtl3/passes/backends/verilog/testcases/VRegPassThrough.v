// We do not explicitly include VReg here. Instead we assume the include
// directory or the v_lib is correctly passed to Verilator.

module VRegPassThrough(
  input  logic          clk,
  input  logic          reset,
  output logic [32-1:0] q,
  input  logic [32-1:0] d
);

  VReg inner_reg(
    .clk(clk),
    .reset(reset),
    .q(q),
    .d(d)
  );

endmodule

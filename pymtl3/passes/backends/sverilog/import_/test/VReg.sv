module VReg(
  input  logic          clk,
  input  logic          reset,
  output logic [32-1:0] q,
  input  logic [32-1:0] d
);
  always_ff @(posedge clk) begin
    q <= d;
  end

endmodule

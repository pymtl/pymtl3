module VReg(
  input           clk,
  input           reset,
  output [32-1:0] q,
  input  [32-1:0] d
);
  logic q;
  always_ff @(posedge clk) begin
    q <= d;
  end

endmodule

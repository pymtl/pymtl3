module Adder
#(
  parameter nbits = 32
)
(
  input  logic          clk,
  input  logic          reset,
  input  logic [nbits-1:0] a,
  input  logic [nbits-1:0] b,
  output logic [nbits-1:0] sum
);

always_comb begin
  sum = a + b;
  /* if (a == 1) begin */
  /*   sum = 0; */
  /* end */
end

endmodule

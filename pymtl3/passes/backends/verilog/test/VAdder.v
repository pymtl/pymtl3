module VAdder(
  input  logic          clk,
  input  logic          reset,
  input  logic [32-1:0] a,
  input  logic [32-1:0] b,
  output logic [32-1:0] sum
);

  assign sum = a + b + 1;

endmodule

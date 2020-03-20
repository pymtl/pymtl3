module test_VUninit(
  input  logic          clk,
  input  logic          reset,
  output logic [32-1:0] q,
  input  logic [32-1:0] d
);

  always_comb begin
    if (d == 32'd42)
      q = 32'd42;
  end

endmodule

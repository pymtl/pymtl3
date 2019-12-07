module VAdder #( parameter nbits = 32 )
(
  input clk,
  input reset,
  input [nbits-1:0] in0,
  input [nbits-1:0] in1,
  input cin,
  output [nbits-1:0] out,
  output cout
);

  logic [nbits:0] temp;

  always_comb begin
    temp = ( in0 + in1 ) + 32'(cin);
  end
  
  assign cout = temp[nbits];
  assign out = temp[nbits-1:0];

endmodule

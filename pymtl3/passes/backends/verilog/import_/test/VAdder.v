module VAdder #( parameter nbits = 32 )
(
  input  logic clk,
  input  logic reset,
  input  logic [nbits-1:0] in0,
  input  logic [nbits-1:0] in1,
  input  logic cin,
  output logic [nbits-1:0] out,
  output logic cout
);

  logic [nbits:0] temp;

  always_comb begin
    temp = ( in0 + in1 ) + 32'(cin);
  end
  
  assign cout = temp[nbits];
  assign out = temp[nbits-1:0];

endmodule

module test_VAdder #( parameter nbits = 32 )
(
  input  logic clk,
  input  logic reset,
  input  logic [nbits-1:0] in0,
  input  logic [nbits-1:0] in1,
  input  logic cin,
  output logic [nbits-1:0] out,
  output logic cout
);

  logic [nbits:0] temp;

  always_comb begin
    temp = ( in0 + in1 ) + 32'(cin);
  end
  
  assign cout = temp[nbits];
  assign out = temp[nbits-1:0];

endmodule

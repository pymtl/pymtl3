module child (
  input [9:0] in_,
  output logic [9:0] out
);
  assign out = in_ + 1;
endmodule

module test_VIncr (
  input [9:0] in_,
  output logic [9:0] out,
  output logic vcd_en
);
  logic [9:0] child_out;

  child c (
    .in_(in_),
    .out(child_out)
  );

  assign out = child_out;

  assign vcd_en = (in_[2:0] >= 4);
endmodule

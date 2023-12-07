module test_VAssert (
  input [9:0] in_,
  output logic [9:0] out
);

  assign out = in_;

  always_comb begin
    assert (in_ != 4);
  end

endmodule

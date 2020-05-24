module test_VPassThrough
#(
  parameter num_ports = 2,
  parameter bitwidth  = 32
)
(
  input  logic [bitwidth-1:0] in_ [0:num_ports-1],
  output logic [bitwidth-1:0] out [0:num_ports-1]
);

  genvar i;

  generate
    for(i = 0; i < num_ports; i= i+1) begin
      assign out[i] = in_[i];
    end
  endgenerate

endmodule

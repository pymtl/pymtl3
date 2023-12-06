module RegIncr
#(
  parameter nbits = 32
)
(
  input  logic          clk,
  input  logic          reset,
  input  logic [nbits-1:0] in_,
  output logic [nbits-1:0] out
);

always_ff @(posedge clk) begin
  out <= in_ + 1;
end

endmodule

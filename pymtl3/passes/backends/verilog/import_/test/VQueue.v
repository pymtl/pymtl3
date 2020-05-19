/*========================================================================
  NormalQueue
 *======================================================================
  System verilog implementation of a register based normal queue.

  Author : Yanghui Ou
    Date : June 9, 2019
*/

module test_VQueue
#(
  parameter data_width  = 32,
  parameter num_entries = 2,
  parameter count_width = $clog2( num_entries+1 )
)
(
  input  logic                   clk,
  input  logic                   reset,
  output logic [count_width-1:0] count,
  input  logic                   deq_en,
  output logic                   deq_rdy,
  output logic [data_width -1:0] deq_msg,
  input  logic                   enq_en,
  output logic                   enq_rdy,
  input  logic [data_width -1:0] enq_msg
);

  localparam                   addr_width = num_entries == 1 ? 1 : $clog2( num_entries );
  localparam [count_width-1:0] max_size   = num_entries[count_width-1:0];
  localparam [addr_width -1:0] last_idx   = num_entries[addr_width -1:0] - 'd1;

  // Wire declaration
  logic [addr_width-1:0] deq_ptr;
  logic [addr_width-1:0] enq_ptr;
  logic [data_width-1:0] data_reg [0:num_entries-1];

  // Sequential logic
  always_ff @(posedge clk) begin
    if (reset) begin
      deq_ptr <= 'd0;
      deq_ptr <= 'd0;
      count   <= 'd0;
    end
    else begin
      deq_ptr <= ~deq_en ? deq_ptr : deq_ptr == last_idx? 'd0 : deq_ptr + 'd1;
      enq_ptr <= ~enq_en ? enq_ptr : enq_ptr == last_idx? 'd0 : enq_ptr + 'd1;
      count <= ( enq_en & ~deq_en ) ? count + 'd1 :
               ( deq_en & ~enq_en ) ? count - 'd1 : count;
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      for (int i = 0; i < num_entries; i += 1)
        data_reg[i] <= 'd0;
    end
    else if (enq_en) begin
      data_reg[enq_ptr] <= enq_msg;
    end
  end

  assign enq_rdy = count < max_size;
  assign deq_rdy = count > 'd0;
  assign deq_msg = data_reg[deq_ptr];

endmodule

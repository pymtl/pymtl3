template = \
'''
// VTB_CYCLE_TIME   : clock period in ns
// VTB_INPUT_DELAY  : how long after rising clk edge should we write inputs
// VTB_OUTPUT_DELAY : how long before rising clk edge should we check outputs
// VTB_OUTPUT_ASSERT_DELAY = VTB_CYCLE_TIME - VTB_OUTPUT_DELAY
//  setting VTB_OUTPUT_ASSERT_DELAY takes priority over VTB_OUTPUT_DELAY

`define CYCLE_TIME 10
`define VTB_INPUT_DELAY 1
`define VTB_OUTPUT_DELAY 1

`ifndef VTB_OUTPUT_ASSERT_DELAY
`define VTB_OUTPUT_ASSERT_DELAY (`CYCLE_TIME-`VTB_OUTPUT_DELAY)
`endif

`define INTRA_CYCLE_TIME (`VTB_OUTPUT_ASSERT_DELAY-`VTB_INPUT_DELAY)

`timescale 1ns/1ns

`define T({args_strs}) \\
        t({args_strs},`__LINE__)

// Tick one extra cycle upon an error.
`define VTB_TEST_FAIL(lineno, out, ref, port_name) \\
    $display("- Timestamp      : %0d (default unit: ns)", $time); \\
    $display("- Cycle number   : %0d (variable: cycle_count)", cycle_count); \\
    $display("- line number    : line %0d in {cases_file_name}", lineno); \\
    $display("- port name      : %s", port_name); \\
    $display("- expected value : 0x%x", ref); \\
    $display("- actual value   : 0x%x", out); \\
    $display(""); \\
    #(`CYCLE_TIME-`INTRA_CYCLE_TIME); \\
    cycle_count += 1; \\
    #`CYCLE_TIME; \\
    cycle_count += 1; \\
    $fatal;

`define CHECK(lineno, out, ref, port_name) \\
  if ((|(out ^ out)) == 1'b0) ; \\
  else begin \\
    $display(""); \\
    $display("The test bench received a value containing X/Z's! Please note"); \\
    $display("that the VTB is pessmistic about X's and you should make sure"); \\
    $display("all output ports of your DUT does not produce X's after reset."); \\
    `VTB_TEST_FAIL(lineno, out, ref, port_name) \\
  end \\
  if (out != ref) begin \\
    $display(""); \\
    $display("The test bench received an incorrect value!"); \\
    `VTB_TEST_FAIL(lineno, out, ref, port_name) \\
  end

module Top;
  // convention
  logic clk;
  logic reset;
  integer cycle_count;

  {signal_decls};

  task t(
    {task_signal_decls},
    integer lineno
  );
  begin
    {task_assign_strs};
    #`INTRA_CYCLE_TIME;
    {task_check_strs};
    #(`CYCLE_TIME-`INTRA_CYCLE_TIME);
    cycle_count += 1;
  end
  endtask

  always #((`CYCLE_TIME*1.0)/2) clk = ~clk;

  // DUT name
  // By default we use the translated name of the Verilog component. But you can change
  // that by defining the VTB_TOP_MODULE_NAME macro through the simulator command line
  // options (e.g., for VCS you can do +define+VTB_TOP_MODULE_NAME=YourTopModuleName).
`ifdef VTB_TOP_MODULE_NAME
  `VTB_TOP_MODULE_NAME DUT
`else
  {dut_name} DUT
`endif
  (
    {dut_clk_decl},
    {dut_reset_decl},
    {dut_signal_decls}
  );

  initial begin
    assert(0 <= `VTB_INPUT_DELAY)
      else $fatal("\\n=====\\n\\nVTB_INPUT_DELAY should >= 0\\n\\n=====\\n");

    assert(`VTB_INPUT_DELAY < `VTB_OUTPUT_ASSERT_DELAY)
      else $fatal("\\n=====\\n\\nVTB_OUTPUT_ASSERT_DELAY should be larger than VTB_INPUT_DELAY\\n\\n=====\\n");

    assert(`VTB_OUTPUT_ASSERT_DELAY <= `CYCLE_TIME)
      else $fatal("\\n=====\\n\\nVTB_OUTPUT_ASSERT_DELAY should be smaller than or equal to CYCLE_TIME\\n\\n=====\\n");

    cycle_count = 0;
    clk   = 1'b0; // NEED TO DO THIS TO HAVE FALLING EDGE AT TIME 0
    reset = 1'b1; // TODO reset active low/high
    #((`CYCLE_TIME*1.0)/2);

    // Now we are talking
    #`VTB_INPUT_DELAY;
    #`CYCLE_TIME;
    cycle_count = 1;
    #`CYCLE_TIME;
    cycle_count = 2;
    // 2 cycles plus input delay
    reset = 1'b0;

    `include "{cases_file_name}"

    $display("");
    $display("  [ passed ]");
    $display("");

    // Tick one extra cycle for better waveform
    #`CYCLE_TIME;
    cycle_count += 1;
    $finish;
  end
endmodule
'''

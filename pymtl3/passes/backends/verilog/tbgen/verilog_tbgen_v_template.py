template = \
'''
// VT_INPUT_DELAY, VTB_OUTPUT_ASSERT_DELAY are timestamps relative to the rising edge.
`define VTB_INPUT_DELAY 1
`define VTB_OUTPUT_ASSERT_DELAY 3

// CYCLE_TIME and INTRA_CYCLE_TIME are duration of time.
`define CYCLE_TIME 4
`define INTRA_CYCLE_TIME `VTB_OUTPUT_ASSERT_DELAY-`VTB_INPUT_DELAY

`timescale 1ns/1ns

`define T({args_strs}) \\
        t({args_strs},`__LINE__)

// Tick two extra cycles upon an error.
`define CHECK(lineno, out, ref, port_name) \\
  if (out != ref) begin \\
    $display(""); \\
    $display("The test bench received an incorrect value!"); \\
    $display("- line %0d in {cases_file_name}", lineno); \\
    $display("- cycle number   : %0d", lineno+2); \\
    $display("- port name      : %s", port_name); \\
    $display("- expected value : 0x%x", ref); \\
    $display("- actual value   : 0x%x", out); \\
    $display(""); \\
    #`CYCLE_TIME; \\
    #`CYCLE_TIME; \\
    $fatal; \\
  end

module {harness_name};
  // convention
  logic clk;
  logic reset;

  {signal_decls};

  task t(
    {task_signal_decls},
    integer lineno
  );
  begin
    {task_assign_strs};
    #`INTRA_CYCLE_TIME;
    {task_check_strs};
    #(`CYCLE_TIME-INTRA_CYCLE_TIME);
  end
  endtask

  // use 25% clock cycle, so #1 for setup #2 for sim #1 for hold
  always #(`CYCLE_TIME/2) clk = ~clk;

  {dut_name} DUT
  (
    {dut_clk_decl},
    {dut_reset_decl},
    {dut_signal_decls}
  );

  initial begin
    assert(0 <= VTB_INPUT_DELAY);
    assert(VTB_INPUT_DELAY < VTB_OUTPUT_ASSERT_DELAY);
    assert(VTB_OUTPUT_ASSERT_DELAY <= CYCLE_TIME);

    clk   = 1'b1; // NEED TO DO THIS TO HAVE RISING EDGE AT TIME 0
    reset = 1'b0; // TODO reset active low/high

    #`VTB_INPUT_DELAY;
    reset = 1'b1;
    #`CYCLE_TIME;
    #`CYCLE_TIME;
    // 2 cycles plus input delay
    reset = 1'b0;

    `include "{cases_file_name}"

    $display("");
    $display("  [ passed ]");
    $display("");

    // Tick two extra cycles for better waveform
    #`CYCLE_TIME;
    #`CYCLE_TIME;
    $finish;
  end
endmodule
'''

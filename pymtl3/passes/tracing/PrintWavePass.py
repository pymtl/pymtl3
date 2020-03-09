"""
========================================================================
PrintWavePass.py
========================================================================
Print single bit signal in wave form and multi-bit signal by showing
least significant bits.

To use, call top.print_wave()

Inspired by PyRTL's state machine screenshot, which shows the change of signal
values along ticks of the clock.

Link: https://ucsbarchlab.github.io/PyRTL/

Author : Kaishuo Cheng, Shunning Jiang
Date   : Nov 9, 2019
"""

import py

from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError


class PrintWavePass( BasePass ):

  def __call__( self, top ):
    if hasattr( top, "config_tracing" ):
      top.config_tracing.check()

      if top.config_tracing.tracing in [ 'text_ascii', 'text_fancy' ]:
        if not hasattr( top._tracing, "text_sigs" ):
          raise PassOrderError( "text_sigs" )

        def gen_print_wave( top ):
          def print_wave():
            _help_print( top )
          return print_wave

        top.print_textwave = gen_print_wave(top)

def _process_binary( sig, base, max ):
  """
  Returns int value from a signal in 32b form. Used for testing.

  Example: input: 0b00000000000000000000000000000000 10
           output: 0
  """
  if sig[1] == "b":
    sig = sig[2:]
  if base == 10:
    temp_int = int(sig,2)
    if sig[0] == '1':
      return temp_int -2 **32     # taking 2's complement.
                                  # leading 1 indicates a negative number
    else:
      return temp_int
    #hex number
  else:
    temp_hex = hex(int(sig,2))[2:]
    l = len(temp_hex)
    if l > max:
      temp_hex = temp_hex[l-max:]

    if l < max:
      temp_hex = '0'*(max-l) + temp_hex
    return temp_hex

def _help_print( top ):
  #default is text_fancy
  char_length = top.config_tracing.chars_per_cycle

  assert char_length % 2 == 0
  tick = '\u258f'
  up, down = '\u2571', '\u2572'
  x, low, high = '\u2573', '\u005f', '\u203e'
  revstart, revstop = '\x1B[7m', '\x1B[0m'
  light_gray = '\033[47m'
  back='\033[0m'  #back to normal printing
  if top.config_tracing.tracing == 'text_ascii':
    up,down,x,low = '/','\\','|','_'
    tick ='|'

  all_signal_values = top._tracing.text_sigs
  #spaces before cycle number
  max_length = 5
  for sig in all_signal_values:
    #   Example: s.in(12b)
    # length of signal name + (b) + number of digits, like 12
    # to add(32b) in front, add this to maxlength:
    #len(str(len(all_signal_values[sig][0][0])))+3
    max_length = max( max_length, len(sig)-2 )

  print("")
  print(" "*(max_length+1),end = "")

  #-----------------------------------------------------------------------
  # handle clk and reset
  #-----------------------------------------------------------------------
  # handles clock tick symbol

  for i in range(0,len(all_signal_values["s.reset"])):
    # insert a space every 5 cycles
    print(f"{tick}{str(i).ljust(char_length-1)}",end="")
  print("")

  # Adding one blank line
  print("")

  # handle clock signal
  clk_cycle_str = up + (char_length-2)//2*str(high) + down + (char_length-2)//2*str(low)

  print("clk".rjust(max_length), clk_cycle_str * len(all_signal_values["s.reset"]))

  print("")

  #signals
  for sig in all_signal_values:
    bit_length = len(all_signal_values[sig][0])-2
    print((sig[2:]).rjust(max_length),end=" ")
    # one bit
    if bit_length==1:
      prev_sig = None
      for i, val in enumerate( all_signal_values[sig] ):
        # every 5 cycles add a space
        # if i%5 == 0:
          # print(" ",end = "")
        if val[2] == '1':
          current_sig = high
        else:
          current_sig = low
        # detecting if first cycle
        if prev_sig is not None:
          if prev_sig == low and current_sig == high:
            print(up+current_sig*(char_length-1),end = "")
          elif prev_sig == high and current_sig == low:
            print(down+current_sig*(char_length-1),end = "")
          # prev and current signal agree
          else:
            print(current_sig*char_length,end = "")
        # first cycle
        else:
          print(current_sig*char_length,end = "")
        prev_sig = current_sig

      print("")
      #multiple bits
    else:
      next = 0
      val_list = all_signal_values[sig]
      for i in range(len(val_list)):
        # signals in this cycle is still the same as before
        if next > 0:
          next -= 1
          continue

        val = val_list[i]
        for j in range(i,len(val_list)):
          if val_list[j] != val:
            j = j-1
            break

        #first is reserved for X or " ". Rest is 5 char length.
        length = (char_length-1) + char_length*(j-i)
        next = j-i

        if length >= bit_length // (char_length-1):
          length = bit_length // (char_length-1)
          if bit_length % char_length != 0:
            length += 1
          plus = False
        else:
          #reverse a place for +
          length = length -1
          plus = True

        current = _process_binary(val,16,length)
        # print a +, with one less space for signal number
        if plus:
          if i==0:
            print(light_gray + " " +'\033[30m'+"+"+ current,end = "")
          else:
            print(light_gray + '\033[30m'+x + "+" +current,end = "")
        # no +, more spaces for signal number
        else:
          if i==0:
            print(light_gray + " " +'\033[30m'+ current,end = "")
          else:
            print(light_gray + '\033[30m'+x +current,end = "")
          print(" "*(char_length-1+char_length*(j-i)-length),end = "")
      print(back + "")
    print("")

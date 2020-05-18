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

from pymtl3.dsl import Const, MetadataKey
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class PrintTextWavePass( BasePass ):

  # PrintWavePass public pass data

  #: chars_per_cycle
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ""
  chars_per_cycle = MetadataKey(int)

  #: enable
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: False
  enable = MetadataKey(bool)

  textwave_func = MetadataKey()
  textwave_dict = MetadataKey()

  def __call__( self, top ):
    if top.has_metadata( self.enable ) and top.get_metadata( self.enable ):

      assert not top.has_metadata( self.textwave_func )
      assert not top.has_metadata( self.textwave_dict )

      func, sigs_dict = self._collect_sig_func( top )

      top.set_metadata( self.textwave_func, func )
      top.set_metadata( self.textwave_dict, sigs_dict )
      top.print_textwave = self._gen_print_wave( top, sigs_dict )

  def _process_binary( self, sig, base, max ):
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

  def _gen_print_wave( self, top, sigs_dict ):

    def print_wave():
      if top.has_metadata( self.chars_per_cycle ):
        char_length = top.get_metadata( self.chars_per_cycle )
      else:
        char_length = 6
      # Shunning: deprecate text_fancy
      # up, down = '\u2571', '\u2572'
      # x, low = '\u2573', '\u005f'

      assert char_length % 2 == 0
      tick = '|'
      up,down,x,low,high = '/','\\','|','_', '\u203e'
      revstart, revstop = '\x1B[7m', '\x1B[0m'
      light_gray = '\033[47m'
      back='\033[0m'  #back to normal printing

      all_signal_values = text_sigs
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

      for i in range(len(all_signal_values["s.reset"])):
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

            current = self._process_binary(val,16,length)
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
    return print_wave

  def _collect_sig_func( self, top ):

    # TODO use actual nets to reduce the amount of saved signals

    # Give all ' and " characters a preceding backslash for .format
    wav_srcs = []
    text_sigs = {}

    # Now we create per-cycle signal value collect functions
    signal_names = []
    for x in top._dsl.all_signals:
      if x.is_top_level_signal() and x.get_field_name() != "clk" and x.get_field_name() != "reset":
        signal_names.append( (x._dsl.level, repr(x)) )

    for _, x in [(0, 's.reset')] + sorted(signal_names):
      text_sigs[x] = []
      wav_srcs.append(f"text_sigs['{x}'].append( {x}.to_bits().bin() )")

    # TODO use integer index instead of dict, should be easy
    src =  """
def dump_wav():
  {}
""".format( "\n  ".join(wav_srcs) )
    s, l_dict = top, {}
    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)
    return l_dict['dump_wav'], text_sigs

"""
========================================================================
PrintWavePass.py
========================================================================
Print the most sigficant number of signals in wave form.
top object uses top._print_wave(top) to print.

Author : Kaishuo Cheng
Date   : Oct 4, 2019
"""

from __future__ import absolute_import, division, print_function
import time
from collections import defaultdict
from copy import deepcopy
import py
import sys
from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata
import random

class PrintWavePass( BasePass ):

  def __call__( self, top ):
    setattr(top,"_print_wave",_help_print)

def _process_binary(sig,base):
    """
    Returns int value from a signal in 32b form. Used for testing.

    Example: input: 0b00000000000000000000000000000000 10
             output: 0
    """
    if sig[1] == "b":
        sig = sig[2:]
    if base == 10:
        tempint = int(sig,2)
        if sig[0] == '1':
            return tempint -2 **32      #taking 2's complement.
                                    #leading 1 indicates a negative number
        else:
            return tempint
    #hex number
    else:
        temphex = hex(int(sig,2))
        l = len(temphex)
        if l > 4:
            temphex = temphex[:4]
        if l < 4:
            temphex = '0'*(4-l) + temphex
        return temphex

def _help_print(self):
    char_length = 5
    _tick = u'\u258f'
    _up, _down = u'\u2571', u'\u2572'
    _x, _low, _high = u'\u2573', u'\u005f', u'\u203e'
    _revstart, _revstop = '\x1B[7m', '\x1B[0m'
    _lightgrey = '\033[47m'
    _back='\033[0m'  #back to normal printing
    allsignals = self._collectsignals

    #spaces before cycle number
    maxlength = 0
    for sig in allsignals:
        #   Example: s.in(12b)
        # length of signal name + (b) + number of digits, like 12
        thislength = len(sig) + len(str(len(allsignals[sig][0][0])))+3
        if thislength > maxlength:
            if sig != "s.clk" and sig != "s.reset":
                maxlength = thislength

    print(" "*(maxlength+1),end = "")

    for i in range(0,len(allsignals["s.clk"]),5):
          print(_tick + str(i)+ " "*(5*char_length-1) ,end="")

    #signals
    for sig in allsignals:

      if sig != "s.clk" and sig != "s.reset":
        print("")
        bitlength = len(allsignals[sig][0][0])-2
        suffix = "(" + str(bitlength) + "b)"
        print((sig+suffix).rjust(maxlength),end="")
        prevsig = None
        # one bit
        if bitlength==1:
          for val in allsignals[sig]:

            #every 5 cycles add a space
            if val[1]%5 == 0:
              print(" ",end = "")
            if val[0][2] == '1':
                currentsig = _high
            else:
                currentsig = _low
            if prevsig is not None:
              if prevsig == _low and currentsig == _high:
                print(_up+currentsig*(char_length-1),end = "")
              elif prevsig == _high and currentsig == _low:
                print(_down+currentsig*(char_length-1),end = "")
              else:
                  print(currentsig*char_length,end = "")
            else:
                print(currentsig*char_length,end = "")
            prevsig = currentsig

          print("")
        #multiple bits
        else:
            for val in allsignals[sig]:
              if val[1]%5 == 0:
                print(_back +" ",end = "")

              current = _process_binary(val[0],16)
              if prevsig is None:
                    print(_lightgrey + " " +'\033[30m'+ current,end = "")
              else:
                  if prevsig[0] == val[0]:
                      print(_lightgrey + " "*(char_length),end = "")
                  else:
                      print(_lightgrey + '\033[30m'+_x + current,end = "")
              prevsig = val
            print(_back + "")

    print("")

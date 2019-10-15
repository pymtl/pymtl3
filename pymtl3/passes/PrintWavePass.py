"""
========================================================================
PrintWavePass.py
========================================================================
#Print the most sigficant number of signals in wave form.
.state(or State) is processed in state form.
#top object uses top.printwave(top) to print.

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


class PrintWavePass( BasePass ):

  def __call__( self, top ):
    setattr(top,"printwave",helpprint)

def helpprint(self):
    char_length = 5
    _tick = u'\u258f'
    _up, _down = u'\u2571', u'\u2572'
    _x, _low, _high = u'\u2573', u'\u005f', u'\u203e'
    _revstart, _revstop = '\x1B[7m', '\x1B[0m'
    _lightgrey = '\033[47m'
    _back='\033[0m'
    allsignals = self._collectsignals

    maxlength = 0
    for sig in allsignals:
        if len(sig) > maxlength:
            if sig != "s.clk" and sig != "s.reset":
                maxlength = len(sig)
    print(" "*(maxlength+1),end = "")
    for i in range(0,len(allsignals["s.clk"]),5):
          print("|" + str(i)+ " "*(5*char_length-1) ,end="")
    print("")
    for sig in allsignals:
      if sig != "s.clk" and sig != "s.reset":
        print("")
        print(sig.rjust(maxlength),end="")
        prev_val = None
        if sig != "s.state" and sig != "s.State":
          for val in allsignals[sig]:
            if val[1]%5 == 0:
              print(" ",end = "")
            if val[0][:3] == '0b1':
                currentsig = _high
            else:
                currentsig = _low
            if prev_val is not None:
              if prev_val[0][:3] == '0b0' and currentsig == _high:
                print(_up+currentsig*(char_length-1),end = "")
              elif prev_val[0][:3] == '0b1' and currentsig == _low:
                print(_down+currentsig*(char_length-1),end = "")
              else:
                  print(currentsig*char_length,end = "")
            else:
                print(currentsig*char_length,end = "")
            prev_val = val
        else:
            for val in allsignals[sig]:
              if val[1]%5 == 0:
                print(_back +" ",end = "")
              if len(val[0]) > char_length+2:

                  cutval = val[0][2:char_length+2]
              else:
                  cutval = val[0][2:]
              if prev_val is None:
                    print(_lightgrey + " " + cutval.rjust(char_length-1),end = "")
              else:
                  if prev_val[0] == val[0]:
                      print(_lightgrey + " "*(char_length),end = "")
                  else:
                      print(_lightgrey + _x + cutval.rjust(char_length-1),end = "")
              prev_val = val
            print(_back,"",end = "")
    print("")

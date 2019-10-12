from antlr4 import *
from FIRRTLLexer import FIRRTLLexer
from FIRRTLListener import FIRRTLListener
from FIRRTLParser import FIRRTLParser
import sys

class FIRRTLPrintListener(FIRRTLListener):
    def enterCircuit(self, ctx):
        print(dir(ctx))

def main():
    lexer = FIRRTLLexer(FileStream('Icache.fir'))
    stream = CommonTokenStream(lexer)
    parser = FIRRTLParser(stream)
    tree = parser.circuit()
    printer = FIRRTLPrintListener()
    walker = ParseTreeWalker()
    walker.walk(printer, tree)

if __name__ == '__main__':
    main()

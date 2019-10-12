# Generated from FIRRTL.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .FIRRTLParser import FIRRTLParser
else:
    from FIRRTLParser import FIRRTLParser

# This class defines a complete listener for a parse tree produced by FIRRTLParser.
class FIRRTLListener(ParseTreeListener):

    # Enter a parse tree produced by FIRRTLParser#circuit.
    def enterCircuit(self, ctx:FIRRTLParser.CircuitContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#circuit.
    def exitCircuit(self, ctx:FIRRTLParser.CircuitContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#module.
    def enterModule(self, ctx:FIRRTLParser.ModuleContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#module.
    def exitModule(self, ctx:FIRRTLParser.ModuleContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#port.
    def enterPort(self, ctx:FIRRTLParser.PortContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#port.
    def exitPort(self, ctx:FIRRTLParser.PortContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#direction.
    def enterDirection(self, ctx:FIRRTLParser.DirectionContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#direction.
    def exitDirection(self, ctx:FIRRTLParser.DirectionContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#typetype.
    def enterTypetype(self, ctx:FIRRTLParser.TypetypeContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#typetype.
    def exitTypetype(self, ctx:FIRRTLParser.TypetypeContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#field.
    def enterField(self, ctx:FIRRTLParser.FieldContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#field.
    def exitField(self, ctx:FIRRTLParser.FieldContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#defname.
    def enterDefname(self, ctx:FIRRTLParser.DefnameContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#defname.
    def exitDefname(self, ctx:FIRRTLParser.DefnameContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#parameter.
    def enterParameter(self, ctx:FIRRTLParser.ParameterContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#parameter.
    def exitParameter(self, ctx:FIRRTLParser.ParameterContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#moduleBlock.
    def enterModuleBlock(self, ctx:FIRRTLParser.ModuleBlockContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#moduleBlock.
    def exitModuleBlock(self, ctx:FIRRTLParser.ModuleBlockContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#simple_reset0.
    def enterSimple_reset0(self, ctx:FIRRTLParser.Simple_reset0Context):
        pass

    # Exit a parse tree produced by FIRRTLParser#simple_reset0.
    def exitSimple_reset0(self, ctx:FIRRTLParser.Simple_reset0Context):
        pass


    # Enter a parse tree produced by FIRRTLParser#simple_reset.
    def enterSimple_reset(self, ctx:FIRRTLParser.Simple_resetContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#simple_reset.
    def exitSimple_reset(self, ctx:FIRRTLParser.Simple_resetContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#reset_block.
    def enterReset_block(self, ctx:FIRRTLParser.Reset_blockContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#reset_block.
    def exitReset_block(self, ctx:FIRRTLParser.Reset_blockContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#stmt.
    def enterStmt(self, ctx:FIRRTLParser.StmtContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#stmt.
    def exitStmt(self, ctx:FIRRTLParser.StmtContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#memField.
    def enterMemField(self, ctx:FIRRTLParser.MemFieldContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#memField.
    def exitMemField(self, ctx:FIRRTLParser.MemFieldContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#simple_stmt.
    def enterSimple_stmt(self, ctx:FIRRTLParser.Simple_stmtContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#simple_stmt.
    def exitSimple_stmt(self, ctx:FIRRTLParser.Simple_stmtContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#suite.
    def enterSuite(self, ctx:FIRRTLParser.SuiteContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#suite.
    def exitSuite(self, ctx:FIRRTLParser.SuiteContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#when.
    def enterWhen(self, ctx:FIRRTLParser.WhenContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#when.
    def exitWhen(self, ctx:FIRRTLParser.WhenContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#info.
    def enterInfo(self, ctx:FIRRTLParser.InfoContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#info.
    def exitInfo(self, ctx:FIRRTLParser.InfoContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#mdir.
    def enterMdir(self, ctx:FIRRTLParser.MdirContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#mdir.
    def exitMdir(self, ctx:FIRRTLParser.MdirContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#ruw.
    def enterRuw(self, ctx:FIRRTLParser.RuwContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#ruw.
    def exitRuw(self, ctx:FIRRTLParser.RuwContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#exp.
    def enterExp(self, ctx:FIRRTLParser.ExpContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#exp.
    def exitExp(self, ctx:FIRRTLParser.ExpContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#idid.
    def enterIdid(self, ctx:FIRRTLParser.IdidContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#idid.
    def exitIdid(self, ctx:FIRRTLParser.IdidContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#fieldId.
    def enterFieldId(self, ctx:FIRRTLParser.FieldIdContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#fieldId.
    def exitFieldId(self, ctx:FIRRTLParser.FieldIdContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#intLit.
    def enterIntLit(self, ctx:FIRRTLParser.IntLitContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#intLit.
    def exitIntLit(self, ctx:FIRRTLParser.IntLitContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#keywordAsId.
    def enterKeywordAsId(self, ctx:FIRRTLParser.KeywordAsIdContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#keywordAsId.
    def exitKeywordAsId(self, ctx:FIRRTLParser.KeywordAsIdContext):
        pass


    # Enter a parse tree produced by FIRRTLParser#primop.
    def enterPrimop(self, ctx:FIRRTLParser.PrimopContext):
        pass

    # Exit a parse tree produced by FIRRTLParser#primop.
    def exitPrimop(self, ctx:FIRRTLParser.PrimopContext):
        pass



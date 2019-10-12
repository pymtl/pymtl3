// See LICENSE for license details.

// Shunning: I basically take FIRRTL's g4 and port the scala code to
// Python3 to handle strict indentations in the same way as firrtl
// https://github.com/freechipsproject/firrtl/blob/master/src/main/antlr4/FIRRTL.g4
// Note that some of the APIs are different across scala/python:
//       Scala                    |            Python
//  copy constructor              |         token.clone()
// token.getCharPositionInLine    |         token.column
//   token.getType                |         token.type
//   token.getText                |         token.text
//
// Usage: antlr4 -Dlanguage=Python3 FIRRTL.g4

grammar FIRRTL;

tokens { INDENT, DEDENT }

@lexer::header {
from antlr4.Token import CommonToken
from collections  import deque

import importlib

# Allow languages to extend the lexer and parser, by loading the parser dynamically
# Shunning: this is from https://github.com/antlr/grammars-v4/blob/master/python3-py/Python3.g4
# I need this to access LanguageParser.INDENT/DEDENT

module_path = __name__[:-5]
language_name = __name__.split('.')[-1]
language_name = language_name[:-5]  # Remove Lexer from name
LanguageParser = getattr(importlib.import_module('{}Parser'.format(module_path)), '{}Parser'.format(language_name))
}

@lexer::members {

@property
def tokens(self):
  try:  return self._tokens
  except AttributeError:  self._tokens = deque();  return self._tokens

@property
def indents(self):
  try:  return self._indents
  except AttributeError:  self._indents = []; return self._indents

@property
def reachedEof(self):
  try:  return self._reachedEof
  except AttributeError:  self._reachedEof = False; return self._reachedEof
@reachedEof.setter
def reachedEof(self, value):
  self._reachedEof = value

def reset(self):
  super().reset()
  self.tokens = deque()
  self.indents = []
  self.opened = 0
  self.reachedEof = False

def createToken( self, tokenType, copyFrom ):
  ret = copyFrom.clone()
  ret.type = tokenType

  if   tokenType == self.NEWLINE: ret.text = "NEWLINE"
  elif tokenType == LanguageParser.INDENT:  ret.text = "INDENT"
  elif tokenType == LanguageParser.DEDENT:  ret.text = "DEDENT"

  return ret

def eofHandler( self, t ):
  if not self.indents:
    return createToken( self.NEWLINE, t )

  ret = self.unwindTo( 0, t )
  self.reachedEof = True

  self.tokens.append(t)
  return ret

def nextToken( self ):
  # only for first run
  if not self.indents:
    self.indents.append( 0 )

    firstRealToken = super().nextToken()
    while firstRealToken.type == self.NEWLINE:
      firstRealToken = super().nextToken()

    indent = firstRealToken.column
    if indent > 0:
      self.indents.append( indent )
      self.tokens.append( self.createToken( LanguageParser.INDENT, firstRealToken) )

    self.tokens.append( firstRealToken )

  t = super().nextToken() if not self.tokens else self.tokens.popleft()

  if self.reachedEof:  return t

  if t.type == self.NEWLINE:
    nextNext = super().nextToken()
    while nextNext.type == self.NEWLINE:
      t = nextNext
      nextNext = super().nextToken()

    if nextNext.type == Token.EOF:
      return self.eofHandler( nextNext )

    nlText = t.text
    nlLen  = len(nlText)
    indent = nlLen - (2 if (nlLen > 0 and nlText[0] == '\r') else 1)

    prevIndent = self.indents[-1] # stack!

    if indent == prevIndent:
      ret = t
    elif indent > prevIndent:
      self.indents.append( indent )
      ret = self.createToken( LanguageParser.INDENT, t )
    else:
      ret = self.unwindTo( indent, t )

    self.tokens.append( nextNext )
    return ret

  if t.type == Token.EOF: return self.eofHandler(t)

  return t

# Returns a DEDENT token, and also queues up additional DEDENTs as necessary.
#
# @param targetIndent the "size" of the indentation (number of spaces) by the end
# @param copyFrom     the triggering token
# @return a DEDENT token

def unwindTo( self, targetIndent, copyFrom ):
  assert not self.tokens
  self.tokens.append( self.createToken( self.NEWLINE, copyFrom ) )

  # To make things easier, we'll queue up ALL of the dedents, and then pop off the first one.
  # For example, here's how some text is analyzed:
  #
  #  Text          :  Indentation  :  Action         : Indents Deque
  #  [ baseline ]  :  0            :  nothing        : [0]
  #  [   foo    ]  :  2            :  INDENT         : [0, 2]
  #  [    bar   ]  :  3            :  INDENT         : [0, 2, 3]
  #  [ baz      ]  :  0            :  DEDENT x2      : [0]

  while True:
    prevIndent = self.indents.pop()
    if prevIndent > targetIndent:
      self.tokens.append( self.createToken( LanguageParser.DEDENT, copyFrom ) )
    else:
      if prevIndent < targetIndent:
        self.indents.append( prevIndent )
        self.tokens.append( self.createToken(LanguageParser.INDENT, copyFrom ) )
      break

  self.indents.append( targetIndent )
  return self.tokens.popleft()
}

/*------------------------------------------------------------------
 * PARSER RULES
 *------------------------------------------------------------------*/

// Does there have to be at least one module?
circuit
  : 'circuit' idid ':' info? INDENT module* DEDENT
  ;

module
  : 'module' idid ':' info? INDENT port* moduleBlock DEDENT
  | 'extmodule' idid ':' info? INDENT port* defname? parameter* DEDENT
  ;

port
  : direction idid ':' typetype info? NEWLINE
  ;

direction
  : 'input'
  | 'output'
  ;

typetype
  : 'UInt' ('<' intLit '>')?
  | 'SInt' ('<' intLit '>')?
  | 'Fixed' ('<' intLit '>')? ('<' '<' intLit '>' '>')?
  | 'Clock'
  | 'AsyncReset'
  | 'Reset'
  | 'Analog' ('<' intLit '>')?
  | '{' field* '}'        // Bundle
  | typetype '[' intLit ']'   // Vector
  ;

field
  : 'flip'? fieldId ':' typetype
  ;

defname
  : 'defname' '=' idid NEWLINE
  ;

parameter
  : 'parameter' idid '=' intLit NEWLINE
  | 'parameter' idid '=' StringLit NEWLINE
  | 'parameter' idid '=' DoubleLit NEWLINE
  | 'parameter' idid '=' RawString NEWLINE
  ;

moduleBlock
  : simple_stmt*
  ;

simple_reset0:  'reset' '=>' '(' exp exp ')';

simple_reset
	: simple_reset0
	| '(' simple_reset0 ')'
	;

reset_block
	: INDENT simple_reset info? NEWLINE DEDENT
	| '(' simple_reset ')'
  ;

stmt
  : 'wire' idid ':' typetype info?
  | 'reg' idid ':' typetype exp ('with' ':' reset_block)? info?
  | 'mem' idid ':' info? INDENT memField* DEDENT
  | 'cmem' idid ':' typetype info?
  | 'smem' idid ':' typetype ruw? info?
  | mdir 'mport' idid '=' idid '[' exp ']' exp info?
  | 'inst' idid 'of' idid info?
  | 'node' idid '=' exp info?
  | exp '<=' exp info?
  | exp '<-' exp info?
  | exp 'is' 'invalid' info?
  | when
  | 'stop(' exp exp intLit ')' info?
  | 'printf(' exp exp StringLit ( exp)* ')' info?
  | 'skip' info?
  | 'attach' '(' exp+ ')' info?
  ;

memField
	:  'data-type' '=>' typetype NEWLINE
	| 'depth' '=>' intLit NEWLINE
	| 'read-latency' '=>' intLit NEWLINE
	| 'write-latency' '=>' intLit NEWLINE
	| 'read-under-write' '=>' ruw NEWLINE
	| 'reader' '=>' idid+ NEWLINE
	| 'writer' '=>' idid+ NEWLINE
	| 'readwriter' '=>' idid+ NEWLINE
	;

simple_stmt
  : stmt | NEWLINE
  ;

/*
    We should provide syntatctical distinction between a "moduleBody" and a "suite":
    - statements require a "suite" which means they can EITHER have a "simple statement" (one-liner) on the same line
        OR a group of one or more _indented_ statements after a new-line. A "suite" may _not_ be empty
    - modules on the other hand require a group of one or more statements without any indentation to follow "port"
        definitions. Let's call that _the_ "moduleBody". A "moduleBody" could possibly be empty
*/
suite
  : simple_stmt
  | INDENT simple_stmt+ DEDENT
  ;

when
  : 'when' exp ':' info? suite? ('else' ( when | ':' info? suite?) )?
  ;

info
  : FileInfo
  ;

mdir
  : 'infer'
  | 'read'
  | 'write'
  | 'rdwr'
  ;

ruw
  : 'old'
  | 'new'
  | 'undefined'
  ;

exp
  : 'UInt' ('<' intLit '>')? '(' intLit ')'
  | 'SInt' ('<' intLit '>')? '(' intLit ')'
  | idid    // Ref
  | exp '.' fieldId
  | exp '.' DoubleLit // TODO Workaround for #470
  | exp '[' intLit ']'
  | exp '[' exp ']'
  | 'mux(' exp exp exp ')'
  | 'validif(' exp exp ')'
  | primop exp* intLit*  ')'
  ;

idid
  : Id
  | keywordAsId
  ;

fieldId
  : Id
  | RelaxedId
  | UnsignedInt
  | keywordAsId
  ;

intLit
  : UnsignedInt
  | SignedInt
  | HexLit
  ;

// Keywords that are also legal ids
keywordAsId
  : 'circuit'
  | 'module'
  | 'extmodule'
  | 'parameter'
  | 'input'
  | 'output'
  | 'UInt'
  | 'SInt'
  | 'Clock'
  | 'Analog'
  | 'Fixed'
  | 'flip'
  | 'wire'
  | 'reg'
  | 'with'
  | 'reset'
  | 'mem'
  | 'depth'
  | 'reader'
  | 'writer'
  | 'readwriter'
  | 'inst'
  | 'of'
  | 'node'
  | 'is'
  | 'invalid'
  | 'when'
  | 'else'
  | 'stop'
  | 'printf'
  | 'skip'
  | 'old'
  | 'new'
  | 'undefined'
  | 'mux'
  | 'validif'
  | 'cmem'
  | 'smem'
  | 'mport'
  | 'infer'
  | 'read'
  | 'write'
  | 'rdwr'
  ;

// Parentheses are added as part of name because semantics require no space between primop and open parentheses
// (And ANTLR either ignores whitespace or considers it everywhere)
primop
  : 'add('
  | 'sub('
  | 'mul('
  | 'div('
  | 'rem('
  | 'lt('
  | 'leq('
  | 'gt('
  | 'geq('
  | 'eq('
  | 'neq('
  | 'pad('
  | 'asUInt('
  | 'asAsyncReset('
  | 'asSInt('
  | 'asClock('
  | 'shl('
  | 'shr('
  | 'dshl('
  | 'dshr('
  | 'cvt('
  | 'neg('
  | 'not('
  | 'and('
  | 'or('
  | 'xor('
  | 'andr('
  | 'orr('
  | 'xorr('
  | 'cat('
  | 'bits('
  | 'head('
  | 'tail('
  | 'asFixedPoint('
  | 'bpshl('
  | 'bpshr('
  | 'bpset('
  ;

/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

UnsignedInt
  : '0'
  | PosInt
  ;

SignedInt
  : ( '+' | '-' ) PosInt
  ;

fragment
PosInt
  : [1-9] ( Digit )*
  ;

HexLit
  : '"' 'h' ( '+' | '-' )? ( HexDigit )+ '"'
  ;

DoubleLit
  : ( '+' | '-' )? Digit+ '.' Digit+ ( 'E' ( '+' | '-' )? Digit+ )?
  ;

fragment
Digit
  : [0-9]
  ;

fragment
HexDigit
  : [a-fA-F0-9]
  ;

StringLit
  : '"' UnquotedString? '"'
  ;

RawString
  : '\'' UnquotedString? '\''
  ;

fragment
UnquotedString
  : ( '\\\'' | '\\"' | ~[\r\n] )+?
  ;

FileInfo
  : '@[' ('\\]'|.)*? ']'
  ;

Id
  : LegalStartChar (LegalIdChar)*
  ;

RelaxedId
  : (LegalIdChar)+
  ;

fragment
LegalIdChar
  : LegalStartChar
  | Digit
  | '$'
  ;

fragment
LegalStartChar
  : [a-zA-Z_]
  ;

fragment COMMENT
  : ';' ~[\r\n]*
  ;

fragment WHITESPACE
	: [ \t,]+
	;

SKIP_
	: ( WHITESPACE | COMMENT ) -> skip
	;

NEWLINE
	:'\r'? '\n' ' '*
	;

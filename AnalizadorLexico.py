from dataclasses import dataclass
import re, sys, os, csv
from typing import List, Optional

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"[L{line},C{column}] {message}")
        self.line=line; self.column=column

class Lexer:
    KEYWORDS = {"let":"LET","const":"CONST","if":"IF","else":"ELSE","while":"WHILE","for":"FOR","function":"FUNCTION","return":"RETURN","true":"TRUE","false":"FALSE"}
    OPERATORS = {"==":"EQEQ","!=":"NEQ","<=":"LE",">=":"GE","&&":"AND_AND","||":"OR_OR","=":"EQ","<":"LT",">":"GT","+":"PLUS","-":"MINUS","*":"STAR","/":"SLASH","%":"PERCENT","!":"BANG",".":"DOT",",":"COMMA",";":"SEMICOLON","(":"LPAREN",")":"RPAREN","{":"LBRACE","}":"RBRACE","[":"LBRACKET","]":"RBRACKET"}
    OPERATOR_KEYS = sorted(OPERATORS.keys(), key=lambda s:(-len(s), s))

    _re_id_start = re.compile(r"[A-Za-z]")
    _re_id_part  = re.compile(r"[A-Za-z0-9_]")
    _re_digit    = re.compile(r"\d")
    _re_number   = re.compile(r"(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?")

    def __init__(self, s:str):
        self.source=s.replace("\r\n","\n").replace("\r","\n")
        self.length=len(self.source); self.pos=0; self.line=1; self.col=1

    def _peek(self,n:int=0)->str:
        i=self.pos+n
        return "\0" if i>=self.length else self.source[i]

    def _advance(self,n:int=1)->str:
        ch="\0"
        for _ in range(n):
            if self.pos>=self.length: return "\0"
            ch=self.source[self.pos]; self.pos+=1
            if ch=="\n": self.line+=1; self.col=1
            else: self.col+=1
        return ch

    def _match(self,text:str)->bool:
        if self.source.startswith(text,self.pos):
            self._advance(len(text)); return True
        return False

    def _skip_ws_and_comments(self):
        while True:
            ch=self._peek()
            if ch in (" ","\t","\f","\v","\n"):
                self._advance(); continue
            if ch=="/" and self._peek(1)=="/":
                start_line,start_col=self.line,self.col
                self._advance(2)
                while True:
                    if self._peek()=="\0":
                        raise LexerError("Comentario //...// sin cerrar", start_line, start_col)
                    if self._peek()=="/" and self._peek(1)=="/":
                        self._advance(2); break
                    self._advance()
                continue
            break

    def _lex_string(self)->Token:
        L,C=self.line,self.col
        assert self._peek()=='"'; self._advance()
        buf=[]
        while True:
            ch=self._peek()
            if ch=="\0":
                raise LexerError("Cadena sin cerrar", L, C)
            if ch=='"': self._advance(); break
            if ch=='\\':
                self._advance(); esc=self._peek()
                mapping={'"':'"','\\':'\\','n':'\n','t':'\t','r':'\r'}
                if esc in mapping:
                    buf.append(mapping[esc]); self._advance()
                else:
                    buf.append('\\'+esc); self._advance()
            else:
                buf.append(ch); self._advance()
        return Token("STRING","".join(buf),L,C)

    def _lex_number(self)->Token:
        L,C=self.line,self.col
        m=self._re_number.match(self.source[self.pos:])
        lex=m.group(0); self._advance(len(lex))
        return Token("NUM",lex,L,C)

    def _lex_identifier_or_keyword(self)->Token:
        L,C=self.line,self.col
        buf=[self._advance()]
        while True:
            ch=self._peek()
            if self._re_id_part.match(ch): buf.append(self._advance())
            else: break
        lex="".join(buf)
        t=self.KEYWORDS.get(lex,"ID")
        return Token(t,lex,L,C)

    def _lex_operator_or_delim(self):
        for op in self.OPERATOR_KEYS:
            if self._match(op):
                col_start=self.col-len(op)
                return Token(self.OPERATORS[op],op,self.line,col_start)
        return None

    def tokenize(self)->List[Token]:
        out:List[Token]=[]
        while True:
            self._skip_ws_and_comments()
            ch=self._peek()
            if ch=="\0": out.append(Token("EOF","",self.line,self.col)); break
            if ch=='"': out.append(self._lex_string()); continue
            if self._re_digit.match(ch) or (ch=="." and self._re_digit.match(self._peek(1))): out.append(self._lex_number()); continue
            if self._re_id_start.match(ch): out.append(self._lex_identifier_or_keyword()); continue
            op=self._lex_operator_or_delim()
            if op: out.append(op); continue
            raise LexerError(f"Símbolo no reconocido: '{ch}'", self.line, self.col)
        return out

def main():
    path="Entrada.txt"
    if len(sys.argv)>=2: path=sys.argv[1]
    if not os.path.exists(path): print(f"ERROR: no se encontró '{path}'"); sys.exit(1)
    with open(path,"r",encoding="utf-8") as f: src=f.read()
    lx=Lexer(src)
    try:
        toks=lx.tokenize()
        print(f"{'LINE':>4} {'COL':>4}  {'TYPE':<12}  LEXEME")
        print("-"*60)
        for t in toks:
            disp=t.lexeme.replace("\n","\\n")
            print(f"{t.line:4} {t.column:4}  {t.type:<12}  {disp}")
        with open("tokens.csv","w",newline="",encoding="utf-8") as cf:
            w=csv.writer(cf); w.writerow(["line","column","type","lexeme"])
            for t in toks: w.writerow([t.line,t.column,t.type,t.lexeme])
        print("\nSe escribió la tabla de tokens en 'tokens.csv'.")
    except LexerError as e:
        print("ERROR LÉXICO:", str(e))
        sys.exit(2)

if __name__=="__main__": main()
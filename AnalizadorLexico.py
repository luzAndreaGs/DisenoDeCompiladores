# AnalizadorLexico_v1.py
from dataclasses import dataclass
import re
from typing import List
import sys, os

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int

class Lexer:
    _re_id_start = re.compile(r"[A-Za-z]")
    _re_id_part  = re.compile(r"[A-Za-z0-9_]")
    _re_digit    = re.compile(r"\d")
    _re_number   = re.compile(r"(?:\d+\.\d*|\.\d+|\d+)")

    def __init__(self, source: str):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.length = len(self.source)
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, n: int = 0) -> str:
        idx = self.pos + n
        return "\0" if idx >= self.length else self.source[idx]

    def _advance(self, n: int = 1) -> str:
        ch = "\0"
        for _ in range(n):
            if self.pos >= self.length:
                return "\0"
            ch = self.source[self.pos]
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        return ch

    def _lex_number(self) -> Token:
        start_line, start_col = self.line, self.col
        m = self._re_number.match(self.source[self.pos:])
        lex = m.group(0)
        self._advance(len(lex))
        return Token("NUM", lex, start_line, start_col)

    def _lex_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        buf = [self._advance()]
        while True:
            ch = self._peek()
            if self._re_id_part.match(ch):
                buf.append(self._advance())
            else:
                break
        return Token("ID", "".join(buf), start_line, start_col)

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            ch = self._peek()
            if ch == "\0":
                tokens.append(Token("EOF", "", self.line, self.col))
                break
            if ch in (" ", "\t", "\f", "\v", "\n"):
                self._advance(); continue
            if self._re_digit.match(ch) or (ch == "." and self._re_digit.match(self._peek(1))):
                tokens.append(self._lex_number()); continue
            if self._re_id_start.match(ch):
                tokens.append(self._lex_identifier()); continue
            # cualquier otro carácter se ignora en v1
            self._advance()
        return tokens

def main():
    path = "Entrada.txt"
    if len(sys.argv) >= 2: path = sys.argv[1]
    if not os.path.exists(path):
        print(f"ERROR: no se encontró el archivo '{path}'.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    lx = Lexer(src)
    toks = lx.tokenize()
    print(f"{'LINE':>4} {'COL':>4}  {'TYPE':<10}  LEXEME")
    print("-"*50)
    for t in toks:
        print(f"{t.line:4} {t.column:4}  {t.type:<10}  {t.lexeme}")

if __name__ == "__main__":
    main()
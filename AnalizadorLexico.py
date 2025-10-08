# AnalizadorLexico.py
from dataclasses import dataclass
import re
from typing import List, Optional
import sys
import csv
import os

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.msg = message
        self.line = line
        self.column = column
        super().__init__(f"[L{line},C{column}] {message}")

class Lexer:
    """
    Analizador léxico
    - Comentarios: // ... //  (debe haber cierre con //)
    - ID: inicia con letra [A-Za-z], continúa con [A-Za-z0-9_]
    - STRING: " ... "
    - NUM: entero/decimal con notación científica opcional (e.g. 12, 12.2, 12e21, 13e-12, 1.2e+3)
    - Ignora espacios/saltos y comentarios.
    """

    # Palabras reservadas según la gramática
    KEYWORDS = {
        "let": "LET",
        "const": "CONST",
        "function": "FUNCTION",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "for": "FOR",
        "return": "RETURN",
        "true": "TRUE",
        "false": "FALSE",
    }

    # Operadores y separadores
    OPERATORS = {
        "==": "EQEQ",
        "!=": "NEQ",
        "<=": "LE",
        ">=": "GE",
        "&&": "AND_AND",
        "||": "OR_OR",
        "=": "EQ",
        "<": "LT",
        ">": "GT",
        "+": "PLUS",
        "-": "MINUS",
        "*": "STAR",
        "/": "SLASH",
        "%": "PERCENT",
        "!": "BANG",
        ".": "DOT",
        ",": "COMMA",
        ";": "SEMICOLON",
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        "[": "LBRACKET",
        "]": "RBRACKET",
    }
    OPERATOR_KEYS = sorted(OPERATORS.keys(), key=lambda s: (-len(s), s))

    # Patrones
    _re_id_start = re.compile(r"[A-Za-z]")          # IDs deben iniciar con letra
    _re_id_part  = re.compile(r"[A-Za-z0-9_]")      # luego pueden incluir dígitos y _
    _re_digit    = re.compile(r"\d")

    # Números: entero/decimal con exponente (e|E[+/-]?d+)
    _re_number = re.compile(r"""
        (?:
            (?:\d+\.\d*|\.\d+|\d+)       # 12.34 | 12. | .34 | 12
            (?:[eE][+-]?\d+)?            # exponente opcional: e10, e-3, E+7
        )
    """, re.VERBOSE)

    def __init__(self, source: str):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.length = len(self.source)
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, n: int = 0) -> str:
        idx = self.pos + n
        if idx >= self.length:
            return "\0"
        return self.source[idx]

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

    def _match(self, text: str) -> bool:
        if self.source.startswith(text, self.pos):
            self._advance(len(text))
            return True
        return False

    def _skip_whitespace_and_comments(self):
        while True:
            ch = self._peek()

            # espacios y saltos
            if ch in (" ", "\t", "\f", "\v", "\n"):
                self._advance()
                continue

            # Comentarios del tipo // ... // 
            if ch == "/" and self._peek(1) == "/":
                start_line, start_col = self.line, self.col
                self._advance(2)  # consume "//" inicial
                # Avanzar hasta encontrar el cierre "//"
                closed = False
                while True:
                    if self._peek() == "\0":
                        raise LexerError("Comentario //...// sin cerrar", start_line, start_col)
                    if self._peek() == "/" and self._peek(1) == "/":
                        self._advance(2)  # consume cierre "//"
                        closed = True
                        break
                    self._advance()
                if closed:
                    continue

            break

    def _lex_string(self) -> Token:
        start_line, start_col = self.line, self.col
        assert self._peek() == '"'
        self._advance()  # consume "
        buf = []
        while True:
            ch = self._peek()
            if ch == "\0":
                raise LexerError("Cadena sin cerrar", start_line, start_col)
            if ch == '"':
                self._advance()
                break
            if ch == "\\": 
                self._advance()
                esc = self._peek()
                mapping = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r"}
                if esc in mapping:
                    buf.append(mapping[esc])
                    self._advance()
                else:
                    buf.append("\\" + esc)
                    self._advance()
            else:
                buf.append(ch)
                self._advance()
        return Token("STRING", "".join(buf), start_line, start_col)

    def _lex_number(self) -> Token:
        start_line, start_col = self.line, self.col
        m = self._re_number.match(self.source[self.pos:])
        assert m
        lex = m.group(0)
        self._advance(len(lex))
        nxt = self._peek()
        if re.match(r"[A-Za-z_]", nxt):
            # Construye el lexema ofensivo completo (e.g., "12abc_xyz")
            off_buf = [lex]
            i = 0
            while True:
                ch = self._peek(i)
                if ch == "\0" or not re.match(r"[A-Za-z0-9_]", ch):
                    break
                off_buf.append(ch)
                i += 1
            ofensivo = "".join(off_buf)
            raise LexerError(
                f"Identificador no puede iniciar con dígito: '{ofensivo}'",
                start_line,
                start_col
            )

        return Token("NUM", lex, start_line, start_col)

    def _lex_identifier_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.col
        buf = []
        # primer carácter (letra)
        buf.append(self._advance())
        # resto (letras/dígitos/_)
        while True:
            ch = self._peek()
            if self._re_id_part.match(ch):
                buf.append(self._advance())
            else:
                break
        lex = "".join(buf)
        ttype = self.KEYWORDS.get(lex, "ID")
        return Token(ttype, lex, start_line, start_col)

    def _lex_operator_or_delim(self) -> Optional[Token]:
        for op in self.OPERATOR_KEYS:
            if self._match(op):
                col_start = self.col - len(op)
                return Token(self.OPERATORS[op], op, self.line, col_start)
        return None

    def _expected_hint(self, ch: str) -> str:
        candidates = []
        if self._re_id_start.match(ch):
            candidates.append("ID / palabra reservada")
        if self._re_digit.match(ch) or ch == ".":
            candidates.append("NUM")
        for op in self.OPERATOR_KEYS:
            if op.startswith(ch):
                candidates.append(op)
        for d in ["(", ")", "{", "}", "[", "]", ",", ";", ".", '"']:
            if d.startswith(ch):
                candidates.append(d)
        if not candidates:
            return "Token desconocido"
        seen, out = set(), []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return "Posibles tokens esperados: " + ", ".join(out)

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            self._skip_whitespace_and_comments()
            ch = self._peek()
            if ch == "\0":
                tokens.append(Token("EOF", "", self.line, self.col))
                break

            # String
            if ch == '"':
                tokens.append(self._lex_string())
                continue

            # Número (enteros/decimales con opcional exponente)
            if self._re_digit.match(ch) or (ch == "." and self._re_digit.match(self._peek(1))):
                tokens.append(self._lex_number())
                continue

            # Identificador o keyword (debe iniciar con letra)
            if self._re_id_start.match(ch):
                tokens.append(self._lex_identifier_or_keyword())
                continue

            # Operadores / delimitadores
            op_tok = self._lex_operator_or_delim()
            if op_tok:
                tokens.append(op_tok)
                continue

            # Carácter no reconocido
            msg = f"Símbolo no reconocido: '{ch}'. " + self._expected_hint(ch)
            raise LexerError(msg, self.line, self.col)
        return tokens


# =========================
# Entrada por archivo y salida
# =========================
def main():
    # Archivo de entrada por defecto: "Entrada.txt"
    path = "Entrada.txt"
    if len(sys.argv) >= 2:
        path = sys.argv[1]

    if not os.path.exists(path):
        print(f"ERROR: no se encontró el archivo '{path}'.")
        print("Uso: python AnalizadorLexico.py [archivo_entrada.txt]")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    lx = Lexer(source)
    try:
        tokens = lx.tokenize()

        # Imprimir tabla en consola
        print(f"{'LINE':>4} {'COL':>4}  {'TYPE':<12}  LEXEME")
        print("-" * 60)
        for t in tokens:
            disp = t.lexeme.replace("\n", "\\n")
            print(f"{t.line:4} {t.column:4}  {t.type:<12}  {disp}")

        # Guardar CSV de tokens
        out_csv = "tokens.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow(["line", "column", "type", "lexeme"])
            for t in tokens:
                writer.writerow([t.line, t.column, t.type, t.lexeme])
        print(f"\nSe escribió la tabla de tokens en '{out_csv}'.")

    except LexerError as e:
        print("ERROR LÉXICO:", str(e))

        # Tabla de errores en consola
        print("\nTABLA DE ERRORES")
        print(f"{'LINE':>4} {'COL':>4}  MESSAGE")
        print("-" * 60)
        print(f"{e.line:4} {e.column:4}  {e.msg}")

        # Guardar CSV de errores
        err_csv = "errores.csv"
        with open(err_csv, "w", newline="", encoding="utf-8") as ef:
            writer = csv.writer(ef)
            writer.writerow(["line", "column", "message"])
            writer.writerow([e.line, e.column, e.msg])
        print(f"\nSe escribió la tabla de errores en '{err_csv}'.")
        sys.exit(2)

if __name__ == "__main__":
    main()
from typing import List, Optional
from AnalizadorLexico import Token

class SyntaxError(Exception):
    def __init__(self, message: str, line: int, column: int, expected: str = ""):
        self.message = message
        self.line = line
        self.column = column
        self.expected = expected
        super().__init__(f"[L{line},C{column}] {message}")

class AnalizadorSintactico:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current_index = 0
        self.errores = []
        
    def current_token(self) -> Optional[Token]:
        """Obtiene el token actual"""
        if self.current_index < len(self.tokens):
            return self.tokens[self.current_index]
        return None
    
    def advance(self):
        """Avanza al siguiente token"""
        if self.current_index < len(self.tokens):
            self.current_index += 1
    
    def match(self, expected_type: str) -> bool:
        """Verifica si el token actual coincide con el tipo esperado"""
        token = self.current_token()
        if token and token.type == expected_type:
            self.advance()
            return True
        return False
    
    def expect(self, expected_type: str, error_message: str = ""):
        """Espera un token específico o lanza error"""
        token = self.current_token()
        if not token:
            raise SyntaxError(
                f"Se esperaba '{expected_type}' pero se llegó al final del archivo",
                0, 0, expected_type
            )
        
        if not self.match(expected_type):
            if not error_message:
                error_message = f"Se esperaba '{expected_type}' pero se encontró '{token.type}'"
            raise SyntaxError(
                error_message,
                token.line,
                token.column,
                expected_type
            )
    
    def parse(self) -> bool:
        """Método principal que inicia el análisis sintáctico"""
        try:
            return self.programa()
        except SyntaxError as e:
            self.errores.append(e)
            return False
    
    def programa(self) -> bool:
        """PROGRAMA → DECLARACION* EOF"""
        while self.current_token() and self.current_token().type != "EOF":
            if not self.declaracion():
                return False
        
        # Verificar EOF al final
        if self.current_token() and self.current_token().type == "EOF":
            self.advance()
            return True
        else:
            token = self.current_token()
            raise SyntaxError(
                "Se esperaba el final del archivo",
                token.line if token else 0,
                token.column if token else 0,
                "EOF"
            )
    
    def declaracion(self) -> bool:
        """DECLARACION → DECLARACION_VAR | DECLARACION_FUNC | SENTENCIA"""
        token = self.current_token()
        if not token:
            return False
            
        if token.type in ["LET", "CONST"]:
            return self.declaracion_var()
        elif token.type == "FUNCTION":
            return self.declaracion_func()
        else:
            return self.sentencia()
    
    def declaracion_var(self) -> bool:
        """DECLARACION_VAR → (LET | CONST) ID = EXPRESION ;"""
        try:
            # LET o CONST
            if not self.match("LET") and not self.match("CONST"):
                token = self.current_token()
                raise SyntaxError(
                    "Se esperaba 'let' o 'const'",
                    token.line if token else 0,
                    token.column if token else 0,
                    "LET o CONST"
                )
            
            # ID
            self.expect("ID", "Se esperaba un identificador después de 'let'/'const'")
            
            # =
            self.expect("EQ", "Se esperaba '=' después del identificador")
            
            # EXPRESION
            if not self.expresion():
                return False
            
            # ;
            self.expect("SEMICOLON", "Se esperaba ';' al final de la declaración")
            
            return True
            
        except SyntaxError as e:
            self.errores.append(e)
            return False
    
    def declaracion_func(self) -> bool:
        """DECLARACION_FUNC → FUNCTION ID ( PARAMETROS ) BLOQUE"""
        try:
            # FUNCTION
            self.expect("FUNCTION", "Se esperaba 'function'")
            
            # ID
            self.expect("ID", "Se esperaba un nombre de función")
            
            # (
            self.expect("LPAREN", "Se esperaba '(' después del nombre de la función")
            
            # PARAMETROS (simplificado)
            self.parametros()
            
            # )
            self.expect("RPAREN", "Se esperaba ')' después de los parámetros")
            
            # BLOQUE
            return self.bloque()
            
        except SyntaxError as e:
            self.errores.append(e)
            return False
    
    def sentencia(self) -> bool:
        """SENTENCIA → SENTENCIA_IF | EXPRESION ;"""
        token = self.current_token()
        if not token:
            return False
            
        if token.type == "IF":
            return self.sentencia_if()
        else:
            # Expresión simple
            if self.expresion():
                self.expect("SEMICOLON", "Se esperaba ';' después de la expresión")
                return True
            return False
    
    def sentencia_if(self) -> bool:
        """SENTENCIA_IF → IF ( EXPRESION ) BLOQUE"""
        try:
            # IF
            self.expect("IF", "Se esperaba 'if'")
            
            # (
            self.expect("LPAREN", "Se esperaba '(' después de 'if'")
            
            # EXPRESION
            if not self.expresion():
                return False
            
            # )
            self.expect("RPAREN", "Se esperaba ')' después de la condición")
            
            # BLOQUE
            return self.bloque()
            
        except SyntaxError as e:
            self.errores.append(e)
            return False
    
    def bloque(self) -> bool:
        """BLOQUE → { DECLARACION* }"""
        try:
            # {
            self.expect("LBRACE", "Se esperaba '{'")
            
            # DECLARACION*
            while (self.current_token() and 
                   self.current_token().type not in ["RBRACE", "EOF"]):
                if not self.declaracion():
                    return False
            
            # }
            self.expect("RBRACE", "Se esperaba '}'")
            
            return True
            
        except SyntaxError as e:
            self.errores.append(e)
            return False
    
    def expresion(self) -> bool:
        """EXPRESION → TERMINO ((PLUS | MINUS) TERMINO)*"""
        if not self.termino():
            return False
        
        while self.current_token() and self.current_token().type in ["PLUS", "MINUS"]:
            self.advance()  # Consumir el operador
            if not self.termino():
                return False
        
        return True
    
    def termino(self) -> bool:
        """TERMINO → FACTOR ((STAR | SLASH) FACTOR)*"""
        if not self.factor():
            return False
        
        while self.current_token() and self.current_token().type in ["STAR", "SLASH"]:
            self.advance()  # Consumir el operador
            if not self.factor():
                return False
        
        return True
    
    def factor(self) -> bool:
        """FACTOR → NUM | STRING | TRUE | FALSE | ID | ( EXPRESION )"""
        token = self.current_token()
        if not token:
            return False
            
        if token.type in ["NUM", "STRING", "TRUE", "FALSE", "ID"]:
            self.advance()
            return True
        elif token.type == "LPAREN":
            self.advance()  # Consumir (
            if not self.expresion():
                return False
            self.expect("RPAREN", "Se esperaba ')' después de la expresión")
            return True
        else:
            raise SyntaxError(
                f"Se esperaba un valor pero se encontró '{token.type}'",
                token.line,
                token.column,
                "número, cadena, true, false, identificador o '('"
            )
    
    def parametros(self) -> bool:
        """PARAMETROS → [ID (, ID)*] (simplificado)"""
        # Por simplicidad, aceptamos parámetros vacíos o una lista de IDs
        if self.current_token() and self.current_token().type == "ID":
            self.advance()  # Primer ID
            
            while self.current_token() and self.current_token().type == "COMMA":
                self.advance()  # Consumir ,
                self.expect("ID", "Se esperaba identificador después de ','")
        
        return True
    
    def get_resultado(self) -> str:
        """Obtiene el mensaje de resultado del análisis"""
        if not self.errores and not self.current_token():
            return "✅ Análisis sintáctico exitoso: El código es sintácticamente correcto"
        elif self.errores:
            error = self.errores[0]
            return f"❌ Error sintáctico: {error.message}"
        else:
            token = self.current_token()
            return f"❌ Error: Tokens restantes sin procesar: '{token.type if token else 'EOF'}'"
    
    def get_errores(self) -> List[SyntaxError]:
        """Retorna la lista de errores encontrados"""
        return self.errores

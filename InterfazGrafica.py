
from AnalizadorSintactico import AnalizadorSintactico, SyntaxError
import sys
import os
import csv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QTabWidget, QLabel, QFileDialog, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor, QBrush


# Importar tu analizador léxico
from AnalizadorLexico import Lexer, LexerError, Token

class CompilerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador Léxico - Compiladores")
        self.setGeometry(100, 100, 1400, 800)
        
        # Datos
        self.tokens = []
        self.errors = []
        
        self.init_ui()
        
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Barra de herramientas
        self.create_toolbar(main_layout)
        
        # Área de contenido principal
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter, 1)
        
        # Editor de código (izquierda)
        self.create_editor(content_splitter)
        
        # Panel de resultados (derecha)
        self.create_results_panel(content_splitter)
        
        # Configurar proporciones del splitter
        content_splitter.setSizes([700, 700])
        
        # Barra de estado
        self.status_label = QLabel("Listo. Abre un archivo .txt o escribe código para analizar.")
        self.status_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        main_layout.addWidget(self.status_label)
        
    def create_toolbar(self, parent_layout):
        toolbar_layout = QHBoxLayout()
        
        # Botones
        self.btn_open = QPushButton("📁 Abrir .txt")
        self.btn_open.clicked.connect(self.open_file)
        self.btn_open.setStyleSheet(self.get_button_style())
        
        self.btn_analyze = QPushButton("🔍 Analizar Léxico")
        self.btn_analyze.clicked.connect(self.analyze_lexical)
        self.btn_analyze.setStyleSheet(self.get_button_style("#007acc", "white"))

        self.btn_sintactico = QPushButton("📐 Analizar Sintáctico")
        self.btn_sintactico.clicked.connect(self.analyze_sintactico)
        self.btn_sintactico.setStyleSheet(self.get_button_style("#6f42c1", "white"))
        
        self.btn_export_tokens = QPushButton("📊 Exportar Tokens")
        self.btn_export_tokens.clicked.connect(self.export_tokens)
        self.btn_export_tokens.setStyleSheet(self.get_button_style("#28a745", "white"))
        
        self.btn_export_errors = QPushButton("⚠️ Exportar Errores")
        self.btn_export_errors.clicked.connect(self.export_errors)
        self.btn_export_errors.setStyleSheet(self.get_button_style("#ffc107", "black"))
        
        self.btn_clear = QPushButton("🗑️ Limpiar")
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_clear.setStyleSheet(self.get_button_style("#dc3545", "white"))
        
        # Agregar botones al layout
        for btn in [self.btn_open, self.btn_analyze, self.btn_sintactico, 
               self.btn_export_tokens, self.btn_export_errors, self.btn_clear]:
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        parent_layout.addLayout(toolbar_layout)
    
    def analyze_sintactico(self):
        """Ejecuta el análisis sintáctico"""
        if not self.tokens:
            QMessageBox.warning(self, "Advertencia", "Primero ejecuta el análisis léxico")
            return
        
        try:
            # Crear y ejecutar analizador sintáctico
            analizador = AnalizadorSintactico(self.tokens)
            resultado = analizador.parse()
            mensaje = analizador.get_resultado()
            
            # Mostrar resultado
            self.status_label.setText(mensaje)
            
            if resultado:
                QMessageBox.information(self, "Análisis Sintáctico", mensaje)
            else:
                QMessageBox.critical(self, "Error Sintáctico", mensaje)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en análisis sintáctico: {str(e)}")

            
    def get_button_style(self, bg_color="#6c757d", text_color="white"):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(bg_color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(bg_color, 40)};
            }}
        """
    
    def darken_color(self, color, percent=20):
        """Oscurece un color hexadecimal"""
        if color.startswith('#'):
            color = color[1:]
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = max(0, r - (r * percent // 100))
        g = max(0, g - (g * percent // 100))
        b = max(0, b - (b * percent // 100))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def create_editor(self, parent):
        # Frame para el editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Label del editor
        editor_label = QLabel("Editor de Código")
        editor_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        editor_layout.addWidget(editor_label)
        
        # Área de texto
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Escribe tu código aquí...\nO abre un archivo .txt usando el botón 'Abrir .txt'")
        
        # Configurar fuente monoespaciada para código
        font = QFont("Monaco", 12)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_editor.setFont(font)
        
        # Estilo del editor
        self.text_editor.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #000000;  /* ← TEXTO NEGRO AQUÍ */
                border: 2px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Monaco', 'Consolas', monospace;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        
        editor_layout.addWidget(self.text_editor)
        parent.addWidget(editor_widget)
    
    def create_results_panel(self, parent):
        # Widget para resultados
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Label del panel de resultados
        results_label = QLabel("Resultados del Análisis")
        results_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        results_layout.addWidget(results_label)
        
        # Tabs para tokens y errores
        self.tabs = QTabWidget()
        
        # Tabla de tokens
        self.tokens_table = QTableWidget()
        self.tokens_table.setColumnCount(4)
        self.tokens_table.setHorizontalHeaderLabels(["Línea", "Columna", "Tipo", "Lexema"])
        self.tokens_table.horizontalHeader().setStretchLastSection(True)
        self.tokens_table.setSortingEnabled(True)
        self.tabs.addTab(self.tokens_table, "Tokens (0)")
        
        # Tabla de errores
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(3)
        self.errors_table.setHorizontalHeaderLabels(["Línea", "Columna", "Mensaje de Error"])
        self.errors_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.errors_table, "Errores (0)")
        
        # Configurar estilo de las tablas
        table_style = """
           QTableWidget {
            gridline-color: #dee2e6;
            background-color: white;
            color: #000000;  /* ← TEXTO NEGRO PARA TABLAS */
        }
        QTableWidget::item {
            padding: 5px;
            border-bottom: 1px solid #dee2e6;
            color: #000000;  /* ← TEXTO NEGRO PARA ITEMS */
        }
        QHeaderView::section {
            background-color: #007acc;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        """
        self.tokens_table.setStyleSheet(table_style)
        self.errors_table.setStyleSheet(table_style)
        
        results_layout.addWidget(self.tabs)
        parent.addWidget(results_widget)
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Abrir archivo de código fuente", 
            "", 
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.text_editor.setPlainText(content)
                self.status_label.setText(f"Archivo cargado: {os.path.basename(file_path)}")
                
                # Limpiar resultados anteriores
                self.clear_results()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")

    def analyze_lexical(self):
        source_code = self.text_editor.toPlainText().strip()
    
        if not source_code:
            QMessageBox.warning(self, "Advertencia", "El editor está vacío. Escribe algún código o abre un archivo.")
            return
        
        # Limpiar resultados anteriores
        self.clear_results()
        
        try:
            # Ejecutar analizador léxico
            lexer = Lexer(source_code)
            self.tokens = lexer.tokenize()
            
            # Mostrar tokens en la tabla
            self.display_tokens()
            
            # Actualizar estado
            token_count = len([t for t in self.tokens if t.type != "EOF"])
            self.status_label.setText(
                f"Análisis completado exitosamente. {token_count} tokens encontrados."
            )
            
            # Cambiar a pestaña de tokens
            self.tabs.setCurrentIndex(0)
        
        except LexerError as e:
            # Mostrar error léxico específico
            self.errors = [(e.line, e.column, e.msg)]
            self.display_errors()
            
            # Resaltar línea con error en el editor
            self.highlight_error_line(e.line)
            
            # Actualizar estado
            self.status_label.setText(f"Error léxico en Línea {e.line}, Columna {e.column}")
            
            # Cambiar a pestaña de errores
            self.tabs.setCurrentIndex(1)
            
            # Mostrar mensaje informativo
            QMessageBox.warning(self, "Error Léxico", f"Se encontró un error léxico:\n\nLínea {e.line}, Columna {e.column}\n{e.msg}")
            
        except Exception as e:
            # Capturar cualquier otro error inesperado
            error_msg = f"Error inesperado durante el análisis:\n{str(e)}"
            self.status_label.setText("Error durante el análisis")
            
            # Mostrar en tabla de errores
            self.errors = [(1, 1, error_msg)]
            self.display_errors()
            
            # Cambiar a pestaña de errores
            self.tabs.setCurrentIndex(1)
            
            QMessageBox.critical(self, "Error Inesperado", error_msg)


    def display_tokens(self):
        self.tokens_table.setRowCount(len(self.tokens))
        
        for row, token in enumerate(self.tokens):
            # Línea
            self.tokens_table.setItem(row, 0, QTableWidgetItem(str(token.line)))
            
            # Columna
            self.tokens_table.setItem(row, 1, QTableWidgetItem(str(token.column)))
            
            # Tipo
            type_item = QTableWidgetItem(token.type)
            
            # Color según tipo de token
            if token.type in ["ID", "NUM", "STRING"]:
                type_item.setBackground(QBrush(QColor("#e8f5e8")))  # Verde claro
            elif token.type in Lexer.KEYWORDS.values():
                type_item.setBackground(QBrush(QColor("#e3f2fd")))  # Azul claro
            elif token.type in Lexer.OPERATORS.values():
                type_item.setBackground(QBrush(QColor("#fff3e0")))  # Naranja claro
            elif token.type == "EOF":
                type_item.setBackground(QBrush(QColor("#f5f5f5")))  # Gris
            
            self.tokens_table.setItem(row, 2, type_item)
            
            # Lexema (escapar caracteres especiales)
            lexeme_display = token.lexeme.replace('\n', '\\n').replace('\t', '\\t')
            self.tokens_table.setItem(row, 3, QTableWidgetItem(lexeme_display))
        
        # Ajustar columnas
        self.tokens_table.resizeColumnsToContents()
        
        # Actualizar título de la pestaña
        token_count = len([t for t in self.tokens if t.type != "EOF"])
        self.tabs.setTabText(0, f"Tokens ({token_count})")
    
    def display_errors(self):
        self.errors_table.setRowCount(len(self.errors))
        
        for row, (line, column, message) in enumerate(self.errors):
            self.errors_table.setItem(row, 0, QTableWidgetItem(str(line)))
            self.errors_table.setItem(row, 1, QTableWidgetItem(str(column)))
            self.errors_table.setItem(row, 2, QTableWidgetItem(message))
        
        # Ajustar columnas
        self.errors_table.resizeColumnsToContents()
        
        # Actualizar título de la pestaña
        self.tabs.setTabText(1, f"Errores ({len(self.errors)})")
    
    def highlight_error_line(self, line_number):
        try:
            # Convertir el QTextEdit a formato de cursor para resaltar
            cursor = self.text_editor.textCursor()
            
            # Mover al inicio del documento
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            # Mover a la línea específica (las líneas empiezan en 1, pero el cursor en 0)
            for _ in range(max(0, line_number - 1)):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            
            # Seleccionar la línea completa
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            
            # Aplicar formato de resaltado
            format = cursor.charFormat()
            format.setBackground(QColor("#ffebee"))  # Rojo muy claro
            cursor.setCharFormat(format)
            
            # Mover el cursor a la línea con error y centrar la vista
            self.text_editor.setTextCursor(cursor)
            self.text_editor.centerCursor()
            
        except Exception as e:
            print(f"Error al resaltar línea: {e}")  # Para debugging
    
    def export_tokens(self):
        if not self.tokens:
            QMessageBox.information(self, "Exportar", "No hay tokens para exportar. Ejecuta el análisis léxico primero.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar tokens a CSV",
            "tokens.csv",
            "Archivos CSV (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["line", "column", "type", "lexeme"])
                    for token in self.tokens:
                        writer.writerow([token.line, token.column, token.type, token.lexeme])
                
                self.status_label.setText(f"Tokens exportados exitosamente: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Éxito", f"Tokens exportados a:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudieron exportar los tokens:\n{str(e)}")
    
    def export_errors(self):
        if not self.errors:
            QMessageBox.information(self, "Exportar", "No hay errores para exportar.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar errores a CSV",
            "errores.csv",
            "Archivos CSV (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["line", "column", "message"])
                    for error in self.errors:
                        writer.writerow([error[0], error[1], error[2]])
                
                self.status_label.setText(f"Errores exportados exitosamente: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Éxito", f"Errores exportados a:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudieron exportar los errores:\n{str(e)}")
    def clear_results(self):
        """Limpiar todas las tablas y datos"""
        try:
            self.tokens_table.setRowCount(0)
            self.errors_table.setRowCount(0)
            self.tokens.clear()
            self.errors.clear()
            
            # Actualizar títulos de pestañas
            self.tabs.setTabText(0, "Tokens (0)")
            self.tabs.setTabText(1, "Errores (0)")
            
            # Limpiar resaltados del editor
            cursor = self.text_editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            format = cursor.charFormat()
            format.setBackground(QColor("#ffffff"))
            cursor.setCharFormat(format)
            cursor.clearSelection()
        
        except Exception as e:
            print(f"Error al limpiar resultados: {e}")

            
    def clear_all(self):
        """Limpiar completamente el editor y resultados"""
        self.text_editor.clear()
        self.clear_results()
        self.status_label.setText("Listo. Abre un archivo .txt o escribe código para analizar.")

def main():
    app = QApplication(sys.argv)
    
    # Estilo de aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = CompilerGUI()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

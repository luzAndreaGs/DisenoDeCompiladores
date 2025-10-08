import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from AnalizadorLexico import Lexer, LexerError

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador Léxico — GUI")
        self.geometry("1100x640")

        # --- Top bar ---
        bar = ttk.Frame(self)
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="Abrir .txt", command=self.open_file).pack(side="left", padx=4, pady=4)
        ttk.Button(bar, text="Analizar léxico", command=self.run_lex).pack(side="left", padx=4)
        ttk.Button(bar, text="Exportar tokens.csv", command=self.export_tokens).pack(side="left", padx=4)
        ttk.Button(bar, text="Exportar errores.csv", command=self.export_errors).pack(side="left", padx=4)

        # --- Editor (izquierda) ---
        left = ttk.Frame(self)
        left.pack(side="left", fill="both", expand=True)
        self.text = tk.Text(left, wrap="none", undo=True)
        self.text.pack(side="left", fill="both", expand=True)
        # scrollbars
        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.text.yview)
        yscroll.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=yscroll.set)

        # --- Panel derecho con tabs ---
        right = ttk.Notebook(self)
        right.pack(side="right", fill="both", expand=True)

        # Tabla de tokens
        self.tokens_tab = ttk.Frame(right)
        self.tokens_table = ttk.Treeview(self.tokens_tab, columns=("line","col","type","lexeme"), show="headings")
        for c, w in (("line",70), ("col",70), ("type",130), ("lexeme",420)):
            self.tokens_table.heading(c, text=c.upper())
            self.tokens_table.column(c, width=w, anchor="center" if c in ("line","col","type") else "w")
        self.tokens_table.pack(fill="both", expand=True)
        right.add(self.tokens_tab, text="Tokens")

        # Tabla de errores
        self.errors_tab = ttk.Frame(right)
        self.errors_table = ttk.Treeview(self.errors_tab, columns=("line","col","message"), show="headings")
        for c, w in (("line",70), ("col",70), ("message",500)):
            self.errors_table.heading(c, text=c.upper())
            self.errors_table.column(c, width=w, anchor="center" if c in ("line","col") else "w")
        self.errors_table.pack(fill="both", expand=True)
        right.add(self.errors_tab, text="Errores")

        # Estado
        self.status = tk.StringVar(value="Listo.")
        ttk.Label(self, textvariable=self.status, anchor="w").pack(side="bottom", fill="x")

        # Datos en memoria para exportar
        self._tokens = []
        self._errors = []

        # Estilo para resaltar errores en el editor
        self.text.tag_configure("err", background="#ffe6e6")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files","*.txt"), ("All files","*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        self.text.delete("1.0", "end")
        self.text.insert("1.0", data)
        self.status.set(f"Abierto: {path}")

    def run_lex(self):
        # limpiar tablas y resaltados
        self.tokens_table.delete(*self.tokens_table.get_children())
        self.errors_table.delete(*self.errors_table.get_children())
        self._tokens.clear()
        self._errors.clear()
        self.text.tag_remove("err", "1.0", "end")

        src = self.text.get("1.0", "end-1c")
        try:
            lx = Lexer(src)
            tokens = lx.tokenize()

            # cargar tokens
            for t in tokens:
                disp = t.lexeme.replace("\n", "\\n")
                self.tokens_table.insert("", "end", values=(t.line, t.column, t.type, disp))
            self._tokens = tokens
            self.status.set(f"Análisis correcto. {len(tokens)} tokens (incluye EOF).")

        except LexerError as e:
            # tabla de errores
            self.errors_table.insert("", "end", values=(e.line, e.column, e.msg))
            self._errors = [(e.line, e.column, e.msg)]
            self.status.set(f"Error léxico en L{e.line},C{e.column}")

            # intenta resaltar la línea del error
            try:
                line_idx = f"{e.line}.0"
                line_end = f"{e.line}.end"
                self.text.tag_add("err", line_idx, line_end)
                self.text.see(line_idx)
            except Exception:
                pass

    def export_tokens(self):
        if not self._tokens:
            messagebox.showwarning("Exportar tokens", "No hay tokens para exportar. Ejecuta 'Analizar léxico' primero.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tokens.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as cf:
            w = csv.writer(cf)
            w.writerow(["line","column","type","lexeme"])
            for t in self._tokens:
                w.writerow([t.line, t.column, t.type, t.lexeme])
        self.status.set(f"tokens.csv exportado en: {path}")

    def export_errors(self):
        if not self._errors:
            messagebox.showinfo("Exportar errores", "No hay errores para exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="errores.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as ef:
            w = csv.writer(ef)
            w.writerow(["line","column","message"])
            for line, col, msg in self._errors:
                w.writerow([line, col, msg])
        self.status.set(f"errores.csv exportado en: {path}")

if __name__ == "__main__":
    App().mainloop()
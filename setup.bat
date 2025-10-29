@echo off
echo 🔧 Configurando el proyecto de Compiladores...

echo 📦 Creando entorno virtual...
python -m venv venv

echo 🚀 Activando entorno virtual...
venv\Scripts\activate

echo 📚 Instalando dependencias...
pip install -r requirements.txt

echo ✅ ¡Configuración completada!
echo Para ejecutar: python InterfazCompiladores.py
echo Para activar el entorno virtual después: venv\Scripts\activate

"""
main.py — Punto de entrada de Mining Manager
Uso: .venv\Scripts\python main.py
"""
import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from miner_app.ui.app import MiningManagerApp


def main():
    app = MiningManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

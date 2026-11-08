"""Demo: the visual identity guide (moved to scripts/identity_board.py).

    python demo_palettes.py <out_dir>          # every identity page + overview + topic board
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(os.path.dirname(HERE), 'scripts', 'identity_board.py')

if __name__ == '__main__':
    subprocess.run([sys.executable, BOARD, '--all', sys.argv[-1]], check=True)

# descrição:        ficheiro principal do jogo.
# autor:            Luís Pereira (18446), Paulo Machado (23484)
# criado a:         4-12-2022
# modificado a:     4-12-2022


import tkinter as tk
from Game import Game

root = tk.Tk()
root.title('Break Those Bricks')

game = Game(root)
game.mainloop()

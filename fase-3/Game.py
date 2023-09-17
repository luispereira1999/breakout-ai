# descrição:        classe responsável pelo jogo (elementos, eventos, UI, etc.).
# autor:            Luís Pereira (18446), Paulo Machado (23484)
# criado a:         9-12-2022
# modificado a:     9-12-2022


import tkinter as tk
from FaceDetection import FaceDetection, Part_Of_Screen


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = 5
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, root):
        super(Game, self).__init__(root)
        self.root = root

        self.text_title = None
        self.text_subtitle = None
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        # adding brick with different hit capacities - 3,2 and 1
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None

        # iniciar deteção de movimentos em simultâneo com o jogo
        self.face_detection_thread = FaceDetection()
        self.face_detection_thread.start()

        self.root.protocol('WM_DELETE_WINDOW', self.click_in_close_game_window)

        # self.setup_new_game()
        self.text_title = self.draw_text(300, 180, 'Iniciar Jogo!')
        self.text_subtitle = self.draw_text(300, 230, 'Clique na Câmara')

        self.canvas.focus_set()

        while not self.face_detection_thread.is_start:
            if self.face_detection_thread.is_finish:
                self.click_in_close_game_window()
                break

            # permitir que seja mostrar a tela de jogo
            self.root.update()

        # iniciar jogo após clicar na câmara
        if not self.face_detection_thread.is_finish:
            self.setup_game()

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.start_game()

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()

        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='28'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.delete(self.text_title)
        self.canvas.delete(self.text_subtitle)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        if self.face_detection_thread.is_finish:
            self.click_in_close_game_window()
            return

        part_of_screen = self.face_detection_thread.part_of_screen

        if part_of_screen == Part_Of_Screen.LEFT:
            self.paddle.move(-10)
        elif part_of_screen == Part_Of_Screen.RIGHT:
            self.paddle.move(10)
        else:
            self.paddle.move(0)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.text_title = self.draw_text(300, 200, 'Ganhaste!')
            self.click_in_close_game_window()
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.text_title = self.draw_text(300, 200, 'Perdeste!')
                self.click_in_close_game_window()
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

    def click_in_close_game_window(self):
        # se o thread já foi encerrado, fechar apenas a janela do jogo
        if not self.face_detection_thread.is_alive():
            self.close_game_window()
            return

        self.face_detection_thread.is_finish = True
        self.face_detection_thread.join()

    def close_game_window(self):
        self.root.destroy()

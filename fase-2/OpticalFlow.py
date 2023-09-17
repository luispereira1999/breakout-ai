# descrição:        classe responsável pelo optical flow da transmissão de vídeo (câmara) do computador,
#                   para assim manipular o paddle do jogo através da deteção de movimentos.
# autor:            Luís Pereira (18446), Paulo Machado (23484)
# criado a:         25-11-2022
# modificado a:     30-11-2022


import cv2 as cv
import numpy as np
from threading import Thread
from enum import Enum


class OpticalFlow(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.is_start = False
        self.is_finish = False

        self.old_frame = None
        self.new_frame = None
        self.old_frame_prepared = None
        self.new_frame_prepared = None

        self.movement_sensibility = 25000
        self.part_of_screen = None

    # função pertencente à classe Thread, chamada quando o thread é iniciado
    def run(self):
        # criar janela
        cv.namedWindow('Camera')

        # criar trackbar
        cv.createTrackbar('Sensibilidade', 'Camera', self.movement_sensibility, 100000,
                          self.onTrackbarChange)

        # rendezirar câmara
        camera = cv.VideoCapture(0)

        # evento de clicar na câmara com o mouse
        cv.setMouseCallback('Camera', self.click_in_camera_and_start_game)

        while True:
            # se o jogo ainda não iniciou, mostrar apenas a câmara
            if not self.is_start:
                # obter primeira frame (como é a primeira será a antiga)
                ret, self.old_frame = camera.read()
                self.old_frame = self.old_frame[:, ::-1, :]

                # preparar frame para efetuar a deteção de movimentos
                self.old_frame_prepared = self.prepare_frame(self.old_frame)

                cv.imshow('Camera', self.old_frame)
            else:
                # obter frame nova
                ret, self.new_frame = camera.read()
                self.new_frame = self.new_frame[:, ::-1, :]

                # preparar frame para efetuar a deteção de movimentos
                self.new_frame_prepared = self.prepare_frame(self.new_frame)

                # fazer deteção de movimentos só quando o jogo iniciar
                self.detect_movement()

                cv.imshow('Camera', self.new_frame)

            # fazer loop a cada 30 milésimos
            cv.waitKey(30)

            # fechar janela da câmara quando o utilizador clica no botão de fechar a janela da câmara
            if cv.getWindowProperty('Camera', cv.WND_PROP_VISIBLE) < 1 or self.is_finish:
                break

        # conclui a transmissão do vídeo
        camera.release()

        # fecha todas as janelas
        cv.destroyAllWindows()

        self.is_finish = True

    def click_in_camera_and_start_game(self, event, x, y, flags, param):
        # sai da função, quando o utilizador clica na câmara e o jogo já está em andamento
        if self.is_start:
            return

        if event == cv.EVENT_LBUTTONUP:
            # iniciar jogo
            self.is_start = True

    def onTrackbarChange(self, x):
        # obter valor atual da trackbar
        self.movement_sensibility = int(cv.getTrackbarPos('Sensibilidade', 'Camera'))

    # preparar cada frame para o cálculo da deteção de movimentos
    def prepare_frame(self, frame):
        # converter para grayscale
        prepared_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # usar um filtro gaussiano para remover ruído da imagem
        prepared_frame = cv.GaussianBlur(prepared_frame, (9, 9), 0)

        return prepared_frame

    def detect_movement(self):
        # aplicar método de farneback para calcular o flow dos movimentos detetados na câmara
        # (os parâmetros usados são os padrão do OpenCV)
        flow = cv.calcOpticalFlowFarneback(prev=self.old_frame_prepared, next=self.new_frame_prepared,
                                           flow=None, pyr_scale=0.5, levels=3, winsize=15,
                                           iterations=3, poly_n=5, poly_sigma=1.2, flags=0)

        # obter a matriz dos vetores de movimento no eixo x
        flow_x = flow[:, :, 0]

        # obter o valor da direção total dos pixeis,
        # se o valor for negativo significa que foi para a esquerda e positivo para a direita
        flow_x_diretion = np.sum(flow_x)

        # verificar o lado da direção do movimento para atualizar o paddle do jogo,
        # a sensibilidade permite ao jogador decidir se quer muito ou pouco que os movimentos sejam identificados
        if flow_x_diretion < -self.movement_sensibility:
            self.part_of_screen = Part_Of_Screen.LEFT
        elif flow_x_diretion > self.movement_sensibility:
            self.part_of_screen = Part_Of_Screen.RIGHT
        else:
            self.part_of_screen = Part_Of_Screen.NONE

        self.old_frame_prepared = self.new_frame_prepared

        return


class Part_Of_Screen(Enum):
    NONE = 0,
    LEFT = 1,
    RIGHT = 2

# descrição:        classe responsável pela deteção de faces da transmissão de vídeo (câmara) do computador,
#                   para assim manipular o paddle do jogo através dessa deteção.
# autor:            Luís Pereira (18446), Paulo Machado (23484)
# criado a:         10-12-2022
# modificado a:     10-12-2022


import cv2 as cv
import numpy as np
from threading import Thread
from enum import Enum


class FaceDetection(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.is_start = False
        self.is_finish = False

        self.frame = None
        self.part_of_screen = None

    # função pertencente à classe Thread, chamada quando o thread é iniciado
    def run(self):
        # criar janela
        cv.namedWindow('Camera')

        # rendezirar câmara
        camera = cv.VideoCapture(0)

        # evento de clicar na câmara com o mouse
        cv.setMouseCallback('Camera', self.click_in_camera_and_start_game)

        # modelo pré-treinado de viola-jones disponibilizado pelo OpenCV
        haarcascade_path = './models/haarcascade_frontalface_default.xml'

        # criar o classificador para aplicar o modelo
        face_cascade = cv.CascadeClassifier(haarcascade_path)

        while True:
            # se o jogo ainda não iniciou, mostrar apenas a câmara
            if not self.is_start:
                # obter frame
                ret, self.frame = camera.read()
                self.frame = self.frame[:, ::-1, :]

                # mostrar frame
                cv.imshow('Camera', self.frame)
            else:
                # obter frame
                ret, self.frame = camera.read()
                self.frame = self.frame[:, ::-1, :]

                # preparar frame para efetuar a deteção de faces
                frame_prepared = self.prepare_frame(self.frame)

                # fazer deteção de faces só quando o jogo iniciar
                image_faces = self.detect_face(frame_prepared, face_cascade)

                # mostrar frame com face detetada
                cv.imshow('Camera', image_faces)

            # fazer loop a cada 1 milésimos
            cv.waitKey(1)

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

    # preparar cada frame para cada deteção de faces
    def prepare_frame(self, frame):
        # converter para grayscale
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        return frame_gray

    def detect_face(self, frame_prepared, face_cascade):
        # lista de todos os retângulos das faces detetadas na frame
        faces = face_cascade.detectMultiScale(frame_prepared)
        image_faces = self.frame.copy()

        # quantidade de faces detetadas
        faces_count = len(faces)

        # se não existem faces, não é necessário fazer mais nada
        if faces_count > 0:
            # obter o retângulo da maior face detetada
            (x, y, w, h) = self.find_biggest_rectangle(faces)
            (center_x, center_y) = self.get_rectangle_center(x, y, w, h)

            # criar elipse à volta da face
            image_face = cv.ellipse(image_faces, (center_x, center_y), (w // 2, h // 2), 0, 0, 360, (0, 0, 255), 4)

            # verificar se existe um valor válido para o centro da face,
            # dado que se existir o centro da face, podemos considerar que a face também existe
            if center_x != -1:
                # descobrir em que lado da tela está a face
                self.part_of_screen = self.find_screen_side_belongs(center_x)

            return image_face
        else:
            return image_faces

    def find_biggest_rectangle(self, rectangles):
        max_area = 0
        biggest_rectangle = None

        for (x, y, w, h) in rectangles:
            current_area = w * h

            if current_area > max_area:
                max_area = len(rectangles)
                biggest_rectangle = (x, y, w, h)

        return biggest_rectangle

    def get_rectangle_center(self, x, y, w, h):
        return x + w // 2, y + h // 2

    def get_screen_width(self, frame):
        return frame.shape[1]

    def get_screen_center_x(self, frame_width):
        return frame_width / 2

    def find_screen_side_belongs(self, x):
        # obter a largura da tela e o centro dela no eixo x
        frame_width = self.get_screen_width(self.frame)
        frame_center_x = self.get_screen_center_x(frame_width)

        belongs_to_left = 0 <= x <= frame_center_x
        belongs_to_right = frame_center_x <= x <= frame_width

        part_of_screen = Part_Of_Screen.NONE

        # guardar em que parte da tela encontra-se o valor de x
        if belongs_to_left:
            part_of_screen = Part_Of_Screen.LEFT
        elif belongs_to_right:
            part_of_screen = Part_Of_Screen.RIGHT

        return part_of_screen


class Part_Of_Screen(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2

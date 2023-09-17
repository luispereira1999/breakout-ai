# descrição:        classe responsável pelo segmentação da transmissão de vídeo (câmera) do computadordo,
#                   para assim manipular o paddle do jogo através da deteção de cor de um determinado objeto.
# autor:            Luís Pereira (18446), Paulo Machado (23484)
# criado a:         5-11-2022
# modificado a:     14-11-2022


import cv2 as cv
import numpy as np
from threading import Thread
from enum import Enum


class Segmentation(Thread):
    def __init__(self):
        Thread.__init__(self)

        # variáveis para os valores das trackbars
        # nota: no opencv as escalas para H|SV são respetivamente: 0-179 | 0-255 | 0-255
        self.h_min = 0
        self.h_max = 179
        self.s_min = 0
        self.s_max = 255
        self.v_min = 0
        self.v_max = 255

        self.is_start = False
        self.is_finish = False

        self.image_original = None
        self.image_hsv = None
        self.part_of_screen = None

    # função pertencente à classe Thread, chamada quando o thread é iniciado
    def run(self):
        # criar janelas
        cv.namedWindow('Camera')

        # rendezirar câmera
        camera = cv.VideoCapture()

        cv.setMouseCallback('Camera', self.click_in_camera_and_start_game)

        while True:
            if not camera.isOpened():
                camera.open(0)

            # obter frame atual
            ret, self.image_original = camera.read()
            self.image_original = self.image_original[:, ::-1, :]

            # usar um filtro gaussiano para remover ruído da imagem
            image_blur = cv.GaussianBlur(self.image_original, (9, 9), 0)

            # converter imagem para HSV
            self.image_hsv = cv.cvtColor(image_blur, cv.COLOR_BGR2HSV)

            # se o jogo ainda não iniciou, mostrar apenas a câmara
            if not self.is_start:
                cv.imshow('Camera', self.image_original)
            else:
                # fazer segmentação só quando o jogo iniciar
                image_segmented = self.segment()
                cv.imshow('Camera', image_segmented)

            # fazer loop a cada 1 milésimo
            cv.waitKey(1)

            # fechar janela da câmera quando o utilizador clica no botão de fechar a janela da câmera
            if cv.getWindowProperty('Camera', cv.WND_PROP_VISIBLE) < 1 or self.is_finish:
                break

        # conclui a transmissão do vídeo
        camera.release()

        # fecha todas as janelas
        cv.destroyAllWindows()

        self.is_finish = True

    def click_in_camera_and_start_game(self, event, x, y, flags, param):
        # sai da função, quando o utilizador clica na câmera e o jogo já em andamento
        if self.is_start:
            return

        if event == cv.EVENT_LBUTTONUP:
            # obter o pixel clicado na câmera
            pixel_hsv_clicked = self.image_hsv[y, x]

            # definir thresholds
            self.h_min = pixel_hsv_clicked[0] - 25
            self.h_max = pixel_hsv_clicked[0] + 25
            self.s_min = pixel_hsv_clicked[1] - 25
            self.s_max = pixel_hsv_clicked[1] + 25
            self.v_min = pixel_hsv_clicked[2] - 25
            self.v_max = pixel_hsv_clicked[2] + 25

            # prevenir que os valores mínimos e máximos não ultrapassem as escalas do openCV para HSV
            if self.h_min < 0:
                self.h_min = 0
            if self.s_min < 0:
                self.s_min = 0
            if self.v_min < 0:
                self.v_min = 0

            if self.h_min > 179:
                self.h_min = 179
            if self.s_min > 255:
                self.s_min = 255
            if self.v_min > 255:
                self.v_min = 255

            # iniciar jogo
            self.is_start = True

    def segment(self):
        # obter os tresholds mínimos e máximos,
        # as escalas HSV utilizadas pelo opencv são: H (0-179) | S (0-255) | V (0-255)
        image_hsv_min = np.array([self.h_min, self.s_min, self.v_min], np.uint8)
        image_hsv_max = np.array([self.h_max, self.s_max, self.v_max], np.uint8)

        # obter os pixeis que fazem parte da junção dos tresholds mínimos e máximos,
        # se pertencer fica a 255 senão fica a 0
        image_mask = cv.inRange(self.image_hsv, image_hsv_min, image_hsv_max)

        # obter todos os contornos externos
        contours, hierarchy = cv.findContours(image_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # fazer uma cópia da imagem original,
        # pelo facto de o drawContours modifica a imagem de entrada
        image_original_copy = self.image_original.copy()

        # se existir contornos
        if len(contours) > 0:
            # obter o maior contorno
            biggest_contour_index = self.find_biggest_contour(contours)

            # desenhar contorno
            cv.drawContours(image=image_original_copy, contours=contours, contourIdx=biggest_contour_index,
                            color=(0, 255, 0), thickness=-1)

            # obter o pixel central do contorno
            contour_center_x, contour_center_y = self.get_center_of_mass(contours[biggest_contour_index])

            # verificar se existe um valor válido para o centro do objeto,
            # uma vez que se existir o centro do objeto, podemos considerar que o objeto também existe
            if contour_center_x != -1:
                # descobrir em que lado está o objeto
                self.part_of_screen = self.find_side_of_screen_belongs(contour_center_x)

        return image_original_copy

    def find_biggest_contour(self, contours):
        max_area = 0
        biggest_contour_index = -1

        for i in range(len(contours)):
            current_area = cv.contourArea(contours[i])

            if current_area > max_area:
                max_area = len(contours[i])
                biggest_contour_index = i

        return biggest_contour_index

    def get_center_of_mass(self, contour):
        moment = cv.moments(contour)
        center_x = -1
        center_y = -1

        # prevenir divisões por 0
        if int(moment['m00']) != 0:
            center_x = int(moment['m10'] / moment['m00'])
            center_y = int(moment['m01'] / moment['m00'])

        return center_x, center_y

    def find_side_of_screen_belongs(self, contour_center_x):
        # obter a largura da tela e o centro no eixo x
        frame_width = self.get_width()
        frame_center_x = self.get_center_x(frame_width)

        belongs_to_left = 0 <= contour_center_x <= frame_width / 2 - 20
        belongs_to_middle = frame_center_x - 20 <= contour_center_x <= frame_center_x + 20
        belongs_to_right = frame_center_x + 20 <= contour_center_x <= frame_width

        part_of_screen = None

        # guardar em que parte da tela encontra-se o objeto,
        # para depois manipular a posição do paddle do jogo
        if belongs_to_left:
            part_of_screen = Part_Of_Screen.LEFT
        elif belongs_to_middle:
            part_of_screen = Part_Of_Screen.MIDDLE
        elif belongs_to_right:
            part_of_screen = Part_Of_Screen.RIGHT

        return part_of_screen

    def get_width(self):
        return self.image_hsv.shape[1]

    def get_center_x(self, frame_width):
        return frame_width / 2


class Part_Of_Screen(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2

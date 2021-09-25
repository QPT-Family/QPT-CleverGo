# -*- coding: utf-8 -*-
# @Time    : 2021/9/25 20:45
# @Author  : He Ruizhi
# @File    : button.py
# @Software: PyCharm

import pygame
import numpy as np


def say_hello():
    print('Hello!')


class Button:
    def __init__(self, screen, text, pos, call_function=say_hello, text_color=(0, 0, 0), font_size=14, size=(87, 27),
                 up_color=(225, 225, 225), down_color=(190, 190, 190), outer_edge_color=(240, 240, 240),
                 inner_edge_color=(173, 173, 173), base_coordinate=(0, 0)):
        self.screen = screen  # 按钮绘制屏幕
        self.text = text  # 按钮上的字
        if isinstance(pos, int) or isinstance(pos, float):  # 按钮绘制的位置
            self.pos = pos
        else:
            self.pos = np.copy(pos)
        self.call_function = call_function  # 鼠标被点击调用的函数
        self.text_color = text_color  # 按钮文字颜色
        self.font_size = font_size  # 按钮字体大小
        self.size = size  # 按钮的大小
        self.up_color = up_color  # 按钮没被点击时的底色
        self.down_color = down_color  # 按钮被点击时的颜色
        self.outer_edge_color = outer_edge_color  # 按钮外边框颜色
        self.inner_edge_color = inner_edge_color  # 按钮内边框颜色
        self.base_coordinate = base_coordinate  # 按钮所在屏幕相对于主屏幕的偏移量，用于确定按钮相对于主屏幕位置
        self.font = pygame.font.Font('assets/fonts/msyh.ttc', font_size)
        self.is_down = False  # 鼠标是否已被按下

    def draw_up(self):
        """
        没被鼠标点击的按钮的绘制方法
        :return:
        """
        return self.draw(self.up_color)

    def draw_down(self):
        """
        被鼠标点击时的按钮绘制方法
        :return:
        """
        return self.draw(self.down_color)

    def draw(self, base_color):
        if isinstance(self.pos, int) or isinstance(self.pos, float):
            self.pos = (self.screen.get_width() - self.size[0]) / 2, self.pos
        base_rect = self.pos[0], self.pos[1], self.size[0], self.size[1]  # 计算按钮的绘制区域
        inner_rect = base_rect[0] + 1, base_rect[1] + 1, base_rect[2] - 2, base_rect[3] - 2  # 内框绘制区域
        pygame.draw.rect(self.screen, base_color, base_rect)  # 绘制按钮底图
        pygame.draw.rect(self.screen, self.outer_edge_color, base_rect, width=1)  # 绘制外框
        pygame.draw.rect(self.screen, self.inner_edge_color, inner_rect, width=1)  # 绘制内框
        # 绘制文字
        button_text = self.font.render(self.text, True, self.text_color)
        # 计算文字绘制位置：按钮正中央
        text_pos = (self.size[0] - button_text.get_width()) / 2 + self.pos[0], \
                   (self.size[1] - button_text.get_height()) / 2 + self.pos[1]
        self.screen.blit(button_text, text_pos)
        return base_rect[0] + self.base_coordinate[0], base_rect[1] + self.base_coordinate[1], base_rect[2], base_rect[3]

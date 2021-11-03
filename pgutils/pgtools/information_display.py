# -*- coding: utf-8 -*-
# @Time    : 2021/10/8 12:44
# @Author  : He Ruizhi
# @File    : text.py
# @Software: PyCharm

import os
import pygame
from collections import deque
from typing import List, Tuple, Optional
from pgutils.text import draw_text
from pgutils.pgtools.toolbase import ToolBase

current_path = os.path.dirname(__file__)


class InformationDisplay(ToolBase):
    def __init__(self, surface: pygame.Surface,
                 display_pos: Optional[List[str or float or int]] = None,
                 display_size: Optional[List[int or float]] = None,
                 max_show: int = 5,
                 bg_color: Tuple[int, int, int] = (165, 219, 214),
                 outer_rect_color: Tuple[int, int, int] = (240, 240, 240),
                 inner_rect_color: Tuple[int, int, int] = (173, 173, 173),
                 font_size: int = 14,
                 font_color: Tuple[int, int, int] = (0, 0, 0),
                 font_path: str = current_path + "/../../assets/fonts/msyh.ttc"):
        """
        在指定pygame.surface上滚动显示信息

        :param surface: 绘制屏幕
        :param display_pos: 绘制位置
        :param display_size: display大小
        :param max_show: 信息滚动显示数
        :param bg_color: 背景颜色
        :param font_size: 字体大小
        :param font_color: 字体颜色
        :param font_path: 字体文件路径
        """
        super(InformationDisplay, self).__init__()
        if display_pos is None:
            display_pos = [20, 20]
        if display_size is None:
            surface_width, surface_height = surface.get_width(), surface.get_height()
            display_size = [surface_width - display_pos[0] * 2, surface_height - display_pos[1] * 2]

        # 创建subsurface
        self.display_surface = surface.subsurface((*display_pos, *display_size))
        # 内外边框绘制位置
        self.outer_rect = 0, 0, self.display_surface.get_width(), self.display_surface.get_height()
        self.inner_rect = self.outer_rect[0] + 1, self.outer_rect[1] + 1, self.outer_rect[2] - 2, self.outer_rect[3] - 2

        # 生成字体对象
        self.font = pygame.font.Font(font_path, font_size)
        # 生成信息存储器
        self.information_container = deque(maxlen=max_show)

        self.display_pos = display_pos
        self.display_size = display_size
        self.bg_color = bg_color
        self.font_color = font_color
        self.outer_rect_color = outer_rect_color
        self.inner_rect_color = inner_rect_color

    def push_text(self, text: str, update=False):
        self.information_container.append(text)
        if update:
            self.enable()

    def update(self):
        self.display_surface.fill(self.bg_color)
        # 绘制外框
        pygame.draw.rect(self.display_surface, self.outer_rect_color, self.outer_rect, width=1)
        # 绘制内框
        pygame.draw.rect(self.display_surface, self.inner_rect_color, self.inner_rect, width=1)

        # 绘制文本
        next_pos = [3, 2]
        for line in self.information_container:
            line = self.font.render(line, True, self.font_color)
            next_pos = draw_text(self.display_surface, line, next_pos)


if __name__ == "__main__":
    import time

    # 功能测试
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("测试")

    info_display = InformationDisplay(screen)
    for i in range(10):
        pygame.event.pump()
        info_display.push_text("测试消息：{}".format(i))
        info_display.update()
        pygame.display.update()
        time.sleep(1)
    while True:
        for event in pygame.event.get():
            pass

# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 11:44
# @Author  : He Ruizhi
# @File    : text.py
# @Software: PyCharm

import pygame
from typing import List, Tuple, Union, Iterable
import os

current_path = os.path.dirname(__file__)


def draw_text(surface: pygame.Surface,
              text: Union[str, pygame.Surface],
              pos: Union[List[str or float or int], Tuple[str or float or int]],
              font_size: int = 48,
              font_color: Union[Tuple[int], List[int]] = (255, 255, 255),
              font_path: str = current_path + "/../../assets/fonts/msyh.ttc",
              next_bias: Union[Tuple[int or float], List[int or float]] = (0, 0)) -> Tuple:
    """
    在指定pygame.surface上绘制文字的方法

    :param surface: 绘制文本的pygame.surface
    :param text: 文本内容
    :param pos: 文本绘制位置
    :param font_size: 字体大小
    :param font_color: 字体颜色
    :param font_path:
    :param next_bias: 下一行文本位置偏移
    :return: 下一行文本绘制位置
    """
    # 创建pygame.font.Font对象
    if isinstance(text, str):
        font = pygame.font.Font(font_path, font_size)
        text = font.render(text, True, font_color)

    pos = list(pos)
    if isinstance(pos[0], str):
        assert pos[0] == "center"
        pos[0] = (surface.get_width() - text.get_width()) / 2
    if isinstance(pos[1], str):
        assert pos[1] == "center"
        pos[1] = (surface.get_height() - text.get_height()) / 2

    surface.blit(text, pos)

    return pos[0] + next_bias[0], pos[1] + text.get_height() + next_bias[1]


if __name__ == "__main__":
    # 功能测试
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("测试")

    draw_text(screen, 'Hello!', ["center", "center"])
    pygame.display.update()
    while True:
        for event in pygame.event.get():
            pass

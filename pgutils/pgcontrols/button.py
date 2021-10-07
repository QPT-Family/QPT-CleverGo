# -*- coding: utf-8 -*-
# @Time    : 2021/9/25 20:45
# @Author  : He Ruizhi
# @File    : button.py
# @Software: PyCharm

import pygame
import os
from pgutils.pgtools.text import draw_text
from pgutils.pgcontrols.ctbase import CtBase
from typing import Tuple, List, Union, Callable, Optional

current_path = os.path.dirname(__file__)


class Button(CtBase):
    """每一个Button均为一个pygame.surface.subsurface"""
    def __init__(self, surface: pygame.Surface,
                 text: str,
                 pos: Union[Tuple[str or int], List[str or int]],
                 call_function: Optional[Callable] = None,
                 click_sound: Union[str, pygame.mixer.Sound] = current_path + "/../../assets/audios/Button.wav",
                 font_size: int = 14,
                 size: Union[Tuple[int], List[int]] = (87, 27),
                 text_color: Union[Tuple[int], List[int]] = (0, 0, 0),
                 up_color: Union[Tuple[int], List[int]] = (225, 225, 225),
                 down_color: Union[Tuple[int], List[int]] = (190, 190, 190),
                 outer_edge_color: Union[Tuple[int], List[int]] = (240, 240, 240),
                 inner_edge_color: Union[Tuple[int], List[int]] = (173, 173, 173)):
        """
        pygame按钮控件，用于在给定pygame.surface上绘制一个按钮

        :param surface: 绘制按钮的pygame.surface
        :param text: 按钮上的文本
        :param pos: 按钮绘制位置
        :param call_function: 点击按钮调用的方法
        :param click_sound: 按钮的点击音效
        :param text_color: 按钮上的文本颜色
        :param font_size: 文本大小
        :param size: 按钮大小
        :param up_color: 按钮弹起时的颜色
        :param down_color: 按钮按下时的颜色
        :param outer_edge_color: 按钮外边框颜色
        :param inner_edge_color: 按钮内边框颜色
        """
        super(Button, self).__init__()

        pos = list(pos)
        if isinstance(pos[0], str):
            assert pos[0] == "center"
            pos[0] = (surface.get_width() - size[0]) // 2
        if isinstance(pos[1], str):
            assert pos[1] == "center"
            pos[1] = (surface.get_height() - size[1]) // 2
        if isinstance(click_sound, str):
            click_sound = pygame.mixer.Sound(click_sound)

        # 按钮surface
        self.button_surface = surface.subsurface(pos[0], pos[1], size[0], size[1])
        # 外边框
        self.outer_rect = 0, 0, size[0], size[1]
        # 内边框
        self.inner_rect = self.outer_rect[0] + 1, self.outer_rect[1] + 1, self.outer_rect[2] - 2, self.outer_rect[3] - 2

        self.text = text
        self.call_function = call_function
        self.click_sound = click_sound
        self.text_color = text_color
        self.font_size = font_size
        self.size = size
        self.up_color = up_color
        self.down_color = down_color
        self.outer_edge_color = outer_edge_color
        self.inner_edge_color = inner_edge_color
        # 按钮是否被按下
        self.is_down = False

    def draw_up(self) -> None:
        """绘制未被点击的按钮"""
        self.is_down = False
        self.draw(self.up_color)
        return None

    def draw_down(self) -> None:
        """绘制已被点击的按钮"""
        self.is_down = True
        self.draw(self.down_color)
        return None

    def draw(self, base_color: Union[Tuple[int], List[int]]) -> None:
        """根据传入的颜色，对按钮显示效果进行更新"""
        # 填充按钮底色
        self.button_surface.fill(base_color)
        # 绘制外框
        pygame.draw.rect(self.button_surface, self.outer_edge_color, self.outer_rect, width=1)
        # 绘制内框
        pygame.draw.rect(self.button_surface, self.inner_edge_color, self.inner_rect, width=1)
        # 绘制按钮文本
        draw_text(self.button_surface, self.text, ["center", "center"], self.font_size, self.text_color)
        return None

    def update(self, event: pygame.event) -> None:
        """根据pygame.event对按钮进行状态更新和方法调用"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 鼠标左键按下
            if self.pos_in_button(event.pos):
                self.draw_down()
                self.is_down = True
        elif event.type == pygame.MOUSEMOTION:
            # 鼠标移动事件，用来检测按钮是否应该弹起
            if not self.pos_in_button(event.pos) and self.is_down:
                self.draw_up()
                self.is_down = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # 鼠标左键弹起事件
            if self.pos_in_button(event.pos) and self.is_down:
                self.draw_up()
                # 播放按钮点击音效
                self.click_sound.play()
                # 调用相应方法
                if self.call_function is not None:
                    self.call_function()
        return None

    def pos_in_button(self, pos) -> bool:
        """判断pos位置是否在按钮范围内"""
        offset = self.button_surface.get_abs_offset()
        if offset[0] <= pos[0] <= (offset[0] + self.size[0]) and offset[1] <= pos[1] <= (offset[1] + self.size[1]):
            return True
        else:
            return False


if __name__ == "__main__":
    def say_hello():
        print("hello!")

    # 功能测试
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("测试")

    button = Button(screen, "测试按钮", ["center", "center"], call_function=say_hello)
    button.draw_up()

    pygame.display.update()
    while True:
        for event in pygame.event.get():
            button.update(event)
        pygame.display.update()

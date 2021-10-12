# -*- coding: utf-8 -*-
# @Time    : 2021/3/7 14:29
# @Author  : He Ruizhi
# @File    : play_game.py
# @Software: PyCharm

from game_engine import GameEngine
from player import HumanPlayer
import pygame
import sys


def pos_in_area(pos, area):
    if area[0] < pos[0] < (area[0] + area[2]) and area[1] < pos[1] < (area[1] + area[3]):
        return True
    else:
        return False


if __name__ == '__main__':
    game = GameEngine()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 退出事件
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 鼠标左键按下
                pass
        # 落子监控
        game.take_action()
        # 音乐控制
        game.music_control()
        # 屏幕刷新
        pygame.display.update()

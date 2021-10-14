# -*- coding: utf-8 -*-
# @Time    : 2021/3/7 14:29
# @Author  : He Ruizhi
# @File    : play_game.py
# @Software: PyCharm

from game_engine import GameEngine
import pygame
import sys


if __name__ == '__main__':
    game = GameEngine()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 退出事件
                sys.exit()
            else:
                game.event_control(event)
        # 落子
        game.take_action()
        # 音乐控制
        game.music_control()
        # 屏幕刷新
        pygame.display.update()

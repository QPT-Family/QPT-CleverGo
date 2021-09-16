# -*- coding: utf-8 -*-
# @Time    : 2021/3/7 14:29
# @Author  : He Ruizhi
# @File    : play_game.py
# @Software: PyCharm

import weiqi_engine
from weiqi_engine import GoGameState
from player import Player, HumanPlayer
import pygame
import sys
sys.path.append('GymGo/')
from gym_go import govars


def pos_in_area(pos, area):
    if area[0] < pos[0] < (area[0] + area[2]) and area[1] < pos[1] < (area[1] + area[3]):
        return True
    else:
        return False


if __name__ == '__main__':
    go_game = GoGameState(mode='play')
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 退出事件
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 鼠标左键按下
                # 判断鼠标位置
                if pos_in_area(event.pos, (0, 0, weiqi_engine.SCREENHEIGHT, weiqi_engine.SCREENHEIGHT)):
                    # 当鼠标点击棋盘区域，判断黑白两方Player是否有HumanPlayer，如果有，执行鼠标落子操作
                    if isinstance(go_game.black_player, HumanPlayer) and go_game.black_player.allow and go_game.game_allow:
                        go_game.black_player.allow = False
                        go_game.black_player.step_with_mouse(go_game, event.pos)
                    if isinstance(go_game.white_player, HumanPlayer) and go_game.white_player.allow and go_game.game_allow:
                        go_game.white_player.allow = False
                        go_game.white_player.step_with_mouse(go_game, event.pos)
                elif pos_in_area(event.pos, (weiqi_engine.SCREENHEIGHT, go_game.tip_area.get_height(),
                                             go_game.info_area.get_width(), go_game.info_area.get_height())):
                    for btn in go_game.info_button_and_area:
                        if pos_in_area(event.pos, btn[1]):
                            btn[0].draw_down()
                            btn[0].is_down = True
                elif pos_in_area(event.pos, (weiqi_engine.SCREENHEIGHT, go_game.tip_area.get_height() + go_game.info_area.get_height(),
                                             go_game.button_area.get_width(), go_game.button_area.get_height())):
                    for btn in go_game.button_and_area:
                        if pos_in_area(event.pos, btn[1]):
                            btn[0].draw_down()
                            btn[0].is_down = True
            elif event.type == pygame.MOUSEMOTION:  # 鼠标移动事件，用来检测按钮是否应该弹起
                for btn in go_game.info_button_and_area + go_game.button_and_area:
                    if not pos_in_area(event.pos, btn[1]) and btn[0].is_down:
                        btn[0].draw_up()
                        btn[0].is_down = False  # 在某个按钮下移除按钮区域，该按钮恢复为没被按下状态
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # 鼠标左键弹起事件
                for btn in go_game.info_button_and_area + go_game.button_and_area:
                    # 在某个按钮上弹起，且该按钮为按下状态
                    if pos_in_area(event.pos, btn[1]) and btn[0].is_down:
                        btn[0].draw_up()
                        btn[0].call_function()  # 调用相应方法
        if go_game.black_player.allow and not isinstance(go_game.black_player, HumanPlayer) and go_game.action_next is None:
            go_game.black_player.allow = False
            go_game.black_player.play(go_game)
        if go_game.white_player.allow and not isinstance(go_game.white_player, HumanPlayer) and go_game.action_next is None:
            go_game.white_player.allow = False
            go_game.white_player.play(go_game)
        if go_game.action_next is not None and go_game.action_next != -1:
            if not go_game.restart:  # 重置标志未打开，本次移动有效
                go_game.play_step(go_game.action_next)
            elif go_game.current_player_type([HumanPlayer]):
                # 或者当前移动由人类玩家作出
                go_game.play_step(go_game.action_next)
                go_game.restart = False
            else:  # 否则只是将重置标志关闭
                go_game.restart = False
            # 更改行动方
            if go_game.get_current_player() == govars.BLACK:
                go_game.black_player.allow = True
            elif go_game.get_current_player() == govars.WHITE:
                go_game.white_player.allow = True
            go_game.action_next = None
        elif go_game.action_next == -1:  # 说明返回了一个无效落子
            go_game.action_next = None
            go_game.restart = False
            # 打开当前玩家允许落子标志
            if go_game.get_current_player() == govars.BLACK:
                go_game.black_player.allow = True
            elif go_game.get_current_player() == govars.WHITE:
                go_game.white_player.allow = True
        go_game.music_control()  # 音乐控制
        pygame.display.update()  # 屏幕刷新

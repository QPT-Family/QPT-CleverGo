# -*- coding: utf-8 -*-
# @Time    : 2021/10/1 0:28
# @Author  : He Ruizhi
# @File    : game_engine.py
# @Software: PyCharm

import pygame
import sys
import copy
import go_engine
from go_engine import GoEngine
from pgutils.ctmanager import CtManager
from pgutils.pgcontrols.button import Button
from pgutils.pgtools.text import draw_text
from pgutils.pgtools.position import pos_in_surface
from player import *
import os
from typing import List, Tuple, Callable, Union

SCREEN_SIZE = 1.8  # 控制模拟器界面放大或缩小的比例
SCREENWIDTH = int(SCREEN_SIZE * 600)  # 屏幕宽度
SCREENHEIGHT = int(SCREEN_SIZE * 400)  # 屏幕高度
BGCOLOR = (53, 107, 162)  # 屏幕背景颜色
BOARDCOLOR = (204, 85, 17)  # 棋盘颜色
BLACK = (0, 0, 0)  # 黑色
WHITE = (255, 255, 255)  # 白色
MARKCOLOR = (0, 200, 200)  # 最近落子标记颜色

# pygame初始化
pygame.init()
# 创建游戏主屏幕
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
# 设置游戏名称
pygame.display.set_caption('鸽子围棋(PigeonGo)')
# 启动界面绘制启动信息
loading_font = pygame.font.Font('assets/fonts/msyh.ttc', 72)
loading_text_render = loading_font.render('正在加载...', True, WHITE)
SCREEN.blit(loading_text_render, ((SCREEN.get_width() - loading_text_render.get_width()) / 2,
                                  (SCREEN.get_height() - loading_text_render.get_height()) / 2))
pygame.display.update()

IMAGES = {'black': (
    pygame.image.load('assets/pictures/B.png').convert_alpha(),
    pygame.image.load('assets/pictures/B-9.png').convert_alpha(),
    pygame.image.load('assets/pictures/B-13.png').convert_alpha(),
    pygame.image.load('assets/pictures/B-19.png').convert_alpha()
), 'white': (
    pygame.image.load('assets/pictures/W.png').convert_alpha(),
    pygame.image.load('assets/pictures/W-9.png').convert_alpha(),
    pygame.image.load('assets/pictures/W-13.png').convert_alpha(),
    pygame.image.load('assets/pictures/W-19.png').convert_alpha()
)}
SOUNDS = {
    'stone': pygame.mixer.Sound('assets/audios/Stone.wav'),
    'button': pygame.mixer.Sound('assets/audios/Button.wav')
}
MUSICS = [[os.path.splitext(music)[0], pygame.mixer.Sound('assets/musics/' + music)]
          for music in os.listdir('assets/musics')]


class GameEngine:
    def __init__(self, board_size: int = 9,
                 komi=7.5,
                 record_step: int = 4,
                 state_format: str = "separated",
                 record_last: bool = True):
        """
        游戏引擎初始化

        :param board_size: 棋盘大小，默认为9
        :param komi: 黑棋贴目数，默认黑贴7.5目（3又3/4子）
        :param record_step: 记录棋盘历史状态步数，默认为4
        :param state_format: 记录棋盘历史状态格式
                            【separated：黑白棋子分别记录在不同的矩阵中，[黑棋，白棋，下一步落子方，上一步落子位置(可选)]】
                            【merged：黑白棋子记录在同一个矩阵中，[棋盘棋子分布(黑1白-1)，下一步落子方，上一步落子位置(可选)]】
        :param record_last: 是否记录上一步落子位置
        """
        assert board_size in [9, 13, 19]
        assert state_format in ["separated", "merged"]

        self.board_size = board_size
        self.komi = komi
        self.record_step = record_step
        self.state_format = state_format
        self.record_last = record_last

        # 初始化GoEngine
        self.game_state = GoEngine(board_size=board_size, komi=komi, record_step=record_step,
                                   state_format=state_format, record_last=record_last)
        # 初始化pygame控件管理器
        self.ct_manager = CtManager()
        # 游戏控制状态
        self.play_state = False
        # 游戏界面状态: 'play' or 'train'
        self.surface_state = 'play'

        self.music_control_name = ['随机播放', '顺序播放', '单曲循环', '音乐关']
        # 黑方玩家
        self.black_player = HumanPlayer()
        # 白方玩家
        self.white_player = HumanPlayer()
        # 黑方玩家ID
        self.black_player_id = 0
        # 白方玩家ID
        self.white_player_id = 0
        # 音乐ID
        self.music_id = 0
        # 音乐控制ID
        self.music_control_id = 0

        # 填充背景色
        SCREEN.fill(BGCOLOR)
        # 棋盘区域
        self.board_surface = SCREEN.subsurface((0, 0, SCREENHEIGHT, SCREENHEIGHT))
        # 展示落子进度的区域
        self.speed_surface = SCREEN.subsurface((SCREENHEIGHT, 0, 3, SCREENHEIGHT))
        # 绘制提示落子方的太极图区域
        self.taiji_surface = SCREEN.subsurface((SCREENHEIGHT + self.speed_surface.get_width(), 0,
                                                SCREENWIDTH - SCREENHEIGHT - self.speed_surface.get_width(),
                                                SCREENHEIGHT / 3.5))
        # 玩家、音乐、音乐控制区域
        self.pmc_surface = SCREEN.subsurface((SCREENHEIGHT + self.speed_surface.get_width(), SCREENHEIGHT / 3.5,
                                              SCREENWIDTH - SCREENHEIGHT - self.speed_surface.get_width(),
                                              SCREENHEIGHT / 5))
        # 游戏操作区域区域
        self.operate_surface = SCREEN.subsurface((SCREENHEIGHT + self.speed_surface.get_width(),
                                                  self.taiji_surface.get_height() + self.pmc_surface.get_height(),
                                                  SCREENWIDTH - SCREENHEIGHT - self.speed_surface.get_width(),
                                                  SCREENHEIGHT * (1 - 1 / 3.5 - 1 / 5)))

        # 初始化按钮控件
        pmc_button_texts = [self.black_player.name, self.white_player.name,
                            MUSICS[self.music_id][0], self.music_control_name[self.music_control_id]]
        pmc_button_call_functions = [self.fct_for_black_player, self.fct_for_white_player,
                                     self.fct_for_music_choose, self.fct_for_music_control]
        self.pmc_buttons = self.create_buttons(self.pmc_surface, pmc_button_texts, pmc_button_call_functions,
                                               [22 * SCREEN_SIZE + 120, self.pmc_surface.get_height() / 20 + 4],
                                               18 * SCREEN_SIZE, up_color=[202, 171, 125], down_color=[186, 146, 86],
                                               outer_edge_color=[255, 255, 214], size=[160, 27], font_size=16,
                                               inner_edge_color=[247, 207, 181], text_color=[253, 253, 19])
        operate_play_button_texts = ['开始游戏', '弃一手', '悔棋', '重新开始', ('十三' if self.board_size == 9 else '九') + '路棋',
                                     ('十三' if self.board_size == 19 else '十九') + '路棋', '训练幼生Alpha狗', '退出游戏']
        operate_play_button_call_functions = [self.fct_for_play_game, self.fct_for_pass, self.fct_for_regret,
                                              self.fct_for_restart, self.fct_for_new_game_1, self.fct_for_new_game_2,
                                              self.fct_for_train_alphago, self.fct_for_exit]
        self.operate_play_buttons = self.create_buttons(self.operate_surface, operate_play_button_texts,
                                                        operate_play_button_call_functions,
                                                        ['center', self.operate_surface.get_height() / 20],
                                                        24 * SCREEN_SIZE, size=[120, 27])
        operate_train_button_texts = ['开始训练', '返回']
        operate_train_button_call_functions = [self.fct_for_train, self.fct_for_back]
        self.operate_train_buttons = self.create_buttons(self.operate_surface, operate_train_button_texts,
                                                         operate_train_button_call_functions,
                                                         ['center', self.operate_surface.get_height() * 0.8],
                                                         24 * SCREEN_SIZE, size=[120, 27])

        # 按钮控件注册
        self.ct_manager.register(self.pmc_buttons)
        self.ct_manager.register(self.operate_play_buttons)
        self.ct_manager.register(self.operate_train_buttons)

        # 棋盘每格的大小
        self.block_size = int(SCREEN_SIZE * 360 / (self.board_size - 1))
        # 棋子大小
        if self.board_size == 9:
            self.piece_size = IMAGES['black'][1].get_size()
        elif self.board_size == 13:
            self.piece_size = IMAGES['black'][2].get_size()
        else:
            self.piece_size = IMAGES['black'][3].get_size()

        # 绘制棋盘、太极图、PMC区域、操作区域
        self.draw_board()
        self.draw_taiji()
        self.draw_pmc()
        self.draw_operate()

        # 音乐播放
        if not pygame.mixer.get_busy():
            MUSICS[self.music_id][1].play()

        # 刷新屏幕
        pygame.display.update()

    def draw_board(self) -> None:
        """绘制棋盘"""
        # 背景颜色覆盖
        self.board_surface.fill(BOARDCOLOR)
        # 确定棋盘边框坐标
        rect_pos = (int(SCREEN_SIZE * 20), int(SCREEN_SIZE * 20), int(SCREEN_SIZE * 360), int(SCREEN_SIZE * 360))
        # 绘制边框
        pygame.draw.rect(self.board_surface, BLACK, rect_pos, 3)
        # 绘制棋盘内线条
        for i in range(self.board_size - 2):
            pygame.draw.line(self.board_surface, BLACK, (SCREEN_SIZE * 20, SCREEN_SIZE * 20 + (i + 1) * self.block_size),
                             (SCREEN_SIZE * 380, SCREEN_SIZE * 20 + (i + 1) * self.block_size), 2)
            pygame.draw.line(self.board_surface, BLACK, (SCREEN_SIZE * 20 + (i + 1) * self.block_size, SCREEN_SIZE * 20),
                             (SCREEN_SIZE * 20 + (i + 1) * self.block_size, SCREEN_SIZE * 380), 2)
        # 绘制天元和星位
        if self.board_size == 9:
            position_loc = [2, 4, 6]
        elif self.board_size == 13:
            position_loc = [3, 6, 9]
        else:
            position_loc = [3, 9, 15]
        positions = [[SCREEN_SIZE * 20 + 1 + self.block_size * i, SCREEN_SIZE * 20 + 1 + self.block_size * j]
                     for i in position_loc for j in position_loc]
        for pos in positions:
            pygame.draw.circle(self.board_surface, BLACK, pos, 5, 0)
        return None

    def draw_taiji(self) -> None:
        """绘制表示下一手落子方的太极图"""
        black_pos = (self.taiji_surface.get_width() - IMAGES['black'][0].get_width()) / 2, \
                    (self.taiji_surface.get_height() - IMAGES['black'][0].get_height()) / 2
        white_pos = black_pos[0] + 44, black_pos[1]
        # 背景颜色填充
        self.taiji_surface.fill(BGCOLOR)
        if not self.play_state:
            # 游戏未进行状态
            self.taiji_surface.blit(IMAGES['black'][0], black_pos)
            self.taiji_surface.blit(IMAGES['white'][0], white_pos)
        else:
            if self.game_state.turn() == go_engine.BLACK:
                # 下一手为黑方
                self.taiji_surface.blit(IMAGES['black'][0], black_pos)
            elif self.game_state.turn() == go_engine.WHITE:
                # 下一手为白方
                self.taiji_surface.blit(IMAGES['white'][0], white_pos)
        return None

    def draw_pmc(self) -> None:
        self.pmc_surface.fill(BGCOLOR)
        # 绘制4行说明文字
        texts = ['执黑玩家：', '执白玩家：', '对弈音乐：', '音乐控制：']
        pos_next = [22 * SCREEN_SIZE, self.pmc_surface.get_height() / 20]
        for text in texts:
            pos_next = draw_text(self.pmc_surface, text, pos_next, font_size=24)
        # 按钮激活
        for button in self.pmc_buttons:
            button.enable()
        return None

    def draw_operate(self) -> None:
        # surface_state为"play"
        if self.surface_state == 'play':
            self.operate_surface.fill(BGCOLOR)
            # 按钮激活
            for button in self.operate_play_buttons:
                button.enable()
        elif self.surface_state == 'train':
            # surface_state为"train"
            pass
        return None

    def draw_pieces(self) -> None:
        """绘制棋子方法"""
        for i in range(self.board_size):
            for j in range(self.board_size):
                # 确定绘制棋子的坐标
                pos = (SCREEN_SIZE * 22 + self.block_size * j - self.piece_size[1] / 2,
                       SCREEN_SIZE * 19 + self.block_size * i - self.piece_size[0] / 2)
                # 查看相应位置有无黑色棋子或白色棋子
                if self.game_state.current_state[go_engine.BLACK][i, j] == 1:
                    if self.board_size == 9:
                        self.board_surface.blit(IMAGES['black'][1], pos)
                    elif self.board_size == 13:
                        self.board_surface.blit(IMAGES['black'][2], pos)
                    else:
                        self.board_surface.blit(IMAGES['black'][3], pos)
                elif self.game_state.current_state[go_engine.WHITE][i, j] == 1:
                    if self.board_size == 9:
                        self.board_surface.blit(IMAGES['white'][1], pos)
                    elif self.board_size == 13:
                        self.board_surface.blit(IMAGES['white'][2], pos)
                    else:
                        self.board_surface.blit(IMAGES['white'][3], pos)
        return None

    def draw_mark(self, action) -> None:
        """根据最近落子的棋盘坐标，绘制标记"""
        row = action // self.board_size
        col = action % self.board_size
        if self.game_state.turn() == go_engine.WHITE:
            if self.board_size == 9:
                pos = (SCREEN_SIZE * 19 + col * self.block_size, SCREEN_SIZE * 22 + row * self.block_size)
            elif self.board_size == 13:
                pos = (SCREEN_SIZE * 20 + col * self.block_size, SCREEN_SIZE * 21 + row * self.block_size)
            else:
                pos = (SCREEN_SIZE * 21 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
        else:
            if self.board_size == 9:
                pos = (SCREEN_SIZE * 19 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
            elif self.board_size == 13:
                pos = (SCREEN_SIZE * 20 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
            else:
                pos = (SCREEN_SIZE * 21 + col * self.block_size, SCREEN_SIZE * 19 + row * self.block_size)
        pygame.draw.circle(self.board_surface, MARKCOLOR, pos, self.piece_size[0] / 2 + 2 * SCREEN_SIZE, 2)
        return None

    def play_step(self, action: int) -> None:
        """输入动作，更新游戏状态，并在有些界面上绘制相应的动画"""
        self.game_state.step(action)
        # 重绘棋盘、棋子、落子标记
        if action != self.board_size * self.board_size and action is not None:
            self.draw_board()
            self.draw_pieces()
            self.draw_mark(action)
            SOUNDS['stone'].play()
        # 重绘提示落子的太极图
        self.draw_taiji()
        if self.game_state.done:
            self.draw_over()
            self.play_state = False
        return None

    def take_action(self) -> None:
        """当self.black_player.action或self.white_player.action不为None时候，执行相应动作"""

        if self.play_state and self.black_player.allow and self.black_player.action is None and \
                self.game_state.turn() == go_engine.BLACK and not isinstance(self.black_player, HumanPlayer):
            self.black_player.play(self)
            self.black_player.allow = False
        if self.play_state and self.white_player.allow and self.white_player.action is None and \
                self.game_state.turn() == go_engine.WHITE and not isinstance(self.white_player, HumanPlayer):
            self.white_player.play(self)
            self.white_player.allow = False

        if self.play_state and self.game_state.turn() == go_engine.BLACK and self.black_player.action is not None:
            self.play_step(self.black_player.action)
            self.black_player.action = None
            self.white_player.allow = True
        if self.play_state and self.game_state.turn() == go_engine.WHITE and self.white_player.action is not None:
            self.play_step(self.white_player.action)
            self.white_player.action = None
            self.black_player.allow = True

        if isinstance(self.black_player, MCTSPlayer) or isinstance(self.black_player, AlphaGoPlayer):
            if self.black_player.speed is not None:
                self.draw_speed(self.black_player.speed[0], self.black_player.speed[1])
                self.black_player.speed = None
        if isinstance(self.white_player, MCTSPlayer) or isinstance(self.white_player, AlphaGoPlayer):
            if self.white_player.speed is not None:
                self.draw_speed(self.white_player.speed[0], self.white_player.speed[1])
                self.white_player.speed = None
        return None

    def event_control(self, event: pygame.event.Event) -> None:
        """
        游戏控制：根据pygame.event触发相应游戏状态

        1. 当Player为HumanPlayer时控制玩家落子
        2. 根据event对ct_manager进行更新

        :param event:
        :return:
        """
        # HumanPlayer落子
        next_player, is_human = self.next_player_and_type()
        if self.play_state and is_human:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and \
                    pos_in_surface(event.pos, self.board_surface):
                action = self.mouse_pos_to_action(event.pos)
                if self.game_state.action_valid(action):
                    if next_player == go_engine.BLACK:
                        self.black_player.action = action
                    else:
                        self.white_player.action = action
        # ct_manager更新
        self.ct_manager.update(event)

    def game_state_simulator(self) -> GoEngine:
        """返回一个用作模拟的game_state"""
        game_state = GoEngine(board_size=self.board_size, komi=self.komi, record_step=self.record_step,
                              state_format=self.state_format, record_last=self.record_last)
        game_state.current_state = np.copy(self.game_state.current_state)
        game_state.board_state = np.copy(self.game_state.board_state)
        game_state.board_state_history = copy.copy(self.game_state.board_state_history)
        game_state.action_history = copy.copy(self.game_state.action_history)
        game_state.done = self.game_state.done
        return game_state

    def mouse_pos_to_action(self, mouse_pos):
        """将鼠标位置转换为action"""
        if 0 < mouse_pos[0] < SCREENHEIGHT and 0 < mouse_pos[1] < SCREENHEIGHT:
            # 将鼠标点击坐标转action，mouse_pos[0]对应列坐标，mouse_pos[1]对应行坐标
            row = round((mouse_pos[1] - SCREEN_SIZE * 20) / self.block_size)
            if row < 0:
                row = 0
            elif row > self.board_size - 1:
                row = self.board_size - 1
            col = round((mouse_pos[0] - SCREEN_SIZE * 20) / self.block_size)
            if col < 0:
                col = 0
            elif col > self.board_size - 1:
                col = self.board_size - 1
            return row * self.board_size + col
        else:
            return None

    def draw_over(self) -> None:
        """绘制游戏结束画面"""
        # 获得黑白双方的区域
        black_areas, white_areas = self.game_state.areas()
        over_text_1 = '协商终局'
        over_text_2 = '黑方{}子 白方{}子'.format(black_areas, white_areas)
        area_difference = (black_areas - white_areas - self.komi) / 2
        if area_difference == 0:
            over_text_3 = '和棋'
        elif area_difference > 0:
            over_text_3 = '黑胜{}子'.format(area_difference)
        else:
            over_text_3 = '白胜{}子'.format(-area_difference)
        over_screen = pygame.Surface((320, 170), pygame.SRCALPHA)
        over_screen.fill((57, 44, 33, 100))
        next_pos = draw_text(over_screen, over_text_1, ['center', over_screen.get_height() / 6],
                             font_size=26, font_color=[220, 220, 220])
        next_pos = draw_text(over_screen, over_text_2, ['center', next_pos[1]],
                             font_size=26, font_color=[220, 220, 220])
        draw_text(over_screen, over_text_3, ['center', next_pos[1]], font_size=26, font_color=[220, 220, 220])
        self.board_surface.blit(over_screen,
                                ((self.board_surface.get_width() - over_screen.get_width()) / 2,
                                 (self.board_surface.get_height() - over_screen.get_height()) / 2))
        return None

    def draw_speed(self, count, total) -> None:
        """一个简单绘制落子进度的方法"""
        self.speed_surface.fill(BGCOLOR)
        sub_speed_area = self.speed_surface.subsurface((0, SCREENHEIGHT - round(count / total * SCREENHEIGHT),
                                                        self.speed_surface.get_width(),
                                                        round(count / total * SCREENHEIGHT)))
        sub_speed_area.fill((15, 255, 255))
        return None

    @staticmethod
    def create_buttons(surface: pygame.Surface,
                       button_texts: List[str],
                       call_functions: List[Callable],
                       first_pos: List[int or float],
                       button_margin: Union[int, float],
                       font_size: int = 14,
                       size: Union[Tuple[int], List[int]] = (87, 27),
                       text_color: Union[Tuple[int], List[int]] = (0, 0, 0),
                       up_color: Union[Tuple[int], List[int]] = (225, 225, 225),
                       down_color: Union[Tuple[int], List[int]] = (190, 190, 190),
                       outer_edge_color: Union[Tuple[int], List[int]] = (240, 240, 240),
                       inner_edge_color: Union[Tuple[int], List[int]] = (173, 173, 173)
                       ) -> List[Button]:
        """
        批量地创建Button控件

        :param surface: Button绘制的surface
        :param button_texts: Button显示文本
        :param call_functions: Button的点击调用的函数
        :param first_pos: 第一个按钮绘制的位置
        :param button_margin: 相邻两个按钮之间的间隔
        :param font_size: 按钮字体大小
        :param size: 按钮大小
        :param text_color: 按钮文本颜色
        :param up_color: 按钮未被点击时颜色
        :param down_color: 按钮被点击时颜色
        :param outer_edge_color: 按钮外边框颜色
        :param inner_edge_color: 按钮内边框颜色
        :return: List[Button]
        """
        assert len(button_texts) == len(call_functions)

        buttons = []

        pos_next = copy.copy(first_pos)
        for btn_text, call_fct in zip(button_texts, call_functions):
            button = Button(surface, btn_text, pos_next, call_fct, size=size, font_size=font_size,
                            text_color=text_color, up_color=up_color, down_color=down_color,
                            outer_edge_color=outer_edge_color, inner_edge_color=inner_edge_color)
            buttons.append(button)
            pos_next[1] += button_margin
        return buttons

    def music_control(self):
        # 音乐控制
        if not pygame.mixer.get_busy() and self.music_control_id != 3:  # 当歌曲没在播放，且音乐没关掉
            if self.music_control_id == 0:  # 随机播放
                rand_int = np.random.randint(len(MUSICS))  # 随机获取一首歌
                if len(MUSICS) > 1:
                    while rand_int == self.music_id:
                        rand_int = np.random.randint(len(MUSICS))
                self.music_id = rand_int
                MUSICS[self.music_id][1].play()
            elif self.music_control_id == 1:  # 顺序播放
                self.music_id += 1
                self.music_id %= len(MUSICS)
                MUSICS[self.music_id][1].play()
            elif self.music_control_id == 2:  # 单曲循环
                MUSICS[self.music_id][1].play()
            self.pmc_buttons[2].set_text(MUSICS[self.music_id][0])
            self.pmc_buttons[2].draw_up()
        elif pygame.mixer.get_busy() and self.music_control_id == 3:  # 音乐关
            MUSICS[self.music_id][1].stop()

    def next_player_and_type(self):
        """返回下一步落子方及其是否为人类玩家"""
        if self.game_state.turn() == go_engine.BLACK:
            if isinstance(self.black_player, HumanPlayer):
                return go_engine.BLACK, True
            else:
                return go_engine.BLACK, False
        else:
            if isinstance(self.white_player, HumanPlayer):
                return go_engine.WHITE, True
            else:
                return go_engine.WHITE, False

    def fct_for_black_player(self):
        # 切换玩家，会使游戏暂停
        self.play_state = False
        self.operate_play_buttons[0].set_text('开始游戏')

        self.black_player.valid = False
        if self.game_state.turn() == go_engine.BLACK:
            if isinstance(self.black_player, MCTSPlayer) or isinstance(self.black_player, AlphaGoPlayer):
                self.draw_speed(0, 1)

        self.black_player_id += 1
        # player_num为游戏支持的Player总数
        player_num = 11 if self.board_size == 9 else 2
        self.black_player_id %= player_num

        # 将当前Player设置为响应Player
        self.black_player = self.create_player(self.black_player_id)

        self.pmc_buttons[0].set_text(self.black_player.name)

    def fct_for_white_player(self):
        # 切换玩家，会使游戏暂停
        self.play_state = False
        self.operate_play_buttons[0].set_text('开始游戏')

        self.white_player.valid = False
        if self.game_state.turn() == go_engine.WHITE:
            if isinstance(self.white_player, MCTSPlayer) or isinstance(self.white_player, AlphaGoPlayer):
                self.draw_speed(0, 1)

        self.white_player_id += 1
        # player_num为游戏支持的Player总数
        player_num = 11 if self.board_size == 9 else 2
        self.white_player_id %= player_num

        # 将当前Player设置为响应Player
        self.white_player = self.create_player(self.white_player_id)

        self.pmc_buttons[1].set_text(self.white_player.name)

    @staticmethod
    def create_player(player_id: int):
        """根据player_id创建player"""
        if player_id == 0:
            player = HumanPlayer()
        elif player_id == 1:
            player = RandomPlayer()
        elif player_id in [2, 3, 4, 5, 6]:
            player = MCTSPlayer(n_playout=400 * (2 ** (player_id - 2)))
        elif player_id == 7:
            player = PolicyNetPlayer(model_path='models/alpha_go.pdparams')
        elif player_id == 8:
            player = ValueNetPlayer(model_path='models/alpha_go.pdparams')
        elif player_id == 9:
            player = AlphaGoPlayer(model_path='models/alpha_go.pdparams')
        elif player_id == 10:
            player = AlphaGoPlayer(model_path='models/my_alpha_go.pdparams')
        else:
            player = Player()
        return player

    def fct_for_music_choose(self):
        MUSICS[self.music_id][1].stop()
        if self.music_control_id == 0:  # 随机播放
            rand_int = np.random.randint(len(MUSICS))  # 随机获取一首歌
            if len(MUSICS) > 1:
                while rand_int == self.music_id:
                    rand_int = np.random.randint(len(MUSICS))
            self.music_id = rand_int
        else:
            self.music_id += 1
            self.music_id %= len(MUSICS)
        self.pmc_buttons[2].set_text(MUSICS[self.music_id][0])
        MUSICS[self.music_id][1].play()

    def fct_for_music_control(self):
        self.music_control_id += 1
        self.music_control_id %= len(self.music_control_name)
        self.pmc_buttons[3].set_text(self.music_control_name[self.music_control_id])
        # 说明音乐控制按钮上一次为音乐关
        if self.music_control_id == 0:
            # 须直接将音乐打开
            MUSICS[self.music_id][1].play()

    def fct_for_play_game(self):
        # 当开始游戏按钮被点击
        if self.play_state:
            # 游戏在进行状态时点击该按钮
            self.operate_play_buttons[0].set_text('开始游戏')
            self.play_state = False
        else:
            # 游戏在未进行状态时点击该按钮
            self.operate_play_buttons[0].set_text('暂停游戏')
            self.play_state = True
        self.draw_taiji()

    def fct_for_pass(self):
        # pass一手
        # 仅在游戏开始且当前玩家为HumanPlayer时有效
        if self.play_state:
            next_player, is_human = self.next_player_and_type()
            if is_human:
                if next_player == go_engine.BLACK:
                    self.black_player.action = self.board_size ** 2
                else:
                    self.white_player.action = self.board_size ** 2

    def fct_for_regret(self):
        # 悔棋
        if self.play_state:
            _, is_human = self.next_player_and_type()
            if is_human:
                if len(self.game_state.board_state_history) > 2:
                    self.game_state.current_state = self.game_state.board_state_history[-3]
                    self.game_state.board_state_history = self.game_state.board_state_history[:-2]
                    action = self.game_state.action_history[-3]
                    self.game_state.action_history = self.game_state.action_history[:-2]
                    self.draw_board()
                    self.draw_pieces()
                    self.draw_mark(action)
                    self.draw_taiji()
                elif len(self.game_state.board_state_history) == 2:
                    self.game_state.reset()
                    self.draw_board()
                    self.draw_taiji()

    def fct_for_restart(self):
        # 当重新开始按钮被点击
        self.play_state = True
        self.operate_play_buttons[0].set_text('暂停游戏')
        self.game_state.reset()
        self.draw_board()
        self.draw_taiji()

        self.black_player.valid = False
        self.white_player.valid = False
        self.black_player = self.create_player(self.black_player_id)
        self.white_player = self.create_player(self.white_player_id)

    def fct_for_new_game_1(self):
        # 保存音乐信息
        music_id = self.music_id
        music_control_id = self.music_control_id
        # 初始化
        if self.board_size == 9:
            new_game_size = 13
        else:
            new_game_size = 9
        self.__init__(new_game_size, komi=self.komi, record_step=self.record_step, state_format=self.state_format,
                      record_last=self.record_last)
        self.music_id = music_id
        self.music_control_id = music_control_id
        self.pmc_buttons[2].set_text(MUSICS[self.music_id][0])
        self.pmc_buttons[3].set_text(self.music_control_name[self.music_control_id])

    def fct_for_new_game_2(self):
        # 保存音乐信息
        music_id = self.music_id
        music_control_id = self.music_control_id
        # 初始化
        if self.board_size == 19:
            new_game_size = 13
        else:
            new_game_size = 19
        self.__init__(new_game_size, komi=self.komi, record_step=self.record_step, state_format=self.state_format,
                      record_last=self.record_last)
        self.music_id = music_id
        self.music_control_id = music_control_id
        self.pmc_buttons[2].set_text(MUSICS[self.music_id][0])
        self.pmc_buttons[3].set_text(self.music_control_name[self.music_control_id])

    def fct_for_train_alphago(self):
        # 点击训练幼生阿尔法狗按钮，进入训练界面
        pass

    @staticmethod
    def fct_for_exit():
        # 当退出游戏按钮被点击
        sys.exit()

    def fct_for_train(self):
        # 当开始训练按钮被点击
        pass

    def fct_for_back(self):
        for button in self.operate_train_buttons:
            button.disable()
        self.play_state = False
        self.draw_operate()


if __name__ == '__main__':
    # 功能测试
    game = GameEngine()
    while True:
        for event in pygame.event.get():
            game.event_control(event)
        game.take_action()
        game.music_control()
        pygame.display.update()

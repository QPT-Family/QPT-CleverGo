# -*- coding: utf-8 -*-
# @Time    : 2021/10/1 0:28
# @Author  : He Ruizhi
# @File    : game_engine.py
# @Software: PyCharm

import pygame
import numpy as np
import sys
import copy
import go_engine
from go_engine import GoEngine
from pgutils.ctmanager import CtManager
from pgutils.pgcontrols.button import Button
from pgutils.pgtools.text import draw_text

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


PLAYERS_9 = ['人类玩家', '随机落子', '蒙特卡洛400', '蒙特卡洛800', '蒙特卡洛1600', '蒙特卡洛3200',
             '蒙特卡洛6400', '策略网络', '价值网络', '阿尔法狗', '幼生阿尔法狗']
PLAYERS_13_19 = ['人类玩家', '随机落子', '蒙特卡洛400', '蒙特卡洛800']
PLAYERS = PLAYERS_9  # 为了在代码中不用判断PLAYERS_9还是PLAYERS_13_19
MUSIC_CONTROLS = ['随机播放', '顺序播放', '单曲循环', '音乐关']

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

# 加载后置
SOUNDS, MUSICS = {}, []
SOUNDS_ALL = ['Stone', 'Button']
# MUSICS_ALL = ['铜雀赋', '风居住的街道', 'Canon', 'Muyuuka', 'River Flows in You', 'Snow Dream', 'Sundial Dreams',
#               'The Rain', '三个人的时光', '人类的光', '只要为你活一天', '大风起兮云飞扬', '天空之城', '心游太玄', '情动',
#               '我愿意', '故乡的原风景', '李香兰', '流光', '清平乐', '爱江山更爱美人', '琵琶语', '画堂春', '穿越时空的思念',
#               '美丽的神话', '虫儿飞', '那些花儿', '风华绝代', '风吹麦浪', '黄昏的归途', '江南雨', 'Childhood Memories',
#               'Lettre A Elise', 'Star Sky', '夜的钢琴曲5', '梦中的婚礼', '瞬间的永恒', '秋日私语']
MUSICS_ALL = ['铜雀赋', '风居住的街道']


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
        self.manager = CtManager()
        # 游戏控制状态
        self.play_state = False
        # 界面状态，用于控制按钮触发【"play", "train"】
        self.surface_state = "play"

        # 游戏界面初始化
        self.surface_init()

        if not pygame.mixer.get_busy():
            MUSICS[self.music_id][1].play()

        # 刷新屏幕
        pygame.display.update()

    def surface_init(self) -> None:
        """游戏界面初始化"""
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
        # 绘制按钮的区域
        self.button_surface = SCREEN.subsurface((SCREENHEIGHT + self.speed_surface.get_width(),
                                                 self.taiji_surface.get_height() + self.pmc_surface.get_height(),
                                                 SCREENWIDTH - SCREENHEIGHT - self.speed_surface.get_width(),
                                                 SCREENHEIGHT * (1 - 1 / 3.5 - 1 / 5)))

        # 棋盘每格的大小
        self.block_size = int(SCREEN_SIZE * 360 / (self.board_size - 1))
        # 棋子大小
        if self.board_size == 9:
            self.piece_size = IMAGES['black'][1].get_size()
        elif self.board_size == 13:
            self.piece_size = IMAGES['black'][2].get_size()
        else:
            self.piece_size = IMAGES['black'][3].get_size()
        # 按钮间隔
        self.button_margin = 24 * SCREEN_SIZE

        # 绘制棋盘、太极图、PMC区域、Button区域
        self.draw_board()
        self.draw_taiji()
        self.draw_pmc()
        self.draw_button()
        return None

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
        # text_color=(253, 253, 19)  金黄色  up_color=(202, 171, 125)  浅黄色  down_color=(186, 146, 86)  深黄色
        self.pmc_surface.fill(BGCOLOR)
        # 绘制4行说明文字
        texts = ['执黑玩家：', '执白玩家：', '对弈音乐：', '音乐控制：']
        pos_next = [22 * SCREEN_SIZE, self.pmc_surface.get_height() / 20]
        for text in texts:
            pos_next = draw_text(self.pmc_surface, text, pos_next, font_size=24)
        button_texts = [PLAYERS[self.black_player_id], PLAYERS[self.white_player_id],
                        MUSICS[self.music_id][0], MUSIC_CONTROLS[self.music_control_id]]
        call_functions = [self.fct_for_black_player, self.fct_for_white_player,
                          self.fct_for_music_choose, self.fct_for_music_control]
        button_active_states = [["play"], ["play"], ["play", "train"], ["play", "train"]]
        # 绘制按钮
        pos_next = [22 * SCREEN_SIZE + 120, self.info_area.get_height() / 20 + 4]
        for btn_text, call_fct, btn_astate in zip(button_texts, call_functions, button_active_states):
            button = Button(self.pmc_surface, btn_text, pos_next, call_fct, up_color=[202, 171, 125],
                            down_color=[186, 146, 86], outer_edge_color=[255, 255, 214], size=[160, 27],
                            inner_edge_color=[247, 207, 181], text_color=[253, 253, 19], font_size=16)
            self.manager.register(button, btn_astate)
            pos_next[1] += button.size[1]
        return None

    def draw_button(self) -> None:
        # surface_state为"play"
        if self.surface_state == "play":
            self.button_surface.fill(BGCOLOR)
            # 绘制 开始游戏、弃一手、悔棋、重新开始、XX路棋、XX路棋、退出游戏 按钮
            button_texts = ['开始游戏', '弃一手', '悔棋', '重新开始', ('十三' if self.board_size == 9 else '九') + '路棋',
                            ('十三' if self.board_size == 19 else '十九') + '路棋', '训练幼生Alpha狗', '退出游戏']
            call_functions = [self.fct_for_play_game, self.fct_for_pass, self.fct_for_regret, self.fct_for_restart,
                              self.fct_for_new_game_1, self.fct_for_new_game_2, self.fct_for_train_alphago, self.fct_for_exit]
            pos_next = ["center", self.button_surface.get_height() / 20]
            for btn_text, call_fct in zip(button_texts, call_functions):
                button = Button(self.button_surface, btn_text, pos_next, call_fct, size=[120, 27])
                self.manager.register(button, [self.surface_state])
        elif self.surface_state == "train":
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
            elif self.board_size == 19:
                pos = (SCREEN_SIZE * 21 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
        else:
            if self.board_size == 9:
                pos = (SCREEN_SIZE * 19 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
            elif self.board_size == 13:
                pos = (SCREEN_SIZE * 20 + col * self.block_size, SCREEN_SIZE * 20 + row * self.block_size)
            elif self.board_size == 19:
                pos = (SCREEN_SIZE * 21 + col * self.block_size, SCREEN_SIZE * 19 + row * self.block_size)
        pygame.draw.circle(self.board_surface, MARKCOLOR, pos, self.piece_size[0] / 2 + 2 * SCREEN_SIZE, 2)
        return None

    def play_step(self, action: int) -> None:
        """
        输入动作，更新游戏状态

        :param action: 一个0 —— self.size * self.size的整数
        :return:
        """
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

        # self.mode = mode  # 判断是训练（train）还是对局（play）
        #
        # if self.mode == 'play':  # 当mode为play时的初始化
        #     self.sound_load()  # 在mode为play时需加载音效
        #     self.state_history = []  # 保存棋盘状态，用于悔棋
        #     self.action_history = []  # 保存历史动作，用于悔棋
        #     global PLAYERS
        #     if self.size == 9:
        #         PLAYERS = PLAYERS_9
        #     else:
        #         PLAYERS = PLAYERS_13_19
        #
        #     # ==================围棋游戏控制信息初始化==========================
        #     self.game_allow = False  # 游戏是否允许开始，用于开始游戏按钮被点击时触发
        #     self.restart = False  # 是否重新开始标记，用于点击重新开始按钮、切换玩家时线程同步
        #     self.action_next = None  # 下一步的action，当其不为None时，将会执行该动作
        #     self.button_area_state = 'main'  # 按钮区域状态，总共有main、train_AlphaGo
        #     self.black_player = HumanPlayer()  # 执黑Player对象
        #     self.white_player = HumanPlayer()  # 执白Player对象
        #     self.black_player_id = 0  # 执黑玩家id
        #     self.white_player_id = 0  # 执白玩家id
        #     self.music_id = 0  # 对弈音乐id
        #     self.music_control_id = 0  # 音乐控制id

    def game_state_cp(self) -> GoEngine:
        """返回一个用作模拟的game_state"""
        game_state = GoEngine(board_size=self.board_size, komi=self.komi, record_step=self.record_step,
                              state_format=self.state_format, record_last=self.record_last)
        game_state.current_state = np.copy(self.game_state.current_state)
        game_state.board_state = np.copy(self.game_state.board_state)
        game_state.board_state_history = copy.copy(self.game_state.board_state_history)
        game_state.action_history = copy.copy(self.game_state.action_history)
        return game_state

    def mouse_pos_to_action(self, mouse_pos):
        """将鼠标位置转换为action"""
        if 0 < mouse_pos[0] < SCREENHEIGHT and 0 < mouse_pos[1] < SCREENHEIGHT:
            # 将鼠标点击坐标转action，mouse_pos[0]对应列坐标，mouse_pos[1]对应行坐标
            row = round((mouse_pos[1] - SCREEN_SIZE * 20) / self.block_size)
            if row < 0:
                row = 0
            elif row > self.size - 1:
                row = self.size - 1
            col = round((mouse_pos[0] - SCREEN_SIZE * 20) / self.block_size)
            if col < 0:
                col = 0
            elif col > self.size - 1:
                col = self.size - 1
            return row * self.size + col
        else:
            return None

    def draw_over(self):
        # 绘制游戏结束画面
        black_areas, white_areas = gogame.areas(self.state_)  # 获得黑白双方的区域
        winner = gogame.winning(self.state_, self.komi)
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
        next_pos = self.draw_text(over_screen, over_text_1, ['center', over_screen.get_height() / 6],
                                  font_size=26, font_color=(220, 220, 220))
        next_pos = self.draw_text(over_screen, over_text_2, ['center', next_pos[1]],
                                  font_size=26, font_color=(220, 220, 220))
        self.draw_text(over_screen, over_text_3, ['center', next_pos[1]], font_size=26, font_color=(220, 220, 220))
        self.board_area.blit(over_screen,
                             ((self.board_area.get_width() - over_screen.get_width()) / 2,
                              (self.board_area.get_height() - over_screen.get_height()) / 2))

    def draw_speed(self, count, total):
        """一个简单绘制落子进度的方法"""
        self.speed_area.fill(BGCOLOR)
        sub_speed_area = self.speed_area.subsurface((0, SCREENHEIGHT - round(count / total * SCREENHEIGHT),
                                                     self.speed_area.get_width(), round(count / total * SCREENHEIGHT)))
        # sub_speed_area.fill((106, 255, 143))
        sub_speed_area.fill((15, 255, 255))

    def music_control(self):
        # 音乐控制
        if not pygame.mixer.get_busy() and self.music_control_id != 3:  # 当歌曲没在播放，且音乐没关掉
            if self.music_control_id == 0:  # 随机播放
                rand_int = np.random.randint(len(MUSICS))  # 随机获取一首歌
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
            self.info_button_and_area = self.draw_info()
        elif pygame.mixer.get_busy() and self.music_control_id == 3:  # 音乐关
            MUSICS[self.music_id][1].stop()

    def fct_for_black_player(self):
        SOUNDS['button'].play()
        self.black_player_id += 1
        self.black_player_id %= len(PLAYERS)
        pre_player_allow = self.black_player.allow
        # 将当前Player设置为响应Player
        if self.black_player_id == 0:  # 人类玩家
            self.black_player = HumanPlayer()
        elif self.black_player_id == 1:  # 随机落子
            self.black_player = RandomPlayer()
        elif self.black_player_id == 2:  # 蒙特卡洛400
            self.black_player = MCTSPlayer(n_playout=40)
        elif self.black_player_id == 3:  # 蒙特卡洛800
            self.black_player = MCTSPlayer(n_playout=800)
        elif self.black_player_id == 4:  # 蒙特卡洛1600
            self.black_player = MCTSPlayer(n_playout=1600)
        elif self.black_player_id == 5:  # 蒙特卡洛3200
            self.black_player = MCTSPlayer(n_playout=3200)
        elif self.black_player_id == 6:  # 蒙特卡洛6400
            self.black_player = MCTSPlayer(n_playout=6400)
        elif self.black_player_id == 7:  # 策略网络
            self.black_player = PolicyNetPlayer()
        elif self.black_player_id == 8:  # 价值网络
            self.black_player = ValueNetPlayer()
        elif self.black_player_id == 9:  # 阿尔法狗
            self.black_player = AlphaGoPlayer(model_path='models/model.pdparams')
        elif self.black_player_id == 10:  # 幼生阿尔法狗（与阿尔法狗只有参数路径不同）
            self.black_player = AlphaGoPlayer(model_path='models/model.pdparams')  # 暂时用相同的参数
        else:  # 暂未实现
            self.black_player = Player()
        self.black_player.allow = pre_player_allow
        self.info_button_and_area = self.draw_info()
        if self.game_allow and self.turn() == govars.BLACK:
            # 在游戏进行状态下切换玩家会导致上一次落子取消
            self.restart = True  # 切换对手时会打开重置标志

    def fct_for_white_player(self):
        SOUNDS['button'].play()
        self.white_player_id += 1
        self.white_player_id %= len(PLAYERS)
        pre_player_allow = self.white_player.allow
        # 将当前Player设置为响应Player
        if self.white_player_id == 0:  # 人类玩家
            self.white_player = HumanPlayer()
        elif self.white_player_id == 1:  # 随机落子
            self.white_player = RandomPlayer()
        elif self.white_player_id == 2:  # 蒙特卡洛400
            self.white_player = MCTSPlayer(n_playout=40)
        elif self.white_player_id == 3:  # 蒙特卡洛800
            self.white_player = MCTSPlayer(n_playout=800)
        elif self.white_player_id == 4:  # 蒙特卡洛1600
            self.white_player = MCTSPlayer(n_playout=1600)
        elif self.white_player_id == 5:  # 蒙特卡洛3200
            self.white_player = MCTSPlayer(n_playout=3200)
        elif self.white_player_id == 6:  # 蒙特卡洛6400
            self.white_player = MCTSPlayer(n_playout=6400)
        elif self.white_player_id == 7:  # 策略网络
            self.white_player = PolicyNetPlayer()
        elif self.white_player_id == 8:  # 价值网络
            self.white_player = ValueNetPlayer()
        elif self.white_player_id == 9:  # 阿尔法狗
            self.white_player = AlphaGoPlayer(model_path='models/model.pdparams')
        elif self.white_player_id == 10:  # 幼生阿尔法狗（与阿尔法狗只有参数路径不同）
            self.white_player = AlphaGoPlayer(model_path='models/model.pdparams')  # 暂时用相同的参数
        else:  # 暂未实现
            self.white_player = Player()
        self.white_player.allow = pre_player_allow
        self.info_button_and_area = self.draw_info()
        if self.game_allow and self.turn() == govars.WHITE:
            # 在游戏进行状态下切换玩家会导致上一次落子取消
            self.restart = True

    def fct_for_music_choose(self):
        SOUNDS['button'].play()
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
        MUSICS[self.music_id][1].play()
        self.info_button_and_area = self.draw_info()

    def fct_for_music_control(self):
        SOUNDS['button'].play()
        self.music_control_id += 1
        self.music_control_id %= len(MUSIC_CONTROLS)
        if self.music_control_id == 0:  # 说明音乐控制按钮上一次为音乐关
            # 须直接将音乐打开
            MUSICS[self.music_id][1].play()
        self.info_button_and_area = self.draw_info()

    def fct_for_play_game(self):
        # 当开始游戏按钮被点击
        SOUNDS['button'].play()
        if not self.game_allow:  # 在game_allow为False情况下，开始游戏按钮点击才有用
            self.reset()
            self.state_history = []
            self.action_history = []
            self.game_allow = True
            self.black_player.allow = True
            self.draw_board()
            self.draw_tip()

    def fct_for_pass(self):
        # pass一手
        SOUNDS['button'].play()
        if self.game_allow:  # 游戏开始后，弃一手按钮才有用
            if not self.current_player_type([HumanPlayer]):
                self.restart = True
            else:  # 如果当前玩家是人类玩家，则会允许对手落子（因为自己会pass）
                if self.get_current_player() == govars.BLACK:
                    self.white_player.allow = True
                elif self.get_current_player() == govars.WHITE:
                    self.black_player.allow = True
            self.play_step(self.size * self.size)
            self.draw_tip()

    def fct_for_regret(self):
        # 悔棋
        SOUNDS['button'].play()
        if self.game_allow:
            if len(self.state_history) > 2:
                self.state_ = self.state_history[-2]
                self.state_history = self.state_history[:-2]
                action = self.action_history[-3]
                self.action_history = self.action_history[:-2]
                # self.simulate_board_state = np.copy(self.state_)
                self.draw_board()
                self.draw_pieces()
                self.draw_mark(action)
                self.draw_tip()
                if not self.current_player_type([HumanPlayer]):
                    self.restart = True
            elif len(self.state_history) == 2:
                self.state_ = self.state_history[-2]
                self.state_history = self.state_history[:-2]
                self.action_history = self.action_history[:-2]
                # self.simulate_board_state = np.copy(self.state_)
                self.draw_board()
                self.draw_pieces()
                self.draw_tip()
                if not self.current_player_type([HumanPlayer]):
                    self.restart = True

    def fct_for_restart(self):
        SOUNDS['button'].play()
        # 当重新开始按钮被点击
        if not self.current_player_type([HumanPlayer]):
            self.restart = True  # 记录重新开始按钮被点击
        self.reset()
        if not self.game_allow:
            self.black_player.allow = True
        self.game_allow = True  # 游戏开始
        self.white_player.allow = False
        self.state_history = []  # 历史记录置空
        self.action_history = []
        # self.simulate_board_state = np.copy(self.state_)
        self.draw_board()
        self.draw_tip()  # 更改落子提示太极图

    def fct_for_new_game_1(self):
        SOUNDS['button'].play()
        # 保存音乐信息
        music_id = self.music_id
        music_control_id = self.music_control_id
        new_game_size = self.size
        # 初始化
        if self.size == 9:
            new_game_size = 13
        else:
            new_game_size = 9
        self.__init__(new_game_size, komi=self.komi, reward_method=self.reward_method, mode=self.mode)
        self.music_id = music_id
        self.music_control_id = music_control_id
        self.draw_board()
        self.draw_tip()
        self.info_button_and_area = self.draw_info()
        self.button_and_area = self.draw_button_area()

    def fct_for_new_game_2(self):
        SOUNDS['button'].play()
        # 保存音乐信息
        music_id = self.music_id
        music_control_id = self.music_control_id
        new_game_size = self.size
        # 初始化
        if self.size == 19:
            new_game_size = 13
        else:
            new_game_size = 19
        self.__init__(new_game_size, komi=self.komi, reward_method=self.reward_method, mode=self.mode)
        self.music_id = music_id
        self.music_control_id = music_control_id
        self.draw_board()
        self.draw_tip()
        self.info_button_and_area = self.draw_info()
        self.button_and_area = self.draw_button_area()

    def fct_for_train_alphago(self):
        # 点击训练幼生阿尔法狗按钮，进入训练界面
        SOUNDS['button'].play()
        self.__init__(self.size, komi=self.komi, reward_method=self.reward_method, mode=self.mode)
        self.trainer = TrainPipeline(self, n_playout=100, model_path='model2.pdparams')
        self.trainer.run()

    def fct_for_exit(self):
        # 当退出游戏按钮被点击
        sys.exit()

    def sound_load(self):
        global SOUNDS, MUSICS, SOUNDS_ALL, MUSICS_ALL
        try:
            for sound in SOUNDS_ALL:
                SOUNDS[sound.lower()] = pygame.mixer.Sound('assets/audios/' + sound + '.wav')
            for music in MUSICS_ALL:
                MUSICS.append([music, pygame.mixer.Sound('assets/musics/' + music + '.mp3')])
        except:
            print("音效系统加载失败！")


if __name__ == '__main__':
    go_game = GoGameState(mode='play')
    while True:
        for event in pygame.event.get():
            pass
        pygame.display.update()

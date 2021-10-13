# -*- coding: utf-8 -*-
# @Time    : 2021/9/30 14:32
# @Author  : He Ruizhi
# @File    : go_engine.py
# @Software: PyCharm

from GymGo.gym_go import govars, gogame
from typing import Union, List, Tuple
import numpy as np
from scipy import ndimage

surround_struct = np.array([[0, 1, 0],
                            [1, 0, 1],
                            [0, 1, 0]])

eye_struct = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])

corner_struct = np.array([[1, 0, 1],
                          [0, 0, 0],
                          [1, 0, 1]])
BLACK = govars.BLACK
WHITE = govars.WHITE


class GoEngine:
    def __init__(self, board_size: int = 9,
                 komi=7.5,
                 record_step: int = 4,
                 state_format: str = "separated",
                 record_last: bool = True):
        """
        围棋引擎初始化

        :param board_size: 棋盘大小，默认为9
        :param komi: 黑棋贴目数，默认黑贴7.5目（3又3/4子）
        :param record_step: 记录棋盘历史状态步数，默认为4
        :param state_format: 记录棋盘历史状态格式
                            【separated：黑白棋子分别记录在不同的矩阵中，[黑棋，白棋，下一步落子方，上一步落子位置(可选)]】
                            【merged：黑白棋子记录在同一个矩阵中，[棋盘棋子分布(黑1白-1)，下一步落子方，上一步落子位置(可选)]】
        :param record_last: 是否记录上一步落子位置
        """
        assert state_format in ["separated", "merged"],\
            "state_format can only be 'separated' or 'merged', but received: {}".format(state_format)

        self.board_size = board_size
        self.komi = komi
        self.record_step = record_step
        self.state_format = state_format
        self.record_last = record_last
        self.current_state = gogame.init_state(board_size)
        # 保存棋盘状态，用于悔棋
        self.board_state_history = []
        # 保存历史动作，用于悔棋
        self.action_history = []

        if state_format == "separated":
            record_step *= 2
        self.state_channels = record_step + 2 if record_last else record_step + 1
        self.board_state = np.zeros((self.state_channels, board_size, board_size))
        self.done = False

    def reset(self) -> np.ndarray:
        """重置current_state, board_state, board_state_history, action_history"""
        self.current_state = gogame.init_state(self.board_size)
        self.board_state = np.zeros((self.state_channels, self.board_size, self.board_size))
        self.board_state_history = []
        self.action_history = []
        self.done = False
        return np.copy(self.current_state)

    def step(self, action: Union[List[int], Tuple[int], int, None]) -> np.ndarray:
        """
        围棋落子

        :param action: 下一步落子位置
        :return:
        """
        assert not self.done
        if isinstance(action, tuple) or isinstance(action, list) or isinstance(action, np.ndarray):
            assert 0 <= action[0] < self.board_size
            assert 0 <= action[1] < self.board_size
            action = self.board_size * action[0] + action[1]
        elif isinstance(action, int):
            assert 0 <= action <= self.board_size ** 2
        elif action is None:
            action = self.board_size ** 2

        self.current_state = gogame.next_state(self.current_state, action, canonical=False)
        # 更新self.board_state
        self.board_state = self._update_state_step(action)
        # 存储历史状态
        self.board_state_history.append(np.copy(self.current_state))
        # 存储历史动作
        self.action_history.append(action)
        self.done = gogame.game_ended(self.current_state)
        return np.copy(self.current_state)

    def _update_state_step(self, action: int) -> np.ndarray:
        """
        更新self.board_state，须在更新完self.current_state之后更新self.board_state

        :param action: 下一步落子位置，1d-action
        :return:
        """
        if self.state_format == "separated":
            # 根据上一步落子方更新self.board_state(因为self.current_state已经更新完毕)
            if self.turn() == govars.WHITE:
                # 根据更新过后的self.current_state，下一步落子方为白方，则上一步落子方为黑方
                self.board_state[:self.record_step - 1] = np.copy(self.board_state[1:self.record_step])
                self.board_state[self.record_step - 1] = np.copy(self.current_state[govars.BLACK])
            else:
                # 根据更新过后的self.current_state，下一步落子方为黑方，则上一步落子方为白方
                self.board_state[self.record_step: self.record_step * 2 - 1] = \
                    np.copy(self.board_state[self.record_step + 1: self.record_step * 2])
                self.board_state[self.record_step * 2 - 1] = np.copy(self.current_state[govars.WHITE])
        elif self.state_format == "merged":
            self.board_state[:self.record_step - 1] = np.copy(self.board_state[1:self.record_step])
            current_state = self.current_state[[govars.BLACK, govars.WHITE]]
            current_state[govars.WHITE] *= -1
            self.board_state[self.record_step - 1] = np.sum(current_state, axis=0)

        if self.record_last:
            # 更新下一步落子方
            self.board_state[-2] = np.copy(self.current_state[govars.TURN_CHNL])
            # 更新上一步落子位置
            self.board_state[-1] = np.zeros((self.board_size, self.board_size))
            # 上一步不为pass
            if action != self.board_size ** 2:
                # 将action转换成position
                position = action // self.board_size, action % self.board_size
                self.board_state[-1, position[0], position[1]] = 1
        else:
            # 更新下一步落子方
            self.board_state[-1] = np.copy(self.current_state[govars.TURN_CHNL])
        return np.copy(self.board_state)

    def board_state(self) -> np.ndarray:
        """用于训练神经网络的棋盘状态矩阵"""
        return np.copy(self.board_state)

    def game_ended(self) -> bool:
        """游戏是否结束"""
        return self.done

    def winner(self) -> int:
        """获胜方，游戏未结束返回-1"""
        if not self.done:
            return -1
        else:
            winner = self.winning()
            winner = govars.BLACK if winner == 1 else govars.WHITE
            return winner

    def action_valid(self, action) -> bool:
        """判断action是否合法"""
        return self.valid_moves()[action]

    def valid_move_idcs(self) -> np.ndarray:
        """下一步落子有效位置的id"""
        valid_moves = self.valid_moves()
        return np.argwhere(valid_moves).flatten()

    def advanced_valid_move_idcs(self) -> np.ndarray:
        """下一步落子的非真眼有效位置的id"""
        advanced_valid_moves = self.advanced_valid_moves()
        return np.argwhere(advanced_valid_moves).flatten()

    def uniform_random_action(self) -> np.ndarray:
        """随机选择落子位置"""
        valid_move_idcs = self.valid_move_idcs()
        return np.random.choice(valid_move_idcs)

    def advanced_uniform_random_action(self) -> np.ndarray:
        """不填真眼的随机位置"""
        advanced_valid_move_idcs = self.advanced_valid_move_idcs()
        return np.random.choice(advanced_valid_move_idcs)

    def turn(self) -> int:
        """下一步落子方"""
        return gogame.turn(self.current_state)

    def valid_moves(self) -> np.ndarray:
        """下一步落子的有效位置"""
        return gogame.valid_moves(self.current_state)

    def advanced_valid_moves(self):
        """下一步落子的非真眼有效位置"""
        valid_moves = 1 - self.current_state[govars.INVD_CHNL]
        eyes_mask = 1 - self.eyes()
        return np.append((valid_moves * eyes_mask).flatten(), 1)

    def winning(self):
        """
        当游戏结束之后，从黑方角度看待，上一步落子后，哪一方胜利
        黑胜：1 白胜：-1
        """
        return gogame.winning(self.current_state, self.komi)

    def areas(self):
        """black_area, white_area"""
        return gogame.areas(self.current_state)

    def eyes(self):
        """
        下一步落子方的真眼位置
        1.如果在角上或者边上，则需要对应8个最近位置均有下一步落子方的棋子；
        2.如果不在边上和角上，则需要对应4个最近边全有下一步落子方的棋子，且至少有三个角有下一步落子方的棋子；
        3.所判断的位置没有棋子
        """
        board_shape = self.current_state.shape[1:]

        side_mask = np.zeros(board_shape)
        side_mask[[0, -1], :] = 1
        side_mask[:, [0, -1]] = 1
        nonside_mask = 1 - side_mask

        # 下一步落子方
        next_player = self.turn()
        # next_player的棋子分布矩阵
        next_player_pieces = self.current_state[next_player]
        # 棋盘所有有棋子的分布矩阵，有棋子则相应位置为1
        all_pieces = np.sum(self.current_state[[govars.BLACK, govars.WHITE]], axis=0)
        # 棋盘上所有空交叉点的分布矩阵，空交叉点位置为1
        empties = 1 - all_pieces

        # 对于边角位置
        side_matrix = ndimage.convolve(next_player_pieces, eye_struct, mode='constant', cval=1) == 8
        side_matrix = side_matrix * side_mask
        # 对于非边角位置
        nonside_matrix = ndimage.convolve(next_player_pieces, surround_struct, mode='constant', cval=1) == 4
        nonside_matrix *= ndimage.convolve(next_player_pieces, corner_struct, mode='constant', cval=1) > 2
        nonside_matrix = nonside_matrix * nonside_mask

        return empties * (side_matrix + nonside_matrix)

    def all_symmetries(self) -> List[np.ndarray]:
        """board_state的8种等价表示"""
        return gogame.all_symmetries(np.copy(self.board_state))

    @staticmethod
    def array_symmetries(array: np.ndarray) -> List[np.ndarray]:
        """
        指定array的8种旋转表示

        :param array: A (C, BOARD_SIZE, BOARD_SIZE) numpy array, where C is any number
        :return:
        """
        return gogame.all_symmetries(array)

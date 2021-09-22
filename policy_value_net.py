# -*- coding: utf-8 -*-
# @Time    : 2021/3/29 21:01
# @Author  : He Ruizhi
# @File    : policy_value_net.py
# @Software: PyCharm

import numpy as np
import paddle


class PolicyValueNet(paddle.nn.Layer):
    def __init__(self, input_channels: int = 10,
                 board_size: int = 9):
        """

        :param input_channels: 输入的通道数，默认为10。双方最近4步，再加一个表示当前落子方的平面，再加上一个最近一手位置的平面
        :param board_size: 棋盘大小
        """
        super(PolicyValueNet, self).__init__()

        # AlphaGo Zero网络架构：一个身子，两个头
        # 特征提取网络
        self.conv_layer = paddle.nn.Sequential(
            paddle.nn.Conv2D(in_channels=input_channels, out_channels=32, kernel_size=3, padding=1),
            paddle.nn.ReLU(),
            paddle.nn.Conv2D(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            paddle.nn.ReLU(),
            paddle.nn.Conv2D(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            paddle.nn.ReLU()
        )

        # 策略网络部分
        self.policy_layer = paddle.nn.Sequential(
            paddle.nn.Conv2D(in_channels=128, out_channels=8, kernel_size=1),
            paddle.nn.ReLU(),
            paddle.nn.Flatten(),
            paddle.nn.Linear(in_features=9*9*8, out_features=256),
            paddle.nn.ReLU(),
            paddle.nn.Linear(in_features=256, out_features=board_size*board_size+1),
            paddle.nn.Softmax()
        )

        # 价值网络部分
        self.value_layer = paddle.nn.Sequential(
            paddle.nn.Conv2D(in_channels=128, out_channels=4, kernel_size=1),
            paddle.nn.ReLU(),
            paddle.nn.Flatten(),
            paddle.nn.Linear(in_features=9*9*4, out_features=128),
            paddle.nn.ReLU(),
            paddle.nn.Linear(in_features=128, out_features=64),
            paddle.nn.ReLU(),
            paddle.nn.Linear(in_features=64, out_features=1),
            paddle.nn.Tanh()
        )

    def forward(self, x):
        x = self.conv_layer(x)
        policy = self.policy_layer(x)
        value = self.value_layer(x)
        return policy, value

    def policy_value_fn(self, simulate_game_state):
        """

        :param simulate_game_state:
        :return:
        """
        legal_positions = simulate_game_state.get_availables()  # 合法的落子位置
        current_state = paddle.to_tensor(simulate_game_state.get_board_state_for_nn()[np.newaxis], dtype='float32')
        act_probs, value = self.forward(current_state)
        act_probs = zip(legal_positions, act_probs.numpy().flatten()[legal_positions])
        return act_probs, value

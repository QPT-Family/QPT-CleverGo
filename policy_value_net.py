# -*- coding: utf-8 -*-
# @Time    : 2021/3/29 21:01
# @Author  : He Ruizhi
# @File    : policy_value_net.py
# @Software: PyCharm

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.regularizers import l2
from tensorflow.keras.initializers import RandomUniform
import numpy as np


class PolicyValueNet:
    def __init__(self, channel_num=10, board_size=9, lr=1e-3):
        # 输入的通道数，默认为10。双方最近4步，再加一个表示当前落子方的平面，再加上一个最近一手位置的平面
        self.channel_num = channel_num
        # 棋盘大小
        self.board_size = board_size
        self.l2_const = 1e-4  # l2正则项比例因子
        self.creak_network()
        self.model_filename = 'models/model.h5'
        self.lr = lr
        self._loss_train_op()

    def creak_network(self):
        network_input = network = tf.keras.Input((self.channel_num, self.board_size, self.board_size))

        # 卷积层部分
        network = layers.Conv2D(filters=32, kernel_size=(3, 3), padding='same', data_format='channels_first',
                                activation='relu', kernel_regularizer=l2(self.l2_const),
                                kernel_initializer=RandomUniform())(network)
        network = layers.Conv2D(filters=64, kernel_size=(3, 3), padding='same', data_format='channels_first',
                                activation='relu', kernel_regularizer=l2(self.l2_const),
                                kernel_initializer=RandomUniform())(network)
        network = layers.Conv2D(filters=128, kernel_size=(3, 3), padding='same', data_format='channels_first',
                                activation='relu', kernel_regularizer=l2(self.l2_const),
                                kernel_initializer=RandomUniform())(network)

        # 策略网络部分
        policy_net = layers.Conv2D(filters=8, kernel_size=(1, 1), data_format='channels_first', activation='relu',
                                   kernel_regularizer=l2(self.l2_const), kernel_initializer=RandomUniform())(network)
        policy_net = layers.Flatten()(policy_net)
        policy_net = layers.Dense(256, use_bias=True, activation='relu', kernel_regularizer=l2(self.l2_const),
                                  kernel_initializer=RandomUniform())(policy_net)
        policy_net = layers.Dense(self.board_size * self.board_size + 1, activation='softmax',
                                  kernel_regularizer=l2(self.l2_const), kernel_initializer=RandomUniform())(policy_net)

        # 价值网络部分
        value_net = layers.Conv2D(filters=4, kernel_size=(1, 1), data_format='channels_first', activation='relu',
                                  kernel_regularizer=l2(self.l2_const), kernel_initializer=RandomUniform())(network)
        value_net = layers.Flatten()(value_net)
        value_net = layers.Dense(128, use_bias=True, activation='relu', kernel_regularizer=l2(self.l2_const),
                                 kernel_initializer=RandomUniform())(value_net)
        value_net = layers.Dense(64, use_bias=True, activation='relu', kernel_regularizer=l2(self.l2_const),
                                 kernel_initializer=RandomUniform())(value_net)
        value_net = layers.Dense(1, use_bias=True, activation='tanh', kernel_regularizer=l2(self.l2_const),
                                 kernel_initializer=RandomUniform())(value_net)

        self.model = tf.keras.Model(network_input, [policy_net, value_net])

        def policy_value(batch_board_state):
            policy, value = self.model(batch_board_state)
            return policy.numpy(), value.numpy()
        self.policy_value = policy_value

    def policy_value_fn(self, simulate_game_state):
        """
        返回每个动作的概率以及节点价值
        :param simulate_game_state:
        :return:
        """
        legal_positions = simulate_game_state.get_availables()  # 合法的落子位置
        current_state = simulate_game_state.get_board_state_for_nn()
        act_probs, value = self.policy_value(current_state[np.newaxis])
        act_probs = zip(legal_positions, act_probs.flatten()[legal_positions])
        return act_probs, value

    def _loss_train_op(self):
        """
        三项损失
        loss = (z - v)^2 + pi^T * log(p) + c||theta||^2
        :return:
        """

        opt = tf.keras.optimizers.Adam(self.lr)
        losses = ['categorical_crossentropy', 'mean_squared_error']
        self.model.compile(optimizer=opt, loss=losses)

        def self_entropy(probs):
            return -np.mean(np.sum(probs * np.log(probs + 1e-10), axis=1))

        def train_step(batch_state_input, batch_mcts_probs, batch_winner):
            loss = self.model.evaluate(batch_state_input, [batch_mcts_probs, batch_winner], batch_size=len(batch_state_input),
                                       verbose=0)
            action_probs, _ = self.model(batch_state_input)
            entropy = self_entropy(action_probs)
            # self.model.fit(state_input_union, [mcts_probs_union, winner_union], batch_size=len(state_input), verbose=0)
            self.model.train_on_batch(batch_state_input, [batch_mcts_probs, batch_winner])
            return loss[0], entropy

        self.train_step = train_step

    def load_model(self):

        try:
            self.model.load_weights(self.model_filename)
            print('加载模型权重成功！')
        except:
            print('加载模型权重失败！')

    def save_model(self):
        self.model.save_weights(self.model_filename)
        print('保存权重完成!')


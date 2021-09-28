# -*- coding: utf-8 -*-
# @Time    : 2021/4/3 12:18
# @Author  : He Ruizhi
# @File    : train.py
# @Software: PyCharm

import sys
import threading
sys.path.append('GymGo/')
from collections import deque
from policy_value_net import PolicyValueNet
from player import MCTSPlayer, AlphaGoPlayer
# from weiqi_engine import GoGameState
import numpy as np
import random
from datetime import datetime
from threading import Thread
import time
import paddle

BUFFER_SIZE = 50000
BUTCH_SIZE = 128
# 线程锁，用于对模型参数读取线程同步
LOCK = threading.Lock()


class TrainPipeline:
    def __init__(self, game_state, size=9, lr=1e-2, temp=1.0, n_playout=100, c_puct=5, channel_num=10,
                 model_path='models/model.pdparams'):
        self.size = size  # 棋盘大小
        self.lr = lr  # 学习率
        self.temp = temp  # 蒙特卡洛树搜索温度参数
        self.n_playout = n_playout  # 蒙特卡洛树搜索模拟次数
        self.c_puct = c_puct  # 蒙特卡洛树搜索中计算上置信限的参数
        self.channel_num = channel_num  # 棋盘状态通道数 = (规定历史步数*2 + 2)  （黑白棋子分布、当前落子方、上一步落子位置）
        # (应该初始化两个网络，一个为train状态，一个为eval状态。暂时不用更新)
        # self.policy_value_net = PolicyValueNet(board_size=self.size, input_channels=self.channel_num)
        self.update_model_flag = False  # 记录生成自对弈数据采用的网络是否需要更新参数
        # self.game_state = GoGameState(size=self.size, mode='train', history_step=(channel_num - 2) // 2)
        self.game_state = game_state
        self.player = AlphaGoPlayer(model_path, c_puct=c_puct, n_playout=n_playout, is_selfplay=True)
        self.policy_value_net = self.player.policy_value_net
        self.data_buffer = deque(maxlen=BUFFER_SIZE)
        self.train_step_count = 0
        self.model_path = model_path
        self.opt = paddle.optimizer.Adam(learning_rate=lr, parameters=self.policy_value_net.parameters())
        # 训练开始先加载一次模型参数
        try:
            state_dict = paddle.load(self.model_path)
            self.policy_value_net.load_dict(state_dict)
            print('模型参数加载成功！')
        except:
            print('模型参数加载失败！')

    def collect_self_play_data(self):
        """
        不断生成自对弈数据，并存入DATA_BUFFER
        :return:
        """
        while True:
            play_data = self.self_play_one_game(temp=self.temp)
            play_datas = self.get_equi_data(play_data)
            # self.data_buffer.append(play_datas)
            self.data_buffer.extend(play_datas)
            if self.update_model_flag:
                LOCK.acquire()
                state_dict = paddle.load(self.model_path)
                self.policy_value_net.set_state_dict(state_dict)
                LOCK.release()
                print('加载模型参数一次！')
                self.update_model_flag = False

    def self_play_one_game(self, temp=1.0):
        """
        自对弈一局游戏，并获得对弈数据
        :param temp: 蒙特卡洛树搜索温度参数
        :return:
        """
        states, mcts_probs, current_players = [], [], []

        while True:
            # 获得动作及概率
            move, move_probs = self.player.get_action(self.game_state, temp=temp, return_probs=True)
            # 存数据
            states.append(self.game_state.get_board_state_for_nn())
            mcts_probs.append(move_probs)
            current_players.append(self.game_state.get_current_player())
            # 执行move
            self.game_state.train_step(move)
            end, winner = self.game_state.game_end()
            if end:
                winners = np.zeros(len(current_players))
                if winner != -1:
                    winners[np.array(current_players) == winner] = 1.0
                    winners[np.array(current_players) != winner] = -1.0
                # 重置蒙特卡洛搜索树
                self.player.reset_player()
                # 重置game_state
                self.game_state.reset()
                states = np.array(states)
                mcts_probs = np.array(mcts_probs)
                return zip(states, mcts_probs, winners)

    def get_equi_data(self, play_data):
        """
        通过旋转和翻转来扩增数据
        :param play_data:
        :return:
        """
        extend_data = []
        for state, mcts_porb, winner in play_data:
            for i in [1, 2, 3, 4]:
                # 逆时针旋转
                equi_state = np.array([np.rot90(s, i) for s in state])
                pass_move_prob = mcts_porb[-1]
                equi_mcts_prob = np.rot90(np.flipud(mcts_porb[:-1].reshape(self.size, self.size)), i)
                extend_data.append((equi_state, np.append(np.flipud(equi_mcts_prob).flatten(), pass_move_prob), winner))
                # 翻转
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state, np.append(np.flipud(equi_mcts_prob).flatten(), pass_move_prob), winner))
        return extend_data

    def network_update(self):
        """
        更新网络参数
        :return:
        """
        print('正在自对弈生成训练数据！')
        while True:
            self.network_update_step()
            if (self.train_step_count + 1) % 1000 == 0:  # 训练1000次，保存更新一次网络参数
                LOCK.acquire()
                paddle.save(self.policy_value_net.state_dict(), self.model_path)
                LOCK.release()
                print('模型参数更新一次！')
                # 提示对局数据生成线程要更新参数
                self.update_model_flag = True

    def network_update_step(self):
        """
        更新一次网络参数
        :return:
        """
        if len(self.data_buffer) > BUTCH_SIZE:
            self.train_step_count += 1
            mini_batch = random.sample(self.data_buffer, BUTCH_SIZE)
            state_batch = paddle.to_tensor(np.array([data[0] for data in mini_batch]), dtype='float32')
            mcts_probs_batch = paddle.to_tensor(np.array([data[1] for data in mini_batch]), dtype='float32')
            winner_batch = paddle.to_tensor(np.array([data[2] for data in mini_batch]), dtype='float32')

            act_probs, value = self.policy_value_net(state_batch)
            ce_loss = paddle.nn.functional.cross_entropy(act_probs, mcts_probs_batch,
                                                         soft_label=True, use_softmax=False)
            mse_loss = paddle.nn.functional.mse_loss(value, winner_batch)
            loss = ce_loss + mse_loss

            loss.backward()
            params = self.policy_value_net.parameters()
            grad_sum = np.sum([np.sum(pms.grad.numpy()) for pms in params])
            self.opt.step()
            self.opt.clear_grad()

            print('{} Step:{} Loss:{} CELoss:{} MSELoss:{} GradTotal:{}'.format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.train_step_count, loss.numpy(), ce_loss.numpy(),
                mse_loss.numpy(), grad_sum))
        else:
            time.sleep(60)

    def run(self):
        # 启动生成对局数据线程
        # Thread(target=self.collect_self_play_data).start()
        # self.network_update()
        # 启动神经网络训练线程
        Thread(target=self.network_update).start()
        self.collect_self_play_data()


if __name__ == '__main__':
    training_pipeline = TrainPipeline(n_playout=200)
    training_pipeline.run()

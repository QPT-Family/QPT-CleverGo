import random
import time
from datetime import datetime
from policy_value_net import PolicyValueNet
import os
import paddle
from collections import deque
from player import AlphaGoPlayer
import numpy as np
from threading import Thread


class Trainer:
    def __init__(self, learning_rate=1e-2, batch_size=128, buffer_size=50000, temp=1.0, n_playout=100, c_puct=5,
                 train_model_path='models/my_alpha_go.pdparams'):
        """
        训练阿尔法狗的训练器

        :param learning_rate: 学习率
        :param temp: 蒙特卡洛数搜索温度参数
        :param n_playout: 蒙特卡洛树搜索模拟次数
        :param c_puct: 蒙特卡洛树搜索中计算上置信限的参数
        :param train_model_path: 训练模型的参数路径
        """
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.buffer_size = buffer_size
        self.temp = temp
        self.n_playout = n_playout
        self.c_puct = c_puct
        self.train_model_path = train_model_path
        self.train_step = 0
        self.model_update_step = 0

        # 创建训练数据存储器
        self.data_buffer = deque(maxlen=buffer_size)

        # 创建阿尔法狗
        self.player = AlphaGoPlayer(train_model_path, c_puct, n_playout, is_selfplay=True)
        # 阿尔法狗网络权重更新信号
        self.player_update = False

        # 创建待训练网络
        self.train_net = PolicyValueNet()
        self.train_net.train()
        # 加载训练网络参数
        if os.path.exists(train_model_path):
            state_dict = paddle.load(train_model_path)
            self.train_net.set_state_dict(state_dict)

        # 创建训练优化器
        self.optimizer = paddle.optimizer.Momentum(learning_rate=learning_rate, parameters=self.train_net.parameters())

    def self_play(self, game):
        Thread(target=self._self_play, args=(game, ), daemon=True).start()

    def _self_play(self, game):
        """不断自对弈生成训练数据"""

        game.info_display.draw('{}  你的阿尔法狗正在和自己下棋！'.format(datetime.now().strftime(r'%m-%d %H:%M:%S')))
        while True:
            if game.surface_state == 'play':
                break

            play_data = self._self_play_one_game(game)
            if play_data is not None:
                play_datas = self.get_equi_data(play_data)
                self.data_buffer.extend(play_datas)
            if self.player_update:
                state_dict = paddle.load(self.train_model_path)
                self.player.policy_value_net.set_state_dict(state_dict)
                self.player_update = False

    def _self_play_one_game(self, game):
        """自对弈依据游戏，并获取对弈数据"""
        states, mcts_probs, current_players = [], [], []

        while True:
            if game.surface_state == 'play':
                break

            # 获取动作及概率
            move, move_probs = self.player.get_action(game, temp=self.temp, return_probs=True)
            # 存数据
            states.append(game.train_game_state.get_board_state())
            mcts_probs.append(move_probs)
            current_players.append(game.train_game_state.turn())
            # 执行落子
            if game.surface_state == 'train':
                game.train_step(move)

            end, winner = game.train_game_state.game_ended(), game.train_game_state.winner()
            if end:
                winners = np.zeros(len(current_players))
                if winner != -1:
                    winners[np.array(current_players) == winner] = 1.0
                    winners[np.array(current_players) != winner] = -1.0
                # 重置蒙特卡洛搜索树
                self.player.reset_player()
                # 重置train_game_state
                game.train_game_state.reset()
                states = np.array(states)
                mcts_probs = np.array(mcts_probs)
                return zip(states, mcts_probs, winners)

    @staticmethod
    def get_equi_data(play_data):
        """通过旋转和翻转来扩增数据"""
        extend_data = []
        for state, mcts_porb, winner in play_data:
            board_size = state.shape[-1]
            for i in [1, 2, 3, 4]:
                # 逆时针旋转
                equi_state = np.array([np.rot90(s, i) for s in state])
                pass_move_prob = mcts_porb[-1]
                equi_mcts_prob = np.rot90(np.flipud(mcts_porb[:-1].reshape(board_size, board_size)), i)
                extend_data.append((equi_state, np.append(np.flipud(equi_mcts_prob).flatten(), pass_move_prob), winner))
                # 翻转
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state, np.append(np.flipud(equi_mcts_prob).flatten(), pass_move_prob), winner))
        return extend_data

    def network_update(self, game):
        Thread(target=self._network_update, args=(game, ), daemon=True).start()

    def _network_update(self, game):
        """不断更新网络参数"""
        while True:
            if game.surface_state == 'play':
                break

            self.update_step()
            if (self.train_step + 1) % 1000 == 0:
                self.model_update_step += 1
                paddle.save(self.train_net.state_dict(), self.train_model_path)
                self.player_update = True

                game.info_display.draw('{}  阿尔法狗成长阶段{}！'.format(
                    datetime.now().strftime(r'%m-%d %H:%M:%S'), self.model_update_step))

    def update_step(self):
        """更新网络参数一次"""
        if len(self.data_buffer) > self.batch_size:
            self.train_step += 1
            batch = random.sample(self.data_buffer, self.batch_size)
            state_batch = paddle.to_tensor([data[0] for data in batch], dtype='float32')
            mcts_probs_batch = paddle.to_tensor([data[1] for data in batch], dtype='float32')
            winner_batch = paddle.to_tensor([data[2] for data in batch], dtype='float32')

            act_probs, value = self.train_net(state_batch)
            ce_loss = paddle.nn.functional.cross_entropy(act_probs, mcts_probs_batch,
                                                         soft_label=True, use_softmax=False)
            mse_loss = paddle.nn.functional.mse_loss(value, winner_batch)
            loss = ce_loss + mse_loss

            loss.backward()
            self.optimizer.step()
            self.optimizer.clear_grad()

            print('{} Step:{} CELoss:{} MSELoss:{} Loss:{}'.format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.train_step,
                ce_loss.numpy(), mse_loss.numpy(), loss.numpy()
            ))
        else:
            time.sleep(60)

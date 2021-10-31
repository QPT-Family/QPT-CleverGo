from datetime import datetime
import os
import paddle
from player import AlphaGoPlayer
import numpy as np
from threading import Thread
from threading import Lock
import go_engine

lock = Lock()


class Trainer:
    def __init__(self, epochs=10, learning_rate=1e-3, batch_size=128, temp=1.0, n_playout=100, c_puct=5,
                 train_model_path='models/my_alpha_go.pdparams'):
        """
        训练阿尔法狗的训练器

        :param epochs: 每自对弈一局，对样本迭代训练的epoch数
        :param learning_rate: 学习率
        :param temp: 蒙特卡洛数搜索温度参数
        :param n_playout: 蒙特卡洛树搜索模拟次数
        :param c_puct: 蒙特卡洛树搜索中计算上置信限的参数
        :param train_model_path: 训练模型的参数路径
        """
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.temp = temp
        self.n_playout = n_playout
        self.c_puct = c_puct
        self.train_model_path = train_model_path
        self.train_step = 0
        self.model_update_step = 0

        # 创建阿尔法狗
        self.player = AlphaGoPlayer(train_model_path, c_puct, n_playout, is_selfplay=True)

        # 创建训练优化器
        self.optimizer = paddle.optimizer.Momentum(learning_rate=learning_rate,
                                                   parameters=self.player.policy_value_net.parameters())

    def start(self, game):
        """启动阿尔法狗训练线程"""
        Thread(target=self._train, args=(game,), daemon=True).start()

    def _train(self, game):
        """训练阿尔法狗"""

        # 加载训练网络参数
        if os.path.exists(self.train_model_path):
            state_dict = paddle.load(self.train_model_path)
            self.player.policy_value_net.set_state_dict(state_dict)
            print('加载模型权重成功！')
            lock.acquire()
            if game.surface_state == 'train':
                game.info_display.draw('{}  你成功唤醒了你的幼生阿尔法狗！'.format(datetime.now().strftime(r'%m-%d %H:%M:%S')))
            lock.release()
        else:
            print('未找到模型参数！')
            lock.acquire()
            if game.surface_state == 'train':
                game.info_display.draw('{}  你成功领养了一只幼生阿尔法狗！'.format(datetime.now().strftime(r'%m-%d %H:%M:%S')))
            lock.release()

        while True:
            if game.surface_state == 'play':
                break

            # 自对弈一局
            lock.acquire()
            if game.surface_state == 'train':
                game.info_display.draw('{}  你的阿尔法狗开始了自对弈！'.format(datetime.now().strftime(r'%m-%d %H:%M:%S')))
            lock.release()
            play_datas = self.self_play_one_game(game)
            if play_datas is not None:
                play_datas = self.get_equi_data(play_datas)
                # 训练网络
                self.update_network(game, play_datas)
                paddle.save(self.player.policy_value_net.state_dict(), self.train_model_path)
                self.model_update_step += 1
                print('保存模型权重一次！')
                lock.acquire()
                if game.surface_state == 'train':
                    game.info_display.draw('{}  阿尔法狗成长阶段{}！'.format(
                        datetime.now().strftime(r'%m-%d %H:%M:%S'), self.model_update_step))
                lock.release()

    def self_play_one_game(self, game):
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
            lock.acquire()
            if game.surface_state == 'train':
                game.train_step(move)
            lock.release()

            end, winner = game.train_game_state.game_ended(), game.train_game_state.winner()
            if end:
                print('{}胜！'.format('黑' if winner == go_engine.BLACK else '白'))
                lock.acquire()
                if game.surface_state == 'train':
                    game.info_display.draw('{}  {}胜！'.format(
                        datetime.now().strftime(r'%m-%d %H:%M:%S'), '黑' if winner == go_engine.BLACK else '白'))
                lock.release()

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

    def update_network(self, game, play_datas):
        """更新网络参数"""
        self.player.policy_value_net.train()
        for epoch in range(self.epochs):
            if game.surface_state == 'play':
                break

            np.random.shuffle(play_datas)
            for i in range(len(play_datas) // self.batch_size + 1):
                self.train_step += 1

                batch = play_datas[i * self.batch_size:(i + 1) * self.batch_size]
                if len(batch) == 0:
                    continue
                state_batch = paddle.to_tensor([data[0] for data in batch], dtype='float32')
                mcts_probs_batch = paddle.to_tensor([data[1] for data in batch], dtype='float32')
                winner_batch = paddle.to_tensor([data[2] for data in batch], dtype='float32')

                act_probs, value = self.player.policy_value_net(state_batch)
                ce_loss = paddle.nn.functional.cross_entropy(act_probs, mcts_probs_batch,
                                                             soft_label=True, use_softmax=False)
                mse_loss = paddle.nn.functional.mse_loss(value, winner_batch)
                loss = ce_loss + mse_loss

                loss.backward()
                self.optimizer.step()
                self.optimizer.clear_grad()

                print('{} Step:{} CELoss:{} MSELoss:{} Loss:{}'.format(
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.train_step,
                    ce_loss.numpy(), mse_loss.numpy(), loss.numpy()))
        self.player.policy_value_net.eval()

# -*- coding: utf-8 -*-
# @Time    : 2021/3/8 18:51
# @Author  : He Ruizhi
# @File    : player.py
# @Software: PyCharm

from threading import Thread
import numpy as np
from time import sleep
from mcts import MCTS, evaluate_rollout
from gym_go import govars


class Player:
    def __init__(self):
        self.allow = False

    def play(self, game_state):
        if game_state.game_allow:
            # daemon=True可以使得父进程结束时，所有子进程全部退出，使得点击退出游戏按钮后，不用等待子进程结束
            Thread(target=self.step, args=(game_state, ), daemon=True).start()

    def step(self, game_state):
        """
        根据当前游戏状态，获得执行动作
        :param game_state: 游戏模拟器对象
        :return:
        """
        print('Hello!')


class HumanPlayer(Player):
    def __init__(self):
        super().__init__()

    def step_with_mouse(self, game_state, mouse_pos):
        action = game_state.mouse_pos_to_action(mouse_pos)
        if action is not None and game_state.action_valid(action):  # 鼠标点击位置合法
            game_state.action_next = action
        else:  # 鼠标点击位置不合法，将标志重新打开
            if game_state.get_current_player() == govars.BLACK:
                game_state.black_player.allow = True
            elif game_state.get_current_player() == govars.WHITE:
                game_state.white_player.allow = True


class RandomPlayer(Player):
    def __init__(self):
        super().__init__()

    def step(self, game_state):
        sleep(1)
        game_state.action_next = self.get_action(game_state)

    def get_action(self, game_state):
        # all_valid_moves = game_state.valid_moves()
        # valid_move_idcs = np.argwhere(all_valid_moves).flatten()
        valid_move_idcs = game_state.get_availables_without_eyes()
        if len(valid_move_idcs) > 1:
            valid_move_idcs = valid_move_idcs[:-1]
        action = np.random.choice(valid_move_idcs)
        return action


class MCTSPlayer(Player):
    def __init__(self, c_puct=5, n_playout=20):
        super().__init__()

        def rollout_policy_fn(simulate_game_state):
            # 选择随机动作
            availables = simulate_game_state.get_availables()
            action_probs = np.random.rand(len(availables))
            return zip(availables, action_probs)

        def policy_value_fn(simulate_game_state):
            # 返回均匀概率及通过随机方法获得的节点价值
            availables = simulate_game_state.get_availables()
            action_probs = np.ones(len(availables)) / len(availables)
            return zip(availables, action_probs), evaluate_rollout(simulate_game_state, rollout_policy_fn)

        self.mcts = MCTS(policy_value_fn, c_puct, n_playout)

    def step(self, game_state):
        game_state.action_next = self.get_action(game_state)
        game_state.draw_speed(0, 1)  # 获得动作后将速度区域清空

    def reset_player(self):
        self.mcts.update_with_move(-1)

    def get_action(self, game_state):
        move = self.mcts.get_move(game_state)
        self.mcts.update_with_move(-1)
        return move


class AlphaGoPlayer(Player):
    def __init__(self, policy_value_function, c_puct=5, n_playout=400, is_selfplay=False):
        super().__init__()
        self.mcts = MCTS(policy_value_function, c_puct, n_playout)
        self.is_selfplay = is_selfplay

    def reset_player(self):
        self.mcts.update_with_move(-1)

    def setp(self, game_state):
        game_state.action_next = self.get_action(game_state)
        game_state.draw_speed(0, 1)

    def get_action(self, game_state, temp=1e-3, return_probs=False):
        move_probs = np.zeros(game_state.size * game_state.size + 1)
        acts, probs = self.mcts.get_move_probs(game_state, temp)
        move_probs[list(acts)] = probs
        if self.is_selfplay:
            # 增加Dirichlet噪声用于探索（在训练时候）
            move = np.random.choice(acts, p=0.75*probs + 0.25*np.random.dirichlet(0.3*np.ones(len(probs))))
            # 更新蒙特卡洛搜索树
            self.mcts.update_with_move(move)  # 因为在生成自对弈棋谱时，落子是黑白交替，均由自己做出决策
        else:
            move = np.random.choice(acts, p=probs)
            self.mcts.update_with_move(-1)  # 与其它对手对弈时，只控制黑方或白方落子，因此每步均置为-1
        if return_probs:
            return move, move_probs
        else:
            return move

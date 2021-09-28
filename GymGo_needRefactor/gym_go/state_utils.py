import numpy as np
from scipy import ndimage
from scipy.ndimage import measurements

from gym_go import govars

group_struct = np.array([[[0, 0, 0],
                          [0, 0, 0],
                          [0, 0, 0]],
                         [[0, 1, 0],
                          [1, 1, 1],
                          [0, 1, 0]],
                         [[0, 0, 0],
                          [0, 0, 0],
                          [0, 0, 0]]])

surround_struct = np.array([[0, 1, 0],
                            [1, 0, 1],
                            [0, 1, 0]])

eye_struct = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])

corner_struct = np.array([[1, 0, 1],
                          [0, 0, 0],
                          [1, 0, 1]])

neighbor_deltas = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])


def compute_invalid_moves(state, player, ko_protect=None):
    """
    Updates invalid moves in the OPPONENT's perspective（观点、视角）
    1.) Opponent cannot move at a location
        i.) If it's occupied（被占领的）
        i.) If it's protected by ko
    2.) Opponent can move at a location
        i.) If it can kill
    3.) Opponent cannot move at a location
        i.) If it's adjacent to one of their groups with only one liberty and
            not adjacent to other groups with more than one liberty and is completely surrounded
        ii.) If it's surrounded by our pieces and all of those corresponding groups
            move more than one liberty
    """
    # All pieces and empty spaces
    all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)  # 棋盘所有有棋子的分布矩阵，有棋子则相应位置为1
    empties = 1 - all_pieces  # 棋盘上所有空交叉点的分布矩阵，空交叉点位置为1

    # Setup invalid and valid arrays
    possible_invalid_array = np.zeros(state.shape[1:])
    definite_valids_array = np.zeros(state.shape[1:])

    # Get all groups
    all_own_groups, num_own_groups = measurements.label(state[player])  # 自己各块棋子分布矩阵，及自己棋子块数
    all_opp_groups, num_opp_groups = measurements.label(state[1 - player])  # 对手各块棋子分布矩阵，及对手棋子块数
    expanded_own_groups = np.zeros((num_own_groups, *state.shape[1:]))  # (1, *[1, 2]) == (1, 1, 2)
    expanded_opp_groups = np.zeros((num_opp_groups, *state.shape[1:]))

    # Expand the groups such that each group is in its own channel
    for i in range(num_own_groups):  # 将每块棋子放入一个通道中
        expanded_own_groups[i] = all_own_groups == (i + 1)

    for i in range(num_opp_groups):
        expanded_opp_groups[i] = all_opp_groups == (i + 1)

    # Get all liberties in the expanded form
    # 计算每一块棋子的气分布矩阵
    # 其中np.newaxis == None，matrix[None]意思是在第0维增加一个维度
    # all_own_liberties和all_opp_liberties均是三维矩阵，代表每块棋子的气的分布
    all_own_liberties = empties[np.newaxis] * ndimage.binary_dilation(expanded_own_groups, surround_struct[np.newaxis])
    all_opp_liberties = empties[np.newaxis] * ndimage.binary_dilation(expanded_opp_groups, surround_struct[np.newaxis])

    own_liberty_counts = np.sum(all_own_liberties, axis=(1, 2))
    opp_liberty_counts = np.sum(all_opp_liberties, axis=(1, 2))
    # all_own_liberties和all_opp_liberties均是三维矩阵， np.sum( , axis=(1,2))针对每块棋子计算其气数
    # own_liberty_counts和opp_liberty_counts均是一维数组，每个元素代表每块棋的气

    # Possible invalids are on single liberties of opponent groups and on multi-liberties of own groups
    # Definite valids are on single liberties of own groups, multi-liberties of opponent groups
    # or you are not surrounded（站在对手的视角看无效落子的位置）
    possible_invalid_array += np.sum(all_own_liberties[own_liberty_counts > 1], axis=0)
    possible_invalid_array += np.sum(all_opp_liberties[opp_liberty_counts == 1], axis=0)
    # all_own_liberties[own_liberty_counts > 1]指获取所有气大于1的通道（每个通道为一块棋的气分布矩阵）
    # possible_invalid_array为一个二维矩阵

    definite_valids_array += np.sum(all_own_liberties[own_liberty_counts == 1], axis=0)
    definite_valids_array += np.sum(all_opp_liberties[opp_liberty_counts > 1], axis=0)

    # All invalid moves are occupied spaces + (possible invalids minus the definite valids and it's surrounded)
    # 得到哪些位置周围有四个棋子（如果是角落则是两个棋子，边上则三个棋子），通过卷积操作实现。由于surround_struct是中心对称的，
    # 因此下面的卷积操作后surrounded操作为被棋子包围的地方为True，其余地方为False
    surrounded = ndimage.convolve(all_pieces, surround_struct, mode='constant', cval=1) == 4
    invalid_moves = all_pieces + possible_invalid_array * (definite_valids_array == 0) * surrounded
    # 对手落子无效的位置：有棋子的位置 + （所有可能落子无效的位置【对手棋子仅一口气，那个气的位置；自己棋子有多口气，那些气的位置】，排除掉
    # 所有必定有效的位置【自己棋子仅有一口气，那个气的位置；对手棋子有多口气，那些气的位置】，并排除掉没有被棋子包围的位置）
    # 注意是站在对手的观点来看待哪些地方落子合法
    # 如何理解上述对手落子无效的位置规则：比较有难度，需要一定的围棋水平。
    # 首先，落子无效的位置必定是被棋子包围的位置（不管是自己棋子还是对手棋子），在所有被棋子包围的位置，如果该位置是对手一块棋的最后
    # 一口气，且不同时是对手另一块棋的多口气位置，或该位置不是自己棋子最后一口气位置，则该位置为对手落子无效位置。

    # Ko-protection
    if ko_protect is not None:  # 劫争位置禁止落子（自己当前一步棋提劫，对手禁止马上提回）
        invalid_moves[ko_protect[0], ko_protect[1]] = 1
    # 返回一个矩阵，所有值大于0的位置为True。因为possible_invalid_array是所有块棋子的气的累加，
    # 当几块棋的某个气是公共的，相应位置值会大于1
    return invalid_moves > 0


def batch_compute_invalid_moves(batch_state, batch_player, batch_ko_protect):
    """
    Updates invalid moves in the OPPONENT's perspective
    1.) Opponent cannot move at a location
        i.) If it's occupied
        i.) If it's protected by ko
    2.) Opponent can move at a location
        i.) If it can kill
    3.) Opponent cannot move at a location
        i.) If it's adjacent to one of their groups with only one liberty and
            not adjacent to other groups with more than one liberty and is completely surrounded
        ii.) If it's surrounded by our pieces and all of those corresponding groups
            move more than one liberty
    """
    batch_idcs = np.arange(len(batch_state))

    # All pieces and empty spaces
    batch_all_pieces = np.sum(batch_state[:, [govars.BLACK, govars.WHITE]], axis=1)
    batch_empties = 1 - batch_all_pieces

    # Setup invalid and valid arrays
    batch_possible_invalid_array = np.zeros(batch_state.shape[:1] + batch_state.shape[2:])
    batch_definite_valids_array = np.zeros(batch_state.shape[:1] + batch_state.shape[2:])

    # Get all groups
    batch_all_own_groups, _ = measurements.label(batch_state[batch_idcs, batch_player], group_struct)
    batch_all_opp_groups, _ = measurements.label(batch_state[batch_idcs, 1 - batch_player], group_struct)

    batch_data = enumerate(zip(batch_all_own_groups, batch_all_opp_groups, batch_empties))
    for i, (all_own_groups, all_opp_groups, empties) in batch_data:
        own_labels = np.unique(all_own_groups)
        opp_labels = np.unique(all_opp_groups)
        own_labels = own_labels[np.nonzero(own_labels)]
        opp_labels = opp_labels[np.nonzero(opp_labels)]
        expanded_own_groups = np.zeros((len(own_labels), *all_own_groups.shape))
        expanded_opp_groups = np.zeros((len(opp_labels), *all_opp_groups.shape))

        # Expand the groups such that each group is in its own channel
        for j, label in enumerate(own_labels):
            expanded_own_groups[j] = all_own_groups == label

        for j, label in enumerate(opp_labels):
            expanded_opp_groups[j] = all_opp_groups == label

        # Get all liberties in the expanded form
        all_own_liberties = empties[np.newaxis] * ndimage.binary_dilation(expanded_own_groups,
                                                                          surround_struct[np.newaxis])
        all_opp_liberties = empties[np.newaxis] * ndimage.binary_dilation(expanded_opp_groups,
                                                                          surround_struct[np.newaxis])

        own_liberty_counts = np.sum(all_own_liberties, axis=(1, 2))
        opp_liberty_counts = np.sum(all_opp_liberties, axis=(1, 2))

        # Possible invalids are on single liberties of opponent groups and on multi-liberties of own groups
        # Definite valids are on single liberties of own groups, multi-liberties of opponent groups
        # or you are not surrounded
        batch_possible_invalid_array[i] += np.sum(all_own_liberties[own_liberty_counts > 1], axis=0)
        batch_possible_invalid_array[i] += np.sum(all_opp_liberties[opp_liberty_counts == 1], axis=0)

        batch_definite_valids_array[i] += np.sum(all_own_liberties[own_liberty_counts == 1], axis=0)
        batch_definite_valids_array[i] += np.sum(all_opp_liberties[opp_liberty_counts > 1], axis=0)

    # All invalid moves are occupied spaces + (possible invalids minus the definite valids and it's surrounded)
    surrounded = ndimage.convolve(batch_all_pieces, surround_struct[np.newaxis], mode='constant', cval=1) == 4
    invalid_moves = batch_all_pieces + batch_possible_invalid_array * (batch_definite_valids_array == 0) * surrounded

    # Ko-protection
    for i, ko_protect in enumerate(batch_ko_protect):
        if ko_protect is not None:
            invalid_moves[i, ko_protect[0], ko_protect[1]] = 1
    return invalid_moves > 0


def update_pieces(state, adj_locs, player):
    opponent = 1 - player
    killed_groups = []  # 记录杀死的棋子的位置

    all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)  # 棋盘所有有棋子的位置矩阵，有棋子则相应位置为1
    empties = 1 - all_pieces  # 所有没有棋子的位置矩阵，没有棋子，则相应位置为1

    all_opp_groups, _ = ndimage.measurements.label(state[opponent])  # ndimage.measurements.label()将各块棋子分别打上不同的标签

    # Go through opponent groups
    all_adj_labels = all_opp_groups[adj_locs[:, 0], adj_locs[:, 1]]  # 获取所有相邻的标签
    all_adj_labels = np.unique(all_adj_labels)  # 去除数组中的重复数字，并进行升序排序之后输出
    for opp_group_idx in all_adj_labels[np.nonzero(all_adj_labels)]:
        # opp_group_idx指一个某块棋子的标签值
        opp_group = all_opp_groups == opp_group_idx  # opp_group是一个二维数组，其中all_opp_group与opp_group_idx相同的地方为True，其余为False
        # opp_group表明了一块棋在棋盘上的位置
        liberties = empties * ndimage.binary_dilation(opp_group)
        # ndimage.binary_dilation，对二维矩阵中的True值进行扩张，即使得True直接相邻的位置变为True
        # empties * ndimage.binary_dilation(opp_group)获得一块棋的气矩阵
        if np.sum(liberties) <= 0:  # np.sum气总数
            # Killed group
            opp_group_locs = np.argwhere(opp_group)  # 获取杀死棋子的位置
            state[opponent, opp_group_locs[:, 0], opp_group_locs[:, 1]] = 0  # 将矩阵相应位置的值置为0
            killed_groups.append(opp_group_locs)
    return killed_groups


def batch_update_pieces(batch_non_pass, batch_state, batch_adj_locs, batch_player):
    batch_opponent = 1 - batch_player
    batch_killed_groups = []

    batch_all_pieces = np.sum(batch_state[:, [govars.BLACK, govars.WHITE]], axis=1)
    batch_empties = 1 - batch_all_pieces

    # 为所有对局游戏的对手的各块棋子分别打上标签，注意标签从1开始，且在不同局之间是连续、不同的
    batch_all_opp_groups, _ = ndimage.measurements.label(batch_state[batch_non_pass, batch_opponent],
                                                         group_struct)

    batch_data = enumerate(zip(batch_all_opp_groups, batch_all_pieces, batch_empties, batch_adj_locs, batch_opponent))
    for i, (all_opp_groups, all_pieces, empties, adj_locs, opponent) in batch_data:
        killed_groups = []

        # 以下同update_pieces()方法中对应code
        # Go through opponent groups
        all_adj_labels = all_opp_groups[adj_locs[:, 0], adj_locs[:, 1]]
        all_adj_labels = np.unique(all_adj_labels)
        for opp_group_idx in all_adj_labels[np.nonzero(all_adj_labels)]:
            opp_group = all_opp_groups == opp_group_idx
            liberties = empties * ndimage.binary_dilation(opp_group)
            if np.sum(liberties) <= 0:
                # Killed group
                opp_group_locs = np.argwhere(opp_group)
                batch_state[batch_non_pass[i], opponent, opp_group_locs[:, 0], opp_group_locs[:, 1]] = 0
                killed_groups.append(opp_group_locs)

        batch_killed_groups.append(killed_groups)

    return batch_killed_groups


def get_eyes(state, player):
    """获得自己的所有真眼位置：
    1.如果在角上或者边上，则需要对应8个最近位置均有自己的棋子；
    2.如果不在边上和角上，则需要对应4个最近边全有自己的棋子，且至少有三个角有自己的棋子；
    3.所判断的位置没有棋子"""
    row_num, col_num = state.shape[1], state.shape[2]
    eyes_matrix = np.zeros((row_num, col_num))

    player_pieces = state[player]  # player的棋子分布矩阵
    all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)  # 棋盘所有有棋子的分布矩阵，有棋子则相应位置为1
    empties = 1 - all_pieces  # 棋盘上所有空交叉点的分布矩阵，空交叉点位置为1

    # 对于边角位置
    num_for_side_matrix = ndimage.convolve(player_pieces, eye_struct, mode='constant', cval=1) == 8
    # 对于非边角位置
    num_for_nonside_matrix = ndimage.convolve(player_pieces, surround_struct, mode='constant', cval=1) == 4
    num_for_nonside_matrix *= ndimage.convolve(player_pieces, corner_struct, mode='constant', cval=1) > 2

    for i in range(row_num):  # 每一行
        for j in range(col_num):  # 每一列
            if i in [0, row_num] or j in [0, col_num]:  # 在边角
                if num_for_side_matrix[i][j] == 1 and empties[i][j] == 1:
                    eyes_matrix[i][j] = 1
            else:  # 不在边角
                if num_for_nonside_matrix[i][j] == 1 and empties[i][j] == 1:
                    eyes_matrix[i][j] = 1
    return eyes_matrix


def adj_data(state, action2d, player):
    neighbors = neighbor_deltas + action2d  # 计算邻居位置
    valid = (neighbors >= 0) & (neighbors < state.shape[1])  # 计算邻居位置是否在棋盘范围内
    valid = np.prod(valid, axis=1)  # 对每一行元素连乘，得到相应邻居是否有效
    neighbors = neighbors[np.nonzero(valid)]  # 得到有效的邻居位置，np.nonezero()获取所有非零元素的索引

    # 2021年3月4日，BUG修改：计算surrounded时，应该计算对手的位置
    # all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)  # 获得一个矩阵，棋盘矩阵位置有棋子（包括黑白）则为1，无棋子则为0
    opp_pieces = state[1-player]  # 获得对手的棋子分布矩阵(修改后的结果)
    # surrounded = (all_pieces[neighbors[:, 0], neighbors[:, 1]] > 0).all()  # 判断所有邻居位置是否均有棋子
    surrounded = (opp_pieces[neighbors[:, 0], neighbors[:, 1]] > 0).all()  # 判断所有邻居位置是否均有对手棋子(修改后的结果)
    # neighbors是一个二维数组，neighbors[:,0]指二维数组第0列，neighbors[:,1]指二维数组第1列
    # all_pieces[neighbors[:, 0], neighbors[:, 1]]指all_pieces矩阵中的所有邻居位置
    # all_pieces[neighbors[:, 0], neighbors[:, 1]] > 0得到一个值为True/False的一维矩阵，表示对应位置是否有棋子
    # .all()函数在【值为True/False的一维矩阵】值全为True时返回True，只要有一个不为True，则返回False
    # 经过上述处理，neighbors为指定action2d的邻居坐标，surrounded表明action2d周围邻居位置是否均有棋子
    return neighbors, surrounded


def batch_adj_data(batch_state, batch_action2d, batch_player):
    batch_neighbors, batch_surrounded = [], []
    for state, action2d, player in zip(batch_state, batch_action2d, batch_player):
        neighbors, surrounded = adj_data(state, action2d, player)
        batch_neighbors.append(neighbors)
        batch_surrounded.append(surrounded)
    return batch_neighbors, batch_surrounded


def set_turn(state):
    """
    Swaps turn
    :param state:
    :return:
    """
    state[govars.TURN_CHNL] = 1 - state[govars.TURN_CHNL]


def batch_set_turn(batch_state):
    """
    Swaps turn
    :param batch_state:
    :return:
    """
    batch_state[:, govars.TURN_CHNL] = 1 - batch_state[:, govars.TURN_CHNL]

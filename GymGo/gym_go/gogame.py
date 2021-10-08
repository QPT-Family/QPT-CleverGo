import numpy as np
from scipy import ndimage
from sklearn import preprocessing

from GymGo.gym_go import state_utils, govars

"""
The state of the game is a numpy array
* Are values are either 0 or 1

* Shape [NUM_CHNLS, SIZE, SIZE]

0 - Black pieces
CHANNEL[0]: 黑棋棋子分布。有黑棋棋子位置为1，否则为0；
1 - White pieces
CHANNEL[1]: 白棋棋子分布。有白棋棋子位置为1，否则为0；
2 - Turn (0 - black, 1 - white)
CHANNEL[2]: 下一步落子方，一个全0或全1的矩阵。0：黑方，1：白方；
3 - Invalid moves (including ko-protection)
CHANNEL[3]: 下一步的落子无效位置。无效位置为1，其余为0；
4 - Previous move was a pass
CHANNEL[4]: 上一步是否为PASS，一个全0或全1的矩阵。0：不是PASS，1：是PASS；
5 - Game over
CHANNEL[5]: 上一步落子后，游戏是否结束，一个全0或全1的矩阵。0：未结束，1：已结束。
"""


def init_state(size):
    # return initial board (numpy board)
    state = np.zeros((govars.NUM_CHNLS, size, size))
    return state


def batch_init_state(batch_size, board_size):
    # return initial board (numpy board)
    batch_state = np.zeros((batch_size, govars.NUM_CHNLS, board_size, board_size))
    return batch_state


def next_state(state, action1d, canonical=False):
    # Deep copy the state to modify
    state = np.copy(state)

    # Initialize basic variables
    board_shape = state.shape[1:]  # state.shape为(通道数, 棋盘高度, 棋盘宽度)
    pass_idx = np.prod(board_shape)  # np.prod()将参数内所有元素连乘，pass_idx："pass"对应的id
    passed = action1d == pass_idx  # 如果action id等于pass_idx，则passed为True
    action2d = action1d // board_shape[0], action1d % board_shape[1]  # 将action1d转换成action2d

    player = turn(state)  # 获取下一步落子方
    previously_passed = prev_player_passed(state)  # 获取上一步是否为pass
    ko_protect = None

    if passed:
        # We passed
        # 如果下一步为pass，则将next_state中PASS_CHNL矩阵置为全1矩阵
        state[govars.PASS_CHNL] = 1
        if previously_passed:
            # Game ended
            # 如果上一步也为pass，则游戏结束【双方连续各pass，则游戏结束】
            # 将next_state中DONE_CHNL矩阵置为全1矩阵
            state[govars.DONE_CHNL] = 1
    else:
        # Move was not pass
        state[govars.PASS_CHNL] = 0

        # Assert move is valid    检查落子是否有效【state中INVD_CHNL对应位置为0】
        assert state[govars.INVD_CHNL, action2d[0], action2d[1]] == 0, ("Invalid move", action2d)

        # Add piece
        state[player, action2d[0], action2d[1]] = 1

        # Get adjacent location and check whether the piece will be surrounded by opponent's piece
        # 获取下一步落子位置的相邻位置（仅在棋盘内）、下一步落子位置是否被下一步落子方对手的棋子包围
        adj_locs, surrounded = state_utils.adj_data(state, action2d, player)

        # Update pieces
        # 更新棋盘黑白棋子分布矩阵，并返回各组被杀死的棋子列表
        killed_groups = state_utils.update_pieces(state, adj_locs, player)

        # If only killed one group, and that one group was one piece, and piece set is surrounded,
        # activate ko protection
        if len(killed_groups) == 1 and surrounded:
            killed_group = killed_groups[0]
            if len(killed_group) == 1:
                ko_protect = killed_group[0]

    # Update invalid moves
    state[govars.INVD_CHNL] = state_utils.compute_invalid_moves(state, player, ko_protect)

    # Switch turn
    # 设置下一步落子方
    state_utils.set_turn(state)

    # 该标记是选择是否始终以黑棋视角看待当前游戏局面
    if canonical:
        # Set canonical form
        # 该函数将黑白棋子分布对换，并更改下一手落子方为黑棋
        state = canonical_form(state)

    return state


def batch_next_states(batch_states, batch_action1d, canonical=False):
    # Deep copy the state to modify
    batch_states = np.copy(batch_states)

    # Initialize basic variables
    board_shape = batch_states.shape[2:]
    pass_idx = np.prod(board_shape)
    batch_pass = np.nonzero(batch_action1d == pass_idx)
    batch_non_pass = np.nonzero(batch_action1d != pass_idx)[0]
    batch_prev_passed = batch_prev_player_passed(batch_states)
    batch_game_ended = np.nonzero(batch_prev_passed & (batch_action1d == pass_idx))
    batch_action2d = np.array([batch_action1d[batch_non_pass] // board_shape[0],
                               batch_action1d[batch_non_pass] % board_shape[1]]).T
    # batch_action2d在.T之前是一个shape为(2, batch_size)的二维数组，第一行代表所有非pass动作的坐标行号，
    # 第二行代表所有非pass动作列号。因此需要.T进行转置

    batch_players = batch_turn(batch_states)
    batch_non_pass_players = batch_players[batch_non_pass]
    batch_ko_protect = np.empty(len(batch_states), dtype=object)

    # Pass moves
    batch_states[batch_pass, govars.PASS_CHNL] = 1
    # Game ended
    batch_states[batch_game_ended, govars.DONE_CHNL] = 1

    # Non-pass moves
    batch_states[batch_non_pass, govars.PASS_CHNL] = 0

    # Assert all non-pass moves are valid
    assert (batch_states[batch_non_pass, govars.INVD_CHNL, batch_action2d[:, 0], batch_action2d[:, 1]] == 0).all()

    # Add piece
    batch_states[batch_non_pass, batch_non_pass_players, batch_action2d[:, 0], batch_action2d[:, 1]] = 1

    # Get adjacent location and check whether the piece will be surrounded by opponent's piece
    batch_adj_locs, batch_surrounded = state_utils.batch_adj_data(batch_states[batch_non_pass], batch_action2d,
                                                                  batch_non_pass_players)

    # Update pieces
    batch_killed_groups = state_utils.batch_update_pieces(batch_non_pass, batch_states, batch_adj_locs,
                                                          batch_non_pass_players)

    # Ko-protection
    for i, (killed_groups, surrounded) in enumerate(zip(batch_killed_groups, batch_surrounded)):
        # If only killed one group, and that one group was one piece, and piece set is surrounded,
        # activate ko protection
        if len(killed_groups) == 1 and surrounded:
            killed_group = killed_groups[0]
            if len(killed_group) == 1:
                batch_ko_protect[batch_non_pass[i]] = killed_group[0]

    # Update invalid moves
    batch_states[:, govars.INVD_CHNL] = state_utils.batch_compute_invalid_moves(batch_states, batch_players,
                                                                                batch_ko_protect)

    # Switch turn
    state_utils.batch_set_turn(batch_states)

    if canonical:
        # Set canonical form
        batch_states = batch_canonical_form(batch_states)

    return batch_states


def invalid_moves(state):
    # return a fixed size binary vector
    if game_ended(state):
        return np.zeros(action_size(state))
    return np.append(state[govars.INVD_CHNL].flatten(), 0)


def valid_moves(state):
    return 1 - invalid_moves(state)


def batch_invalid_moves(batch_state):
    n = len(batch_state)
    batch_invalid_moves_bool = batch_state[:, govars.INVD_CHNL].reshape(n, -1)
    batch_invalid_moves_bool = np.append(batch_invalid_moves_bool, np.zeros((n, 1)), axis=1)
    return batch_invalid_moves_bool


def batch_valid_moves(batch_state):
    return 1 - batch_invalid_moves(batch_state)


def children(state, canonical=False, padded=True):
    valid_moves_bool = valid_moves(state)
    n = len(valid_moves_bool)
    valid_move_idcs = np.argwhere(valid_moves_bool).flatten()
    batch_states = np.tile(state[np.newaxis], (len(valid_move_idcs), 1, 1, 1))
    children = batch_next_states(batch_states, valid_move_idcs, canonical)

    if padded:
        padded_children = np.zeros((n, *state.shape))
        padded_children[valid_move_idcs] = children
        children = padded_children
    return children


def action_size(state=None, board_size: int = None):
    # return number of actions
    if state is not None:
        m, n = state.shape[1:]
    elif board_size is not None:
        m, n = board_size, board_size
    else:
        raise RuntimeError('No argument passed')
    return m * n + 1


def prev_player_passed(state):
    return np.max(state[govars.PASS_CHNL] == 1) == 1


def batch_prev_player_passed(batch_state):
    return np.max(batch_state[:, govars.PASS_CHNL], axis=(1, 2)) == 1


def game_ended(state):
    """
    :param state:
    :return: 0/1 = game not ended / game ended respectively
    """
    m, n = state.shape[1:]
    return int(np.count_nonzero(state[govars.DONE_CHNL] == 1) == m * n)


def batch_game_ended(batch_state):
    """
    :param batch_state:
    :return: 0/1 = game not ended / game ended respectively
    """
    return np.max(batch_state[:, govars.DONE_CHNL], axis=(1, 2))


def winning(state, komi=0):
    black_area, white_area = areas(state)
    area_difference = black_area - white_area
    komi_correction = area_difference - komi

    return np.sign(komi_correction)


def batch_winning(state, komi=0):
    batch_black_area, batch_white_area = batch_areas(state)
    batch_area_difference = batch_black_area - batch_white_area
    batch_komi_correction = batch_area_difference - komi

    return np.sign(batch_komi_correction)


def turn(state):
    """
    :param state:
    :return: Who's turn it is (govars.BLACK/govars.WHITE)
    """
    return int(np.max(state[govars.TURN_CHNL]))


def batch_turn(batch_state):
    return np.max(batch_state[:, govars.TURN_CHNL], axis=(1, 2)).astype(np.int)


def liberties(state: np.ndarray):
    blacks = state[govars.BLACK]
    whites = state[govars.WHITE]
    all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)

    liberty_list = []
    for player_pieces in [blacks, whites]:
        liberties = ndimage.binary_dilation(player_pieces, state_utils.surround_struct)
        liberties *= (1 - all_pieces).astype(np.bool)
        liberty_list.append(liberties)

    return liberty_list[0], liberty_list[1]


def num_liberties(state: np.ndarray):
    black_liberties, white_liberties = liberties(state)
    black_liberties = np.count_nonzero(black_liberties)
    white_liberties = np.count_nonzero(white_liberties)

    return black_liberties, white_liberties


def areas(state):
    '''
    Return black area, white area
    '''

    all_pieces = np.sum(state[[govars.BLACK, govars.WHITE]], axis=0)
    empties = 1 - all_pieces

    empty_labels, num_empty_areas = ndimage.measurements.label(empties)

    black_area, white_area = np.sum(state[govars.BLACK]), np.sum(state[govars.WHITE])
    for label in range(1, num_empty_areas + 1):
        empty_area = empty_labels == label
        neighbors = ndimage.binary_dilation(empty_area)
        black_claim = False
        white_claim = False
        if (state[govars.BLACK] * neighbors > 0).any():
            black_claim = True
        if (state[govars.WHITE] * neighbors > 0).any():
            white_claim = True
        if black_claim and not white_claim:
            black_area += np.sum(empty_area)
        elif white_claim and not black_claim:
            white_area += np.sum(empty_area)

    return black_area, white_area


def batch_areas(batch_state):
    black_areas, white_areas = [], []

    for state in batch_state:
        ba, wa = areas(state)
        black_areas.append(ba)
        white_areas.append(wa)
    return np.array(black_areas), np.array(white_areas)


def canonical_form(state):
    state = np.copy(state)
    if turn(state) == govars.WHITE:
        channels = np.arange(govars.NUM_CHNLS)
        channels[govars.BLACK] = govars.WHITE
        channels[govars.WHITE] = govars.BLACK
        state = state[channels]
        state_utils.set_turn(state)
    return state


def batch_canonical_form(batch_state):
    batch_state = np.copy(batch_state)
    batch_player = batch_turn(batch_state)
    white_players_idcs = np.nonzero(batch_player == govars.WHITE)[0]

    channels = np.arange(govars.NUM_CHNLS)
    channels[govars.BLACK] = govars.WHITE
    channels[govars.WHITE] = govars.BLACK

    for i in white_players_idcs:
        batch_state[i] = batch_state[i, channels]
        batch_state[i, govars.TURN_CHNL] = 1 - batch_player[i]

    return batch_state


def random_symmetry(image):
    """
    Returns a random symmetry of the image
    :param image: A (C, BOARD_SIZE, BOARD_SIZE) numpy array, where C is any number
    :return:
    """
    orientation = np.random.randint(0, 8)

    if (orientation >> 0) % 2:
        # Horizontal flip
        image = np.flip(image, 2)
    if (orientation >> 1) % 2:
        # Vertical flip
        image = np.flip(image, 1)
    if (orientation >> 2) % 2:
        # Rotate 90 degrees
        image = np.rot90(image, axes=(1, 2))

    return image


def all_symmetries(image):
    """
    :param image: A (C, BOARD_SIZE, BOARD_SIZE) numpy array, where C is any number
    :return: All 8 orientations that are symmetrical in a Go game over the 2nd and 3rd axes
    (i.e. rotations, flipping and combos of them)
    """
    symmetries = []

    for i in range(8):
        x = image
        if (i >> 0) % 2:
            # Horizontal flip
            x = np.flip(x, 2)
        if (i >> 1) % 2:
            # Vertical flip
            x = np.flip(x, 1)
        if (i >> 2) % 2:
            # Rotation 90 degrees
            x = np.rot90(x, axes=(1, 2))
        symmetries.append(x)

    return symmetries


def random_weighted_action(move_weights):
    """
    Assumes all invalid moves have weight 0
    Action is 1D
    Expected shape is (NUM OF MOVES, )
    """
    move_weights = preprocessing.normalize(move_weights[np.newaxis], norm='l1')
    return np.random.choice(np.arange(len(move_weights[0])), p=move_weights[0])


def random_action(state):
    """
    Assumed to be (NUM_CHNLS, BOARD_SIZE, BOARD_SIZE)
    Action is 1D
    """
    invalid_moves = state[govars.INVD_CHNL].flatten()
    invalid_moves = np.append(invalid_moves, 0)
    move_weights = 1 - invalid_moves

    return random_weighted_action(move_weights)


def str(state):
    board_str = ' '

    size = state.shape[1]
    for i in range(size):
        board_str += '   {}'.format(i)
    board_str += '\n  '
    board_str += '----' * size + '-'
    board_str += '\n'
    for i in range(size):
        board_str += '{} |'.format(i)
        for j in range(size):
            if state[0, i, j] == 1:
                board_str += ' B'
            elif state[1, i, j] == 1:
                board_str += ' W'
            elif state[2, i, j] == 1:
                board_str += ' .'
            else:
                board_str += '  '

            board_str += ' |'

        board_str += '\n  '
        board_str += '----' * size + '-'
        board_str += '\n'

    black_area, white_area = areas(state)
    done = game_ended(state)
    ppp = prev_player_passed(state)
    t = turn(state)
    board_str += '\tTurn: {}, Last Turn Passed: {}, Game Over: {}\n'.format('B' if t == 0 else 'W', ppp, done)
    board_str += '\tBlack Area: {}, White Area: {}\n'.format(black_area, white_area)
    return board_str

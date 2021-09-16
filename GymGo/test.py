import numpy as np
from scipy import ndimage
from scipy.ndimage import measurements

# matrix = np.zeros((3, 3, 3))
# matrix[0][0][0] = 1
# matrix[0][1][0] = 1.1
# matrix[0][2][0] = 1.11
# matrix[1][0][0] = 2
# matrix[1][1][0] = 2.2
# matrix[1][2][0] = 2.22
# matrix[2][0][0] = 3
# matrix[2][1][0] = 3.3
# matrix[2][2][0] = 3.33
#
# print(matrix)
# print('==================================================')
# new_matrix = matrix[[0, 1]]
# print(new_matrix)
# print('==================================================')
# new_matrix = np.sum(new_matrix, axis=0)
# print(new_matrix)
#
# print('------------------------------------------------------')
# action2d = [2, 2]
# neighbor_deltas = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])
# neighbors = neighbor_deltas + action2d
# print(neighbors)
# valid = (neighbors >= 0) & (neighbors < 3)
# print(valid)
# valid = np.prod(valid, axis=1)
# print(valid)
# neighbors = neighbors[np.nonzero(valid)]
# print(neighbors)
#
# print('------------------------------------------------------')
# # neighbors[1, 0] = 3
# # neighbors[1, 1] = 4
# print(neighbors)
# print(neighbors[:, 0])
# print((new_matrix[neighbors[:, 0], neighbors[:, 1]]) > 0)
# print((new_matrix[neighbors[:, 0], neighbors[:, 1]] > 0).all())


# print('a')
# a = np.array([[1,2,3],
#              [3,4,6],
#              [7,8,9]])
# print(a)
#
# print(a[[0,2], [1,2]])

# test_matrix = np.array([[0, 0, 1, 0],
#                         [1, 0, 1, 1],
#                         [0, 1, 0, 0],
#                         [0, 1, 0, 1]])
# labeled_array, num_features = ndimage.measurements.label(test_matrix)
# print(labeled_array)
# print(num_features)

# test_matrix = np.array([2,2,6,2,6,6,7,3])
# test_matrix = np.unique(test_matrix)
# print(test_matrix)

# test_matrix = np.array([0, 1, 2, 3, 0, 1])
# index = np.nonzero(test_matrix)
# print(index)
# print(test_matrix[index])

# test_matrix = np.array([[0, 1, 1, 0],
#                         [2, 0, 1, 1],
#                         [2, 0, 0, 0],
#                         [2, 0, 0, 3]])
# a = test_matrix == 2
# print(a)
# a = ndimage.binary_dilation(a)
# print(a)
#
# empities = np.array([[1, 0, 0, 0],
#                      [0, 0, 0, 0],
#                      [0, 0, 0, 0],
#                      [0, 1, 1, 0]])
# a = empities * a
# print(a)

# x = np.array([[True, False],
#               [False, True]])
# x = np.argwhere(x)
# print(x)

# x = [2, *[2, 3]]
# x = np.zeros(x)
# print(x)

x = np.array([[[[0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]],
               [[1, 1, 1],
                [1, 1, 1],
                [1, 1, 1]],
               [[2, 2, 2],
                [2, 2, 2],
                [2, 2, 2]],
               [[3, 3, 3],
                [3, 3, 3],
                [3, 3, 3]],
               [[4, 4, 4],
                [4, 4, 4],
                [4, 4, 4]],
               [[5, 5, 5],
                [5, 5, 5],
                [5, 5, 5]]]])
y = x[np.newaxis]
print(x.shape)
print(y.shape)
print(x[:, 1])
print(np.max(x[:, 3], axis=(1, 2)))

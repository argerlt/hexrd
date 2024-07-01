import numpy as np

from hexrd import matrixutil as mutil


def test_vec_mv_cob_matrix():
    np.random.seed(0)
    # Generate some random matrices
    R = np.random.rand(20, 3, 3) * 2 - 1

    T = np.zeros((len(R), 6, 6), dtype='float64')
    sqr2 = np.sqrt(2)
    # Hardcoded implementation
    T[:, 0, 0] = R[:, 0, 0]**2
    T[:, 0, 1] = R[:, 0, 1]**2
    T[:, 0, 2] = R[:, 0, 2]**2
    T[:, 0, 3] = sqr2 * R[:, 0, 1] * R[:, 0, 2]
    T[:, 0, 4] = sqr2 * R[:, 0, 0] * R[:, 0, 2]
    T[:, 0, 5] = sqr2 * R[:, 0, 0] * R[:, 0, 1]
    T[:, 1, 0] = R[:, 1, 0]**2
    T[:, 1, 1] = R[:, 1, 1]**2
    T[:, 1, 2] = R[:, 1, 2]**2
    T[:, 1, 3] = sqr2 * R[:, 1, 1] * R[:, 1, 2]
    T[:, 1, 4] = sqr2 * R[:, 1, 0] * R[:, 1, 2]
    T[:, 1, 5] = sqr2 * R[:, 1, 0] * R[:, 1, 1]
    T[:, 2, 0] = R[:, 2, 0]**2
    T[:, 2, 1] = R[:, 2, 1]**2
    T[:, 2, 2] = R[:, 2, 2]**2
    T[:, 2, 3] = sqr2 * R[:, 2, 1] * R[:, 2, 2]
    T[:, 2, 4] = sqr2 * R[:, 2, 0] * R[:, 2, 2]
    T[:, 2, 5] = sqr2 * R[:, 2, 0] * R[:, 2, 1]
    T[:, 3, 0] = sqr2 * R[:, 1, 0] * R[:, 2, 0]
    T[:, 3, 1] = sqr2 * R[:, 1, 1] * R[:, 2, 1]
    T[:, 3, 2] = sqr2 * R[:, 1, 2] * R[:, 2, 2]
    T[:, 3, 3] = R[:, 1, 2] * R[:, 2, 1] + R[:, 1, 1] * R[:, 2, 2]
    T[:, 3, 4] = R[:, 1, 2] * R[:, 2, 0] + R[:, 1, 0] * R[:, 2, 2]
    T[:, 3, 5] = R[:, 1, 1] * R[:, 2, 0] + R[:, 1, 0] * R[:, 2, 1]
    T[:, 4, 0] = sqr2 * R[:, 0, 0] * R[:, 2, 0]
    T[:, 4, 1] = sqr2 * R[:, 0, 1] * R[:, 2, 1]
    T[:, 4, 2] = sqr2 * R[:, 0, 2] * R[:, 2, 2]
    T[:, 4, 3] = R[:, 0, 2] * R[:, 2, 1] + R[:, 0, 1] * R[:, 2, 2]
    T[:, 4, 4] = R[:, 0, 2] * R[:, 2, 0] + R[:, 0, 0] * R[:, 2, 2]
    T[:, 4, 5] = R[:, 0, 1] * R[:, 2, 0] + R[:, 0, 0] * R[:, 2, 1]
    T[:, 5, 0] = sqr2 * R[:, 0, 0] * R[:, 1, 0]
    T[:, 5, 1] = sqr2 * R[:, 0, 1] * R[:, 1, 1]
    T[:, 5, 2] = sqr2 * R[:, 0, 2] * R[:, 1, 2]
    T[:, 5, 3] = R[:, 0, 2] * R[:, 1, 1] + R[:, 0, 1] * R[:, 1, 2]
    T[:, 5, 4] = R[:, 0, 0] * R[:, 1, 2] + R[:, 0, 2] * R[:, 1, 0]
    T[:, 5, 5] = R[:, 0, 1] * R[:, 1, 0] + R[:, 0, 0] * R[:, 1, 1]

    T2 = mutil.vecMVCOBMatrix(R)

    assert np.allclose(T, T2)

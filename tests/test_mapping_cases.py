import numpy as np


def case_1_1_symmetric_sum():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 2], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "sum"
    weight = None

    expected_mask = np.array([0, 0, 0], dtype=int)
    expected_map_dense = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_1_1_symmetric_avg():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 2], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "avg"
    weight = None

    expected_mask = np.array([0, 0, 0], dtype=int)
    expected_map_dense = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_1_1_symmetric_weight():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 2], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "weight"
    weight = np.array([0.5, 0.3, 0.1])

    expected_mask = np.array([0, 0, 0], dtype=int)

    expected_map_dense = np.array(
        [
            [0.5, 0.0, 0.0],
            [0.0, 0.3, 0.0],
            [0.0, 0.0, 0.1],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_1_1_asymmetric_sum():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 3, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "sum"
    weight = None

    expected_mask = np.array([1, 1, 0, 0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_1_1_asymmetric_avg():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 3, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "avg"
    weight = None

    expected_mask = np.array([1, 1, 0, 0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_1_1_asymmetric_weight():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 3, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "weight"
    weight = np.array([0.5, 0.3, 0.1])

    expected_mask = np.array([1, 1, 0, 0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.3, 0.0],
            [0.0, 0.0, 0.1],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_symmetric_sum():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 1], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "sum"
    weight = None

    expected_mask = np.array([0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_symmetric_avg():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 1], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "avg"
    weight = None

    expected_mask = np.array([0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.5, 0.5],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_symmetric_weight():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([0, 1, 1], dtype=int)

    nsrc = 3
    ntgt = 3
    operator = "weight"
    weight = np.array([0.5, 0.3, 0.1])

    expected_mask = np.array([0, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.5, 0.0, 0.0],
            [0.0, 0.3, 0.1],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_asymmetric_sum():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 2, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "sum"
    weight = None

    expected_mask = np.array([1, 1, 0, 1, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_asymmetric_avg():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 2, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "avg"
    weight = None

    expected_mask = np.array([1, 1, 0, 1, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )


def case_n_1_asymmetric_weight():
    src_idx = np.array([0, 1, 2], dtype=int)
    tgt_idx = np.array([2, 2, 4], dtype=int)

    nsrc = 3
    ntgt = 6
    operator = "weight"
    weight = np.array([0.5, 0.3, 0.1])

    expected_mask = np.array([1, 1, 0, 1, 0, 1], dtype=int)
    expected_map_dense = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.5, 0.3, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.1],
            [0.0, 0.0, 0.0],
        ]
    )
    return (
        src_idx,
        tgt_idx,
        nsrc,
        ntgt,
        operator,
        weight,
        expected_map_dense,
        expected_mask,
    )

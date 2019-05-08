from mosaicu import generate_radius_indices


def test_generate_generate_radius_indices():
    actual_radius1 = generate_radius_indices(0, 0, 1)
    expected = [(0, 0), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
    assert expected == actual_radius1

    actual_radius2 = generate_radius_indices(0, 0, 2)
    expected = [(0, 0), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1),
                (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
                (-1, 2), (0, 2), (1, 2), (2, 2),
                (2, 1), (2, 0), (2, -1), (2, -2),
                (1, -2), (0, -2), (-1, -2)]
    print(actual_radius2)
    assert expected == actual_radius2

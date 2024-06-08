def make_fake():
    result = []
    for i in range(1, 6):
        row = []
        result.append(row)
        for z in range(1, 6):
            row.append(f"fake {i} {z}")
    return result
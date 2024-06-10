def make_fake():
    result = []
    for i in range(1, 6):
        row = []
        result.append(row)
        for z in range(1, 6):
            row.append({"cost": f"fake {i} {z}",
                        "id": int(str(i) + str(z))})
    return result

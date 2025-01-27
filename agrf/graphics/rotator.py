import math


def natural_dimens(angle, bbox, scale):
    radian = math.radians(angle)
    cos, sin = math.cos(radian), math.sin(radian)

    x, y, z = bbox["x"], bbox["y"], bbox["z"]

    xcom, ycom = abs(x * cos), abs(y * sin)
    pxcom, pycom = abs(x * sin), abs(y * cos)

    width = pxcom + pycom
    horizontal_height = (xcom + ycom) * 0.5
    height = horizontal_height + z

    return (width * scale, height * scale)


def unnatural_dimens(angle, bbox, scale, *, unnaturalness=1):
    radian = math.radians(abs(angle % 90 - 45))
    new_x = bbox["x"] / math.cos(radian * unnaturalness)

    return natural_dimens(angle, {**bbox, "x": new_x}, scale)


if __name__ == "__main__":
    DEFAULT_SCALE = 2**0.5 / 13

    for angle in range(0, 91, 15):
        print(angle, natural_dimens(angle, {"x": 252, "y": 80, "z": 96}, DEFAULT_SCALE))
    print()

    for angle in range(0, 91, 15):
        print(angle, unnatural_dimens(angle, {"x": 252, "y": 80, "z": 96}, DEFAULT_SCALE))
    print()

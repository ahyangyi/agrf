import grf


class Registers:
    ZERO = grf.Temp(0)
    CLIMATE_RAIL_OFFSET = grf.Temp(1)
    CLIMATE_OFFSET = grf.Temp(2)
    SNOW = grf.Temp(3)
    NOSNOW = grf.Temp(4)
    RECOLOUR_OFFSET = grf.Temp(5)


code = """
TEMP[0x00] = 0
TEMP[0x01] = (26 * ((terrain_type & 0x5) > 0) + 82 * (max(track_type, 1) - 1)) * (track_type <= 3)
TEMP[0x02] = 569 * ((terrain_type & 0x5) > 0)
TEMP[0x03] = (terrain_type & 0x4) == 0x4
TEMP[0x04] = (terrain_type & 0x4) != 0x4
"""

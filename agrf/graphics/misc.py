import grf

SCALE_TO_ZOOM = {4: grf.ZOOM_4X, 2: grf.ZOOM_2X, 1: grf.ZOOM_NORMAL}
ZOOM_TO_SCALE = {v: k for k, v in SCALE_TO_ZOOM.items()}

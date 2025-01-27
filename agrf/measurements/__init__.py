from .length import Length


class RealMeasurementMixin:
    def __init__(self):
        pass

    @staticmethod
    def measurement_names():
        return {"length": Length, "width": Length, "height": Length}

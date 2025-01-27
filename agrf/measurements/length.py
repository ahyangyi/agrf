from dataclasses import dataclass


class Length:
    def __init__(self, meters):
        self.meters = meters

    @staticmethod
    def from_meters(self, meters):
        return Length(meters)

    @staticmethod
    def from_inches(self, inches):
        return Length.from_meters(inches * 0.0254)

    @staticmethod
    def from_feet(self, feet):
        return Length.from_inches(feet * 12)

    @staticmethod
    def from_feet_inches(self, feet, inches):
        return Length.from_inches(feet * 12 + inches)

    def __str__(self):
        return f"{self.meters}m"

    def str_milimeters(self):
        return f"{self.meters*1000}mm"


@dataclass
class Size3D:
    length: Length
    width: Length
    height: Length

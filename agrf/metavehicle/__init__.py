from agrf.variant import AVariant
from agrf.strings import get_translation


def dimens_repr(dimensions):
    if dimensions is None:
        return ""
    return " × ".join(map(str, dimensions))


class AMetaVehicle(AVariant):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def name(self, string_manager, lang_id=0x7F):
        return get_translation(string_manager[f"STR_VEHICLE_NAME_{self.translation_name}"], lang_id)

    @property
    def real_dimensions_repr(self):
        return dimens_repr(self.get("real_dimensions", None))

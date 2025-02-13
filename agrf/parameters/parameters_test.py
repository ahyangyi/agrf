import grf
from .parameters import Parameter, ParameterList


def test_int_params():
    p1 = Parameter("FOO", 0, limits=(0, 20))
    p2 = Parameter("BAR", 15, limits=(10, 20))
    pl = ParameterList([p1, p2])

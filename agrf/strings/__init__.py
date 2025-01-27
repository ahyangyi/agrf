import grf
from nml import grfstrings


class String:
    def __init__(self, s, *args):
        self.s = s
        self.args = args

    def __call__(self, *args):
        if len(args) == 0:
            return self
        if isinstance(args[-1], grf.StringManager):
            s = args[-1]
            params = []
            for x in self.args + args[:-1]:
                if isinstance(x, str):
                    params.append(s[x])
                else:
                    params.append(x(s))
            return args[-1][self.s].eval(*params)
        return String(self.s, *(self.args + args))


def get_translation(stringref, lang_id=0x7F):
    stringref.manager.set_nml_globals()
    ns = stringref.string_nmlexpr
    if lang_id in grfstrings.get_translations(ns):
        return grfstrings.get_translation(ns, lang_id)
    return grfstrings.get_translation(ns)


def remove_control_letters(s):
    ret = []
    i = 0
    while i < len(s):
        if s[i] == "\\":
            if s[i + 1] == "U":
                i += 6
            else:
                i += 3
        else:
            ret.append(s[i])
            i += 1
    return "".join(ret)

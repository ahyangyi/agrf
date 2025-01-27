class BuildingSymmetryMixin:
    @classmethod
    def create_variants(classobj, variants):
        assert len(variants) == len(classobj.render_indices())
        for i, v in enumerate(variants):
            cls = v.__class__
            v.__class__ = type(f"{cls.__name__}+{classobj.__name__}", (classobj, cls), {})

            idx = classobj.render_indices()[i]
            v._M = variants[classobj._symmetry_descriptor[idx ^ 1]]
            if idx % 2 == 0:
                v._R = variants[classobj._symmetry_descriptor[idx ^ 2]]
                v._T = variants[classobj._symmetry_descriptor[idx ^ 4]]
            else:
                v._R = variants[classobj._symmetry_descriptor[idx ^ 4]]
                v._T = variants[classobj._symmetry_descriptor[idx ^ 2]]
            v.symmetry = classobj
        return variants[0]

    @property
    def M(self):
        return self._M

    @property
    def R(self):
        return self._R

    @property
    def T(self):
        return self._T

    @classmethod
    def get_all_variants(cls, thing):
        return [cls.symmetry_index(thing, i) for i in cls.render_indices()]

    @classmethod
    def get_all_entries(cls, thing):
        ret = [thing]

        if cls._symmetry_descriptor[2] != cls._symmetry_descriptor[0]:
            ret = ret + [x.R for x in ret]
        if set(cls._symmetry_descriptor[i] for i in [4, 6]) != set(cls._symmetry_descriptor[i] for i in [0, 2]):
            ret = ret + [x.T for x in ret]
        return ret

    @property
    def all_variants(self):
        return self.get_all_variants(self)

    @classmethod
    def is_symmetrical_y(classobj):
        return classobj._symmetry_descriptor[:4] == classobj._symmetry_descriptor[4:]

    @staticmethod
    def __canonicalize_descriptor(descriptor):
        ret = []
        assignment = {}
        for x in descriptor:
            if x not in assignment:
                assignment[x] = len(assignment)
            ret.append(assignment[x])
        return tuple(ret)

    @staticmethod
    def __merge_descriptor(descriptor, merge_operations):
        assignment = {}
        for a, b in merge_operations:
            while a in assignment:
                a = assignment[a]
            while b in assignment:
                b = assignment[b]
            if a == b:
                continue
            if a < b:
                assignment[b] = a
            else:
                assignment[a] = b

        ret = []
        for x in descriptor:
            while x in assignment:
                x = assignment[x]
            ret.append(x)
        return tuple(ret)

    @classmethod
    def render_indices(classobj):
        ret = []
        seen = set()
        for i in range(8):
            if classobj._symmetry_descriptor[i] not in seen:
                seen.add(classobj._symmetry_descriptor[i])
                ret.append(i)

        return ret

    @classmethod
    def join(classobj1, classobj2):
        new_descriptor = tuple((classobj1._symmetry_descriptor[i], classobj2._symmetry_descriptor[i]) for i in range(8))
        new_descriptor = BuildingSymmetryMixin.__canonicalize_descriptor(new_descriptor)
        return BuildingSymmetryMixin._type_pool[new_descriptor]

    @classmethod
    def meet(classobj1, classobj2):
        ret = []
        prev1 = {}
        prev2 = {}
        for i in range(8):
            cur = i
            a, b = classobj1._symmetry_descriptor[i], classobj2._symmetry_descriptor[i]
            if a in prev1:
                ai = prev1[a]
                cur = ret[ai]
            prev1[a] = i
            if b in prev2:
                bi = prev2[b]
                if cur != i:
                    for j in range(i):
                        if ret[j] == cur:
                            ret[j] = ret[bi]
                cur = ret[bi]
            prev2[b] = i
            ret.append(cur)
        new_descriptor = BuildingSymmetryMixin.__canonicalize_descriptor(ret)
        return BuildingSymmetryMixin._type_pool[new_descriptor]

    @classmethod
    def break_x_symmetry(classobj):
        return classobj.join(BuildingSymmetricalY)

    @classmethod
    def break_y_symmetry(classobj):
        return classobj.join(BuildingSymmetricalX)

    @classmethod
    def add_x_symmetry(classobj):
        return classobj.meet(BuildingSymmetricalX)

    @classmethod
    def add_y_symmetry(classobj):
        return classobj.meet(BuildingSymmetricalY)

    @classmethod
    def chirality_indices(classobj):
        if set(classobj._symmetry_descriptor[i] for i in [0, 3, 5, 6]) == set(
            classobj._symmetry_descriptor[i] for i in [1, 2, 4, 7]
        ):
            return [0]
        else:
            return [0, 2]

    @classmethod
    def rotational_view_indices(classobj):
        if classobj._symmetry_descriptor[0] != classobj._symmetry_descriptor[3]:
            if len(set(classobj._symmetry_descriptor[i] for i in [0, 3, 5, 6])) == 4:
                return [0, 3, 6, 5]
            else:
                return [0, 3]
        else:
            return [0]

    @classmethod
    def rotational_views(classobj, cur):
        return [classobj.symmetry_index(cur, i) for i in classobj.rotational_view_indices()]

    @classmethod
    def chiralities(classobj, cur):
        return [classobj.symmetry_index(cur, i) for i in classobj.chirality_indices()]

    def symmetry_index(self, i):
        if i == 0:
            return self
        if i == 1:
            return self.M
        if i == 2:
            return self.R
        if i == 3:
            return self.R.M
        if i == 4:
            return self.T
        if i == 5:
            return self.T.M
        if i == 6:
            return self.T.R
        return self.T.R.M

    @classmethod
    def canonical_index(classobj, i):
        for j in range(8):
            if classobj._symmetry_descriptor[j] == classobj._symmetry_descriptor[i]:
                return j
        # Unreachable
        return i

    @staticmethod
    def compose_symmetry_indices(a, b):
        if a % 2 == 1:
            return a ^ (2 if (b & 4) else 0) ^ (4 if (b & 2) else 0) ^ (b & 1)
        return a ^ b

    _type_pool = {}


class BuildingFull(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 2, 3, 4, 5, 6, 7)


class BuildingSymmetricalX(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 0, 1, 2, 3, 2, 3)


class BuildingSymmetricalY(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 2, 3, 0, 1, 2, 3)


class BuildingSymmetrical(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 0, 1, 0, 1, 0, 1)


class BuildingRotational(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 2, 3, 2, 3, 0, 1)


class BuildingRotational4(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 1, 0, 1, 0, 0, 1)


class BuildingDiagonal(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 0, 1, 2, 2, 1, 3, 3)


class BuildingDiagonalAlt(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 1, 2, 2, 3, 3, 1, 0)


class BuildingDiamond(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 0, 1, 1, 1, 1, 0, 0)


class BuildingCylindrical(BuildingSymmetryMixin):
    _symmetry_descriptor = (0, 0, 0, 0, 0, 0, 0, 0)


BuildingSymmetryMixin._type_pool[(0, 1, 2, 3, 4, 5, 6, 7)] = BuildingFull
BuildingSymmetryMixin._type_pool[(0, 1, 0, 1, 2, 3, 2, 3)] = BuildingSymmetricalX
BuildingSymmetryMixin._type_pool[(0, 1, 2, 3, 0, 1, 2, 3)] = BuildingSymmetricalY
BuildingSymmetryMixin._type_pool[(0, 1, 0, 1, 0, 1, 0, 1)] = BuildingSymmetrical
BuildingSymmetryMixin._type_pool[(0, 0, 1, 2, 2, 1, 3, 3)] = BuildingDiagonal
BuildingSymmetryMixin._type_pool[(0, 1, 2, 3, 2, 3, 0, 1)] = BuildingRotational
BuildingSymmetryMixin._type_pool[(0, 0, 0, 0, 0, 0, 0, 0)] = BuildingCylindrical

import grf
from .split_definition import SplitDefinition


class MetaSpriteMixin:
    def __init__(self, feature, props_hash, parameter_list):
        self.feature = feature
        self.props_hash = props_hash
        self._parameter_list = parameter_list

    @property
    def dynamic_prop_variables(self):
        ret = set()
        for p in self._props.values():
            # FIXME recursive SplitDefinitions?
            if isinstance(p, SplitDefinition):
                p.fixup(self._parameter_list)
                for v in p.variables:
                    ret.add(v)
        return list(sorted(ret))

    def postprocess_props(self, props):
        return props

    def resolve_props(self, parameters):
        if "exists" in self._props:
            v = self._props["exists"]
            while isinstance(v, SplitDefinition):
                v.fixup(self._parameter_list)
                branch_key = tuple(parameters[var] for var in v.variables)
                v = v.branches[branch_key]
            if not v:
                return {"exists": False}

        new_props = {}
        for k, v in self._props.items():
            if k == "exists":
                continue
            while isinstance(v, SplitDefinition):
                v.fixup(self._parameter_list)
                branch_key = tuple(parameters[var] for var in v.variables)
                v = v.branches[branch_key]
            new_props[k] = v
        return new_props

    def dynamic_definitions(self):
        all_choices = self.dynamic_prop_variables

        def dfs(parameters, i=0):
            if i == len(all_choices):
                resolved_props = self.resolve_props(parameters)
                exists = resolved_props.pop("exists", True)
                if exists:
                    return [
                        [grf.Define(feature=self.feature, id=self.id, props=self.postprocess_props(resolved_props))]
                    ], self.props_hash(resolved_props)
                else:
                    return [], 0
            ret = []
            var_id = all_choices[i]
            sublists = []
            hashes = []
            for choice in self._parameter_list.parameter_by_id(var_id).enum.keys():
                parameters[var_id] = choice
                sublist, h = dfs(parameters, i + 1)
                sublists.append(sublist)
                hashes.append(h)
            del parameters[var_id]

            if all(hashes[0] == h for h in hashes):
                return sublists[0], hash(tuple(hashes))

            for choice in range(len(self._parameter_list.parameter_by_id(var_id).enum)):
                sublist = sublists[choice]
                for g in sublist:
                    ret.append(
                        [grf.If(is_static=True, variable=var_id, condition=0x03, value=choice, skip=len(g), varsize=4)]
                        + g
                    )

            compressed_ret = []
            cur_group = []
            for group in ret:
                if len(cur_group) + len(group) + i <= 255:
                    cur_group.extend(group)
                else:
                    compressed_ret.append(cur_group)
                    cur_group = group
            if len(cur_group) > 0:
                compressed_ret.append(cur_group)

            return compressed_ret, hash(tuple(hashes))

        return dfs({}, 0)[0]

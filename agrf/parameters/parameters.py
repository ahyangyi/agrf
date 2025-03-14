import copy
import grf


class ParameterReverseLookup:
    def __init__(self, enum):
        self.enum = enum
        if self.enum is not None:
            self.reverse_lookup = {v: k for k, v in self.enum.items()}

    def enum_index(self, name):
        return self.reverse_lookup[name]


class Parameter(ParameterReverseLookup):
    def __init__(self, name, default, enum=None, limits=None, mapping=None, option_name=None):
        super().__init__(enum)
        self.name = name
        self.default = default
        self._limits = limits
        self.mapping = mapping
        self.option_name = option_name or name

    def add(self, g, s):
        g.add_int_parameter(
            name=s[f"STR_PARAM_{self.name}"],
            description=s[f"STR_PARAM_{self.name}_DESC"],
            default=self.default,
            limits=self.limits,
            enum=self.enum and {k: s[f"STR_PARAM_{self.option_name}_{v}"] for k, v in self.enum.items()},
            mapping=self.mapping,
        )

    @property
    def min_value(self):
        return min(self.enum.keys())

    @property
    def max_value(self):
        return max(self.enum.keys())

    @property
    def limits(self):
        if self.enum is None:
            return self._limits
        return (self.min_value, self.max_value)

    @property
    def range(self):
        return (self.min_value, self.max_value + 1)

    def set_index(self, index):
        self.index = index

    @property
    def code(self):
        if self.mapping is None:
            return f"var(0x7F, param={self.index}, shift=0, and=0xffffffff)"

        m = self.mapping
        return f"var(0x7F, param={m.grf_parameter}, shift={m.first_bit}, and={2 ** m.num_bit - 1})"

    def make_if(self, is_static, skip):
        assert self.min_value == 0 and self.max_value == 1
        if self.mapping is not None:
            assert self.mapping.num_bit == 1
            return grf.If(
                is_static=is_static,
                variable=self.mapping.grf_parameter,
                condition=0x01,
                value=self.mapping.first_bit,
                skip=skip,
                varsize=1,
            )
        return grf.If(is_static=is_static, variable=self.index, condition=0x02, value=0x0, skip=skip, varsize=4)


class ParameterList:
    def __init__(self, parameters):
        self.parameters = parameters
        for i, p in enumerate(parameters):
            p.set_index(i)

    def add(self, g, s):
        for p in self.parameters:
            p.add(g, s)

    def index(self, name):
        return self[name].index

    def preset_index(self, name):
        return self.index(name)

    def __getitem__(self, name):
        return [p for p in self.parameters if p.name == name][0]

    def parameter_by_id(self, i):
        return self.parameters[i]


class ParameterListWithPreset(ParameterList):
    def __init__(self, parameters, presets, start_id=0x40, preset_param_name="PRESET", preset_enum_name="PRESET"):
        super().__init__(parameters)
        self.presets = presets
        self.preset_param_id = self.index(preset_param_name)
        self._parameters_with_preset = {}
        self._preset_parameters = {}
        for p in self.presets.values():
            for k in p.keys():
                if k not in self._parameters_with_preset:
                    self._parameters_with_preset[k] = (start_id, self[k].enum_index(preset_enum_name))
                    self._preset_parameters[start_id] = ParameterReverseLookup(
                        {kk: v for kk, v in self[k].enum.items() if v != preset_enum_name}
                    )
                    start_id += 1

    def preset_index(self, name):
        if name in self._parameters_with_preset:
            return self._parameters_with_preset[name][0]
        return self.index(name)

    def add(self, g, s):
        super().add(g, s)
        for k, (v, preset_enum_id) in sorted(self._parameters_with_preset.items()):
            k_id = self.index(k)
            for preset_name, preset in self.presets.items():
                preset_id = self.parameters[self.preset_param_id].enum_index(preset_name)
                g.add(
                    grf.If(
                        is_static=True,
                        variable=self.preset_param_id,
                        condition=0x03,
                        value=preset_id,
                        skip=2,
                        varsize=4,
                    )
                )
                g.add(grf.If(is_static=True, variable=k_id, condition=0x03, value=preset_enum_id, skip=1, varsize=4))
                g.add(
                    grf.ComputeParameters(
                        target=v,
                        operation=0x00,
                        if_undefined=False,
                        source1=0xFF,
                        source2=0xFF,
                        value=self[k].enum_index(preset[k]),
                    )
                )

    def parameter_by_id(self, i):
        if i in self._preset_parameters:
            return self._preset_parameters[i]
        return super().parameter_by_id(i)


class SearchSpace:
    def __init__(self, choices, parameter_list):
        self.choices = choices
        self.parameter_list = parameter_list

    def _iterate_variations(self, i, params):
        if i == len(self.choices):
            yield params
        else:
            parameter_name, available_choices = self.choices[i]
            for j in available_choices:
                new_params = params.copy()
                new_params[parameter_name] = j
                for variation in self._iterate_variations(i + 1, new_params):
                    yield variation

    def iterate_variations(self):
        for variation in self._iterate_variations(0, {}):
            yield variation

    def desc(self, params):
        return "".join(str(options.index(params[i])) for i, options in self.choices)

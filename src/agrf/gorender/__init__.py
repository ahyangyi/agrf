import os
import subprocess
import json
import tempfile
from copy import deepcopy


class Config:
    def __init__(self, load_from=None, config=None):
        if load_from is None:
            self.config = {}
        else:
            with open(load_from) as f:
                self.config = json.load(f)
        if config is not None:
            self.config.update(config)

        self._final_config = None

    @property
    def final_config(self):
        if self._final_config is not None:
            return self._final_config
        self._final_config = self.subset()
        return self._final_config

    def copy(self):
        return Config(config=deepcopy(self.config))

    def subset(self):
        new_config = deepcopy(self.config)

        if "agrf_subset" in new_config:
            indices = new_config["agrf_subset"]
            for k in ["sprites", "agrf_deltas", "agrf_offsets", "agrf_ydeltas", "agrf_yoffsets"]:
                if k in new_config:
                    new_config[k] = [new_config[k][i] for i in indices]
            del new_config["agrf_subset"]

        return new_config


def render(config, vox_path, output_path=None):
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_clause = ["-o", output_path]
    else:
        output_clause = []

    scales = ",".join(map(str, config.config.get("agrf_scales", [1])))

    if config is None:
        subprocess.run(["gorender", "-s", scales, "-p"] + output_clause + [vox_path], check=True)
        return

    if config.config.get("agrf_palette"):
        palette_clause = ["-palette", config.config.get("agrf_palette")]
    else:
        palette_clause = []

    with tempfile.NamedTemporaryFile("w") as f:
        json.dump(config.final_config, f)
        f.flush()
        subprocess.run(
            ["gorender", "-s", scales, "-m", f.name, "-p"] + palette_clause + output_clause + [vox_path], check=True
        )


def positor(config, vox_path, new_path):
    # FIXME: new_path isn't the .vox file path, but its containing directory
    # if "file" in config["operations"][0]:
    #     other = config["operations"][0]["file"]
    #     try:
    #         if os.path.getmtime(vox_path) < os.path.getmtime(new_path) and os.path.getmtime(other) < os.path.getmtime(
    #             new_path
    #         ):
    #             return
    #     except:
    #         pass
    # else:
    #     try:
    #         if os.path.getmtime(vox_path) < os.path.getmtime(new_path):
    #             return
    #     except:
    #         pass

    os.makedirs(os.path.dirname(new_path), exist_ok=True)

    conf = config.copy()
    conf["files"] = [vox_path]
    with tempfile.NamedTemporaryFile("w") as f:
        json.dump(conf, f)
        f.flush()
        subprocess.run(["positor", "-o", new_path, f.name], check=True)


def hill_positor_1(vox_path, new_path, degree):
    config = {"operations": [{"name": "", "type": "rotate_y", "angle": degree}]}

    positor(config, vox_path, new_path)


def stairstep(vox_path, new_path, x_steps):
    config = {"operations": [{"name": "", "type": "stairstep", "x_steps": x_steps, "z_steps": 1}]}

    positor(config, vox_path, new_path)


def compose(vox_path, subvox_path, new_path, extra_config):
    config = {"operations": [{"name": "", "type": "repeat", "n": 1, "file": subvox_path, **extra_config}]}

    positor(config, vox_path, new_path)


def self_compose(vox_path, new_path, extra_config):
    config = {
        "operations": [
            {
                "name": "",
                "type": "repeat",
                "n": 1,
                "file": vox_path,
                "ignore_mask": True,
                "overwrite": True,
                **extra_config,
            }
        ]
    }

    positor(config, vox_path, new_path)


def produce_empty(vox_path, new_path):
    config = {"operations": [{"name": "", "type": "produce_empty"}]}

    positor(config, vox_path, new_path)


def discard_layers(discards, vox_path, new_path):
    try:
        if os.path.getmtime(vox_path) < os.path.getmtime(new_path):
            return
    except:
        pass
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    subprocess.run(
        ["layer-filter", "--source", vox_path, "--destination", new_path]
        + [x for discard in discards for x in ["--discard", discard]],
        check=True,
    )


def keep_layers(keeps, vox_path, new_path):
    try:
        if os.path.getmtime(vox_path) < os.path.getmtime(new_path):
            return
    except:
        pass
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    subprocess.run(
        ["layer-filter", "--source", vox_path, "--destination", new_path]
        + [x for keep in keeps for x in ["--keep", keep]],
        check=True,
    )

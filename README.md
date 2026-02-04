Ahyangyi's OpenTTD NewGRF Library
=================================

![Unit tests](https://github.com/ahyangyi/agrf/actions/workflows/unit-tests.yml/badge.svg)
![Coverage](https://codecov.io/gh/ahyangyi/agrf/branch/main/graph/badge.svg)

This library depends on [grf-py](https://github.com/citymania-org/grf-py), and implements additional high-level functionalities.

Main features:
* [gorender](https://github.com/mattkimber/gorender) and [cargopositor](https://github.com/mattkimber/cargopositor/) integration.
* Building (houses, stations, objects) library, modeling the OpenTTD features and abstractions such as symmetry modes on it.
* NewGRF parameter management, enabling parameter combination search.
* LayeredImage class to represent an image in the OpenTTD reality.
* "magic" classes such as MagicSwitch to simplify common transformations on NewGRF data structures.

# Reverse Dependencies
`agrf` is currently used by [China Set: Stations - Wuhu](https://github.com/OpenTTD-China-Set/China-Set-Stations-Wuhu) as well as [Ahyangyi's other NewGRFs](https://github.com/ahyangyi/openttd-newgrfs).

# License
This library is licensed in GPLv2+.

from enum import Enum


class Material(str, Enum):
    ALLOY_A = "Alloy-A"
    ALLOY_B = "Alloy-B"
    ALLOY_C = "Alloy-C"
    ALLOY_D = "Alloy-D"
    ALLOY_E = "Alloy-E"
    ALLOY_F = "Alloy-F"
    ALLOY_G = "Alloy-G"
    ALLOY_H = "Alloy-H"
    CAST_A = "Cast-A"
    CAST_B = "Cast-B"
    POLYMER_A = "Polymer-A"
    POLYMER_B = "Polymer-B"
    POLYMER_C = "Polymer-C"


class BlankType(str, Enum):
    EXTRUDED = "Extruded"
    ROLLED_SHEET = "Rolled sheet"
    ROLLED_PLATE = "Rolled plate >3mm"
    INJECTION_MOLDED = "Injection molded plastic"
    DIE_CAST = "Die cast"


class ElectricityGrid(str, Enum):
    REGION_A = "Region A"
    REGION_B = "Region B"
    REGION_C = "Region C"
    RENEWABLES = "100% renewables"


VALID_RECYCLED_CONTENT = {
    Material.POLYMER_A: [0, 50, 75, 100],
    Material.POLYMER_B: [0],
    Material.POLYMER_C: [0],
}

ALL_RECYCLED_CONTENT = [0, 25, 30, 50, 75, 100]

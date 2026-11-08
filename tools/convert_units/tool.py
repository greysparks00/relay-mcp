from math import isfinite

from pint import DimensionalityError, UnitRegistry


registry = UnitRegistry()
# Explicit aliases keep speech abbreviations predictable and identify US cooking measures.
ALIASES = {}
for unit, names in {
    "millimeter": "mm millimetre", "centimeter": "cm centimetre", "meter": "m metre",
    "kilometer": "km kilometre", "inch": "in inches", "foot": "ft feet", "yard": "yd", "mile": "mi",
    "milligram": "mg", "gram": "g", "kilogram": "kg", "ounce": "oz", "pound": "lb lbs",
    "milliliter": "ml millilitre", "liter": "l litre", "teaspoon": "tsp", "tablespoon": "tbsp",
    "fluid_ounce": "fl_oz", "cup": "", "pint": "pt", "quart": "qt", "gallon": "gal",
    "second": "s sec", "minute": "min", "hour": "h hr", "day": "", "week": "",
    "degC": "c celsius centigrade °c", "degF": "f fahrenheit °f", "kelvin": "k",
}.items():
    for alias in [unit.casefold(), *names.split()]:
        ALIASES[alias] = unit


def resolve(label: str) -> str:
    key = "_".join(label.casefold().strip().split())
    key = key.removeprefix("degrees_").removeprefix("degree_").removeprefix("us_")
    unit = ALIASES.get(key) or ALIASES.get(key.removesuffix("s"))
    if unit is None:
        raise ValueError(f"Unsupported unit: {label}")
    return unit


# Convert common length, mass, volume, temperature or duration units. Cooking volumes use US
# customary measures.
def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    if not isfinite(value):
        raise ValueError("Provide a finite number.")
    source, target = resolve(from_unit), resolve(to_unit)
    try:
        result = registry.Quantity(value, source).to(target).magnitude
    except DimensionalityError as error:
        raise ValueError("Choose units that measure the same quantity.") from error
    if not isfinite(result):
        raise ValueError("Converted value is outside the supported numeric range.")
    return {"value": float(format(result, ".12g")), "unit": target}

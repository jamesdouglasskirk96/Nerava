"""
Tesla VIN decoder - pure string parsing, no external API needed.

Tesla VIN structure (17 chars):
  Pos 1-3: WMI (5YJ = Fremont, 7SA = Austin, XP7 = Berlin, LRW = Shanghai)
  Pos 4:   Model (S, 3, X, Y, C=Cybertruck, R=Roadster 2.0)
  Pos 5:   Body type / variant
  Pos 6:   Motor / drive type
  Pos 7:   Energy (battery)
  Pos 8:   Check digit
  Pos 9:   —
  Pos 10:  Model year
  Pos 11:  Assembly plant
  Pos 12-17: Serial number
"""

MODEL_MAP = {
    "S": "Model S",
    "3": "Model 3",
    "X": "Model X",
    "Y": "Model Y",
    "C": "Cybertruck",
    "R": "Roadster",
}

YEAR_MAP = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014,
    "F": 2015, "G": 2016, "H": 2017, "J": 2018, "K": 2019,
    "L": 2020, "M": 2021, "N": 2022, "P": 2023, "R": 2024,
    "S": 2025, "T": 2026, "V": 2027, "W": 2028, "X": 2029,
    "Y": 2030,
}

DRIVE_MAP = {
    "A": "Single Motor RWD",
    "B": "Dual Motor AWD",
    "C": "Single Motor",
    "D": "Dual Motor AWD",
    "E": "Dual Motor",
    "F": "Performance AWD",
    "P": "Performance",
    "N": "Single Motor RWD",
}


def decode_tesla_vin(vin: str):
    """
    Decode a Tesla VIN to model, year, trim, drive type.

    Returns dict with keys: model, year, drive, display (e.g. "2024 Model Y Long Range")
    Returns None if VIN is invalid or not a Tesla VIN.
    """
    if not vin or len(vin) != 17:
        return None

    vin = vin.upper()

    # Check if it's a Tesla VIN (common WMIs)
    wmi = vin[:3]
    tesla_wmis = {"5YJ", "7SA", "XP7", "LRW", "7G2", "SFZ"}
    if wmi not in tesla_wmis:
        return None

    model_char = vin[3]
    year_char = vin[9]
    drive_char = vin[7] if len(vin) > 7 else None

    model = MODEL_MAP.get(model_char)
    year = YEAR_MAP.get(year_char)
    drive = DRIVE_MAP.get(drive_char, "") if drive_char else ""

    if not model or not year:
        return None

    # Build display string
    trim = ""
    if "Performance" in drive:
        trim = "Performance"
    elif "Dual Motor" in drive:
        trim = "Long Range"
    elif "Single Motor" in drive:
        trim = "Standard Range"

    parts = [str(year), model]
    if trim:
        parts.append(trim)

    return {
        "model": model,
        "year": year,
        "drive": drive,
        "trim": trim,
        "display": " ".join(parts),
    }

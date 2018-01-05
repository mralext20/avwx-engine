"""
Contains functions for handling and translating remarks
"""

from avwx.static import PRESSURE_TENDENCIES, REMARKS_ELEMENTS, REMARKS_GROUPS, WX_TRANSLATIONS


def _tdec(code: str, unit: str = 'C') -> str:
    """
    Translates a 4-digit decimal temperature representation

    Ex: 1045 -> -04.5°C    0237 -> 23.7°C
    """
    return f"{'-' if code[0] == '1' else ''}{int(code[1:3])}.{code[3]}°{unit}"


def temp_minmax(code: str) -> str:
    """
    Translates a 5-digit min/max temperature code
    """
    label = 'maximum' if code[0] == '1' else 'minimum'
    return f'6-hour {label} temperature {_tdec(code[1:])}'


def pressure_tendency(code: str, unit: str = 'mb') -> str:
    """
    Translates a 5-digit pressure outlook code

    Ex: 50123 -> 12.3 mb: Increasing, then decreasing
    """
    width, precision = int(code[2:4]), code[4]
    return ('3-hour pressure difference: +/- '
            f'{width}.{precision} {unit} - {PRESSURE_TENDENCIES[code[1]]}')


def precip_36(code: str, unit: str = 'in') -> str:
    """
    Translates a 5-digit 3 and 6-hour precipitation code
    """
    return ('Precipitation in the last 3 hours: '
            f'{int(code[1:3])} {unit}. - 6 hours: {int(code[3:])} {unit}.')


def precip_24(code: str, unit: str = 'in') -> str:
    """
    Translates a 5-digit 24-hour precipitation code
    """
    return f'Precipitation in the last 24 hours: {int(code[1:])} {unit}.'


def sunshine_duration(code: str, unit: str = 'minutes') -> str:
    """
    Translates a 5-digit sunlight duration code
    """
    return f'Duration of sunlight: {int(code[1:])} {unit}'


LEN5_DECODE = {
    '1': temp_minmax,
    '2': temp_minmax,
    '5': pressure_tendency,
    '6': precip_36,
    '7': precip_24,
    '9': sunshine_duration
}


def translate(remarks: str) -> {str: str}:
    """
    Translates elements in the remarks string
    """
    ret = {}
    # Add and replace static multi-word elements
    for key in REMARKS_GROUPS:
        if key in remarks:
            ret[key] = REMARKS_GROUPS[key]
            remarks.replace(key, ' ')
    # For each remaining element
    for rmk in remarks.split()[1:]:
        rlen = len(rmk)
        # Static single-word elements
        if rmk in REMARKS_ELEMENTS:
            ret[rmk] = REMARKS_ELEMENTS[rmk]
        # Digit-only encoded elements
        elif rmk.isdigit():
            if rlen == 5 and rmk[0] in LEN5_DECODE:
                ret[rmk] = LEN5_DECODE[rmk[0]](rmk)
            # 24-hour min/max temperature
            elif rlen == 9:
                ret[rmk] = f'24-hour temperature: max {_tdec(rmk[1:5])} min {_tdec(rmk[1:5])}'
        # Sea level pressure: SLP218
        elif rmk.startswith('SLP'):
            ret[rmk] = f'Sea level pressure: 10{rmk[3:5]}.{rmk[5]} hPa'
        # Temp/Dew with decimal: T02220183
        elif rlen == 9 and rmk[0] == 'T' and rmk[1:].isdigit():
            ret[rmk] = f'Temperature {_tdec(rmk[1:5])} and dewpoint {_tdec(rmk[5:])}'
        # Precipitation amount: P0123
        elif rlen == 5 and rmk[0] == 'P' and rmk[1:].isdigit():
            ret[rmk] = f'Hourly precipitation: {int(rmk[1:3])}.{rmk[3:]} in.'
        # Weather began/ended
        elif rlen == 5 and rmk[2] in ('B', 'E') and rmk[3:].isdigit() and rmk[:2] in WX_TRANSLATIONS:
            state = 'began' if rmk[2] == 'B' else 'ended'
            ret[rmk] = f'{WX_TRANSLATIONS[rmk[:2]]} {state} at :{int(rmk[3:])}'
    return ret

"""
Test translation functions
"""

# pytest: disable=redefined-builtin

# library
import unittest

# module
from avwx import static, structs
from avwx.current.base import get_wx_codes
from avwx.parsing import core, translate


class TestShared(unittest.TestCase):
    """Test shared translation functions"""

    def test_visibility(self):
        """Tests visibility translation and conversion"""
        for vis, unit, translation in (
            ("", "m", ""),
            ("0000", "m", "0km (0sm)"),
            ("2000", "m", "2km (1.2sm)"),
            ("0900", "m", "0.9km (0.6sm)"),
            ("P6", "sm", "Greater than 6sm ( >10km )"),
            ("M1/4", "sm", "Less than .25sm ( <0.4km )"),
            ("3/4", "sm", "0.75sm (1.2km)"),
            ("3/2", "sm", "1.5sm (2.4km)"),
            ("3", "sm", "3sm (4.8km)"),
        ):
            self.assertEqual(
                translate.base.visibility(core.make_number(vis), unit), translation
            )

    def test_altimeter(self):
        """Tests altimeter translation and conversion"""
        for alt, repr, unit, translation in (
            ("", "", "hPa", ""),
            ("1020", "1020", "hPa", "1020 hPa (30.12 inHg)"),
            ("0999", "0999", "hPa", "999 hPa (29.50 inHg)"),
            ("1012", "1012", "hPa", "1012 hPa (29.88 inHg)"),
            ("30.00", "3000", "inHg", "30.00 inHg (1016 hPa)"),
            ("29.92", "2992", "inHg", "29.92 inHg (1013 hPa)"),
            ("30.05", "3005", "inHg", "30.05 inHg (1018 hPa)"),
        ):
            self.assertEqual(
                translate.base.altimeter(core.make_number(alt, repr), unit), translation
            )

    def test_clouds(self):
        """Tests translating each cloud into a single string"""
        self.assertEqual(translate.base.clouds(None), "")
        self.assertEqual(translate.base.clouds([]), "Sky clear")
        for clouds, translation in (
            (["BKN", "FEW020"], "Few clouds at 2000ft"),
            (
                ["OVC030", "SCT100"],
                "Overcast layer at 3000ft, Scattered clouds at 10000ft",
            ),
            (["BKN015CB"], "Broken layer at 1500ft (Cumulonimbus)"),
        ):
            clouds = [core.make_cloud(cloud) for cloud in clouds]
            self.assertEqual(
                translate.base.clouds(clouds), translation + " - Reported AGL"
            )

    def test_wx_codes(self):
        """Tests translating a list of weather codes into a single string"""
        for codes, translation in (
            ([], ""),
            (["VCFC", "+RA"], "Vicinity Funnel Cloud, Heavy Rain"),
            (["-SN"], "Light Snow"),
        ):
            codes = get_wx_codes(codes)[1]
            self.assertEqual(translate.base.wx_codes(codes), translation)

    def test_shared(self):
        """Tests availability of shared values between the METAR and TAF translations"""
        units = structs.Units(**static.core.NA_UNITS)
        data = structs.SharedData(
            altimeter=core.make_number("2992"),
            clouds=[core.make_cloud("OVC060")],
            flight_rules="",
            other=[],
            sanitized="",
            visibility=core.make_number("10"),
            wind_direction=core.make_number("0"),
            wind_gust=core.make_number("0"),
            wind_speed=core.make_number("0"),
            wx_codes=get_wx_codes(["RA"])[1],
        )
        trans = translate.base.current_shared(data, units)
        self.assertIsInstance(trans, dict)
        for key in ("altimeter", "clouds", "visibility", "wx_codes"):
            self.assertIn(key, trans)
            self.assertTrue(bool(trans[key]))


class TestMetar(unittest.TestCase):
    """Test METAR translations"""

    def test_cardinal_direction(self):
        """Tests that a direction int returns the correct cardinal direction string"""
        # 12 - 360+
        keys = (12, 34, 57, 79)
        for i, cardinal in enumerate(
            [
                "NNE",
                "NE",
                "ENE",
                "E",
                "ESE",
                "SE",
                "SSE",
                "S",
                "SSW",
                "SW",
                "WSW",
                "W",
                "WNW",
                "NW",
                "NNW",
                "N",
            ]
        ):
            lower = keys[i % 4] + 90 * (i // 4)
            upper = (
                keys[0] + 90 * ((i // 4) + 1) - 1
                if i % 4 == 3
                else keys[(i % 4) + 1] + 90 * (i // 4) - 1
            )
            for direction in range(lower, upper + 1):
                self.assertEqual(
                    translate.base.get_cardinal_direction(direction), cardinal
                )
        # -0 - 11
        for direction in range(-10, 12):
            self.assertEqual(translate.base.get_cardinal_direction(direction), "N")

    def test_wind(self):
        """Tests that wind values are translating into a single string"""
        for *wind, vardir, translation in (
            ("", "", "", None, ""),
            (
                "360",
                "12",
                "20",
                ["340", "020"],
                "N-360 (variable 340 to 020) at 12kt gusting to 20kt",
            ),
            ("000", "00", "", None, "Calm"),
            ("VRB", "5", "12", None, "Variable at 5kt gusting to 12kt"),
            ("270", "10", "", ["240", "300"], "W-270 (variable 240 to 300) at 10kt"),
        ):
            wind = [core.make_number(i) for i in wind]
            if vardir:
                vardir = [core.make_number(i) for i in vardir]
            self.assertEqual(translate.base.wind(*wind, vardir), translation)

    def test_temperature(self):
        """Tests temperature translation and conversion"""
        for temp, unit, translation in (
            ("20", "F", "20°F (-7°C)"),
            ("M20", "F", "-20°F (-29°C)"),
            ("20", "C", "20°C (68°F)"),
            ("M20", "C", "-20°C (-4°F)"),
            ("", "F", ""),
        ):
            self.assertEqual(
                translate.base.temperature(core.make_number(temp), unit), translation
            )

    def test_metar(self):
        """Tests end-to-end METAR translation"""
        units = structs.Units(**static.core.NA_UNITS)
        data = {
            "altimeter": core.make_number("29.92", "2992"),
            "clouds": [core.make_cloud("BKN015CB")],
            "dewpoint": core.make_number("M01"),
            "other": [],
            "temperature": core.make_number("03"),
            "visibility": core.make_number("3"),
            "wind_direction": core.make_number("360"),
            "wind_gust": core.make_number("20"),
            "wind_speed": core.make_number("12"),
            "wind_variable_direction": [
                core.make_number("340"),
                core.make_number("020"),
            ],
            "wx_codes": get_wx_codes(["+RA"])[1],
        }
        data.update(
            {
                k: ""
                for k in (
                    "raw",
                    "remarks",
                    "station",
                    "time",
                    "flight_rules",
                    "remarks_info",
                    "runway_visibility",
                    "sanitized",
                )
            }
        )
        data = structs.MetarData(**data)
        trans = structs.MetarTrans(
            altimeter="29.92 inHg (1013 hPa)",
            clouds="Broken layer at 1500ft (Cumulonimbus) - Reported AGL",
            dewpoint="-1°C (30°F)",
            remarks={},
            temperature="3°C (37°F)",
            visibility="3sm (4.8km)",
            wind="N-360 (variable 340 to 020) at 12kt gusting to 20kt",
            wx_codes="Heavy Rain",
        )
        translated = translate.metar.translate_metar(data, units)
        self.assertIsInstance(translated, structs.MetarTrans)
        self.assertEqual(translated, trans)


class TestTaf(unittest.TestCase):
    """Test TAF translations"""

    def test_wind_shear(self):
        """Tests wind shear unpacking and translation"""
        for shear, translation in (
            ("", ""),
            ("WS020/07040KT", "Wind shear 2000ft from 070 at 40kt"),
            ("WS100/20020KT", "Wind shear 10000ft from 200 at 20kt"),
        ):
            self.assertEqual(translate.taf.wind_shear(shear), translation)

    def test_turb_ice(self):
        """Tests turbulence and icing translations"""
        for turb_ice, translation in (
            ([], ""),
            (
                ["540553"],
                "Occasional moderate turbulence in clouds from 5500ft to 8500ft",
            ),
            (["611005"], "Light icing from 10000ft to 15000ft"),
            (
                ["610023", "610062"],
                "Light icing from 200ft to 3200ft, Light icing from 600ft to 2600ft",
            ),
        ):
            self.assertEqual(translate.taf.turb_ice(turb_ice), translation)

    def test_min_max_temp(self):
        """Tests temperature time translation and conversion"""
        for temp, translation in (
            ("", ""),
            ("TX20/1518Z", "Maximum temperature of 20°C (68°F) at 15-18:00Z"),
            ("TXM02/04", "Maximum temperature of -2°C (28°F) at 04:00Z"),
            ("TN00/00", "Minimum temperature of 0°C (32°F) at 00:00Z"),
        ):
            self.assertEqual(translate.taf.min_max_temp(temp), translation)

    def test_taf(self):
        """Tests end-to-end TAF translation"""
        units = structs.Units(**static.core.NA_UNITS)
        line_data = {
            "altimeter": core.make_number("29.92", "2992"),
            "clouds": [core.make_cloud("BKN015CB")],
            "icing": ["611005"],
            "other": [],
            "turbulence": ["540553"],
            "visibility": core.make_number("3"),
            "wind_direction": core.make_number("360"),
            "wind_gust": core.make_number("20"),
            "wind_shear": "WS020/07040KT",
            "wind_speed": core.make_number("12"),
            "wx_codes": get_wx_codes(["+RA"])[1],
        }
        line_data.update(
            {
                k: ""
                for k in (
                    "raw",
                    "end_time",
                    "start_time",
                    "transition_start",
                    "probability",
                    "type",
                    "flight_rules",
                    "sanitized",
                )
            }
        )
        data = {"max_temp": "TX20/1518Z", "min_temp": "TN00/00", "remarks": ""}
        data.update(
            {k: "" for k in ("raw", "station", "time", "start_time", "end_time")}
        )
        data = structs.TafData(forecast=[structs.TafLineData(**line_data)], **data)
        line_trans = structs.TafLineTrans(
            altimeter="29.92 inHg (1013 hPa)",
            clouds="Broken layer at 1500ft (Cumulonimbus) - Reported AGL",
            icing="Light icing from 10000ft to 15000ft",
            turbulence="Occasional moderate turbulence in clouds from 5500ft to 8500ft",
            visibility="3sm (4.8km)",
            wind_shear="Wind shear 2000ft from 070 at 40kt",
            wind="N-360 at 12kt gusting to 20kt",
            wx_codes="Heavy Rain",
        )
        trans = structs.TafTrans(
            forecast=[line_trans],
            max_temp="Maximum temperature of 20°C (68°F) at 15-18:00Z",
            min_temp="Minimum temperature of 0°C (32°F) at 00:00Z",
            remarks={},
        )
        translated = translate.taf.translate_taf(data, units)
        self.assertIsInstance(translated, structs.TafTrans)
        for line in translated.forecast:
            self.assertIsInstance(line, structs.TafLineTrans)
        self.assertEqual(translated, trans)

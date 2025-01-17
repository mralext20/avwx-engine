"""
ScrapeService API Tests
"""

# pylint: disable=protected-access,missing-class-docstring,unidiomatic-typecheck

# stdlib
import unittest

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import BaseTestService


class TestScrapeService(BaseTestService):

    service_class = service.scrape.ScrapeService
    report_type = "metar"
    required_attrs = ("method", "_strip_whitespace", "_extract")

    def test_service(self):
        """Tests for expected values and method implementation"""
        # pylint: disable=no-member
        if type(self.serv) == service.scrape.ScrapeService:
            self.assertIsNone(self.serv.url)
            with self.assertRaises(NotImplementedError):
                self.serv._extract(None)
        else:
            self.assertIsInstance(self.serv.url, str)
        self.assertIsInstance(self.serv.method, str)
        self.assertIn(self.serv.method, ("GET", "POST"))

    def test_make_err(self):
        """Tests that InvalidRequest exceptions are generated with the right message"""
        # pylint: disable=no-member
        key, msg = "test_key", "testing"
        err = self.serv._make_err(msg, key)
        err_str = (
            f"Could not find {key} in {self.serv.__class__.__name__} response\n{msg}"
        )
        self.assertIsInstance(err, exceptions.InvalidRequest)
        self.assertEqual(err.args, (err_str,))
        self.assertEqual(str(err), err_str)

    def test_fetch_exceptions(self):
        """Tests fetch exception handling"""
        for station in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                self.serv.fetch(station)
        # Should raise exception due to empty url
        if type(self.serv) == service.scrape.ScrapeService:
            with self.assertRaises(NotImplementedError):
                self.serv.fetch("KJFK")

    @pytest.mark.asyncio
    async def test_async_fetch_exceptions(self):
        """Tests async fetch exception handling"""
        for station in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                await self.serv.async_fetch(station)
        # Should raise exception due to empty url
        if type(self.serv) == service.scrape.ScrapeService:
            with self.assertRaises(NotImplementedError):
                await self.serv.async_fetch("KJFK")


class TestNOAA(TestScrapeService):

    service_class = service.NOAA
    stations = ["KJFK", "EGLL", "PHNL"]


class TestAMO(TestScrapeService):

    service_class = service.AMO
    stations = ["RKSI", "RKSS", "RKNY"]


class TestMAC(TestScrapeService):

    service_class = service.MAC
    stations = ["SKBO"]


class TestAUBOM(TestScrapeService):

    service_class = service.AUBOM
    stations = ["YBBN", "YSSY", "YCNK"]


class TestModule(unittest.TestCase):
    def test_get_service(self):
        """Tests that the correct service class is returned"""
        for stations, country, serv in (
            (("KJFK", "PHNL"), "US", service.NOAA),
            (("EGLL",), "GB", service.NOAA),
            (("RKSI",), "KR", service.AMO),
            (("SKBO", "SKPP"), "CO", service.MAC),
            (("YWOL", "YSSY"), "AU", service.AUBOM),
        ):
            for station in stations:
                self.assertIsInstance(
                    service.get_service(station, country)("metar"), serv
                )

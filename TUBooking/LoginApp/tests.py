"""Tests for TU REST API integration.

The live integration test runs only when TU_API_APP_KEY plus the
TU_API_LIVE_USER/TU_API_LIVE_PASS env vars are set (e.g. on CI runs that
have access to the GitHub secret), so plain local runs without the secret
won't fail.
"""

import os
import unittest

from django.test import TestCase

from .tu_api import TUAPIError, verify_credentials


class TUAPIGuardTests(TestCase):
    def test_missing_app_key_raises(self):
        with self.settings(TU_API_APP_KEY=""):
            with self.assertRaises(TUAPIError):
                verify_credentials("anyone", "anything")


@unittest.skipUnless(
    os.environ.get("TU_API_APP_KEY") and os.environ.get("TU_API_LIVE_USER"),
    "Set TU_API_APP_KEY and TU_API_LIVE_USER/TU_API_LIVE_PASS to run live test.",
)
class TUAPILiveTests(TestCase):
    def test_valid_credentials_return_profile(self):
        result = verify_credentials(
            os.environ["TU_API_LIVE_USER"],
            os.environ["TU_API_LIVE_PASS"],
        )
        self.assertIsNotNone(result, "Expected TU API to accept credentials.")
        self.assertEqual(result["username"], os.environ["TU_API_LIVE_USER"])

    def test_bad_credentials_return_none(self):
        result = verify_credentials("0000000000", "wrong-password")
        self.assertIsNone(result)

# -*- coding: utf-8 -*-
"""Tests for the first project health endpoint.

@author project team
@version 0.1.0
"""

from django.test import TestCase


class HealthCheckTests(TestCase):
    """Verify the HTTP contract of the health endpoint."""

    def test_health_check_returns_ok(self) -> None:
        """A GET request returns a JSON success response."""
        response = self.client.get("/healthz/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_rejects_non_get_requests(self) -> None:
        """The endpoint accepts only GET requests."""
        response = self.client.post("/healthz/")

        self.assertEqual(response.status_code, 405)

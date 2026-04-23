"""Unit tests for utility functions in routes.py."""
import string
import pytest

from app.api.routes import generate_code


class TestGenerateCode:
    def test_default_length(self):
        code = generate_code()
        assert len(code) == 6

    def test_custom_length(self):
        for length in [4, 8, 12]:
            code = generate_code(length=length)
            assert len(code) == length

    def test_characters_are_alphanumeric(self):
        allowed = set(string.ascii_letters + string.digits)
        for _ in range(20):
            code = generate_code()
            assert set(code).issubset(allowed), f"Unexpected chars in: {code}"

    def test_returns_string(self):
        assert isinstance(generate_code(), str)

    def test_codes_are_random(self):
        """Generate many codes and verify there is variation (not all identical)."""
        codes = {generate_code() for _ in range(50)}
        # With 62^6 possibilities, the chance all 50 are the same is astronomically small.
        assert len(codes) > 1

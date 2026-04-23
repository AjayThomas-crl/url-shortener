"""
Comprehensive integration tests for all API routes.

Coverage targets
----------------
GET  /health               – health check
GET  /                     – homepage renders
GET  /admin                – admin dashboard (empty & populated)
GET  /qr/{short_code}      – QR code image generation
POST /shorten              – shorten URL (valid, invalid, custom code, expiration, one-time use)
GET  /{short_code}         – redirect (found, not found, expired, one-time use, click counter)
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.models import URL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_url(db: Session, original_url: str, short_code: str, **kwargs) -> URL:
    """Insert a URL record directly into the test DB."""
    url = URL(original_url=original_url, short_code=short_code, **kwargs)
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


def _shorten(client, long_url: str, **extra_fields):
    """POST to /shorten with optional extra form fields."""
    data = {"long_url": long_url}
    data.update(extra_fields)
    return client.post("/shorten", data=data, follow_redirects=True)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_body(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert body["service"] == "url-shortener"


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------

class TestHomepage:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_contains_form(self, client):
        html = client.get("/").text
        assert "<form" in html.lower()


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

class TestAdminDashboard:
    def test_returns_200_empty(self, client):
        response = client.get("/admin")
        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/admin")
        assert "text/html" in response.headers["content-type"]

    def test_shows_existing_urls(self, client, db_session):
        _create_url(db_session, "https://example.com", "abc123")
        response = client.get("/admin")
        assert response.status_code == 200
        assert "abc123" in response.text

    def test_shows_multiple_urls(self, client, db_session):
        _create_url(db_session, "https://example.com", "code1")
        _create_url(db_session, "https://other.com", "code2")
        response = client.get("/admin")
        assert "code1" in response.text
        assert "code2" in response.text


# ---------------------------------------------------------------------------
# QR code generation
# ---------------------------------------------------------------------------

class TestQRCodeGeneration:
    def test_returns_200(self, client):
        response = client.get("/qr/anycode")
        assert response.status_code == 200

    def test_returns_png_image(self, client):
        response = client.get("/qr/anycode")
        assert response.headers["content-type"] == "image/png"

    def test_response_is_non_empty_bytes(self, client):
        response = client.get("/qr/testcode")
        assert len(response.content) > 0

    def test_different_codes_produce_different_images(self, client):
        img1 = client.get("/qr/codeA").content
        img2 = client.get("/qr/codeB").content
        assert img1 != img2


# ---------------------------------------------------------------------------
# URL shortening
# ---------------------------------------------------------------------------

class TestShortenURL:
    # --- valid URLs ---

    def test_valid_url_returns_200(self, client):
        response = _shorten(client, "https://example.com")
        assert response.status_code == 200

    def test_shortened_url_appears_in_response(self, client):
        response = _shorten(client, "https://example.com")
        assert "http://testserver/" in response.text

    def test_shortened_url_with_http_scheme(self, client):
        response = _shorten(client, "http://example.com")
        assert response.status_code == 200

    def test_url_with_path_and_query(self, client):
        response = _shorten(client, "https://example.com/path?q=hello")
        assert response.status_code == 200

    # --- invalid URLs ---

    def test_missing_scheme_returns_error(self, client):
        response = _shorten(client, "example.com")
        assert response.status_code == 200
        assert "invalid url" in response.text.lower()

    def test_empty_url_returns_error(self, client):
        response = _shorten(client, "")
        assert response.status_code == 200
        assert "invalid url" in response.text.lower()

    def test_only_scheme_returns_error(self, client):
        response = _shorten(client, "https://")
        assert response.status_code == 200
        assert "invalid url" in response.text.lower()

    # --- custom code ---

    def test_custom_code_appears_in_short_url(self, client):
        response = _shorten(client, "https://example.com", custom_code="mycode")
        assert "mycode" in response.text

    def test_duplicate_custom_code_returns_error(self, client, db_session):
        _create_url(db_session, "https://example.com", "taken")
        response = _shorten(client, "https://other.com", custom_code="taken")
        assert response.status_code == 200
        assert "already in use" in response.text.lower()

    def test_unique_custom_codes_both_succeed(self, client):
        r1 = _shorten(client, "https://example.com", custom_code="first1")
        r2 = _shorten(client, "https://other.com", custom_code="second2")
        assert "first1" in r1.text
        assert "second2" in r2.text

    # --- expiration ---

    def test_expiration_zero_stores_no_expiry(self, client, db_session):
        _shorten(client, "https://example.com", custom_code="noexpiry", expiration=0)
        url = db_session.query(URL).filter(URL.short_code == "noexpiry").first()
        assert url is not None
        assert url.expires_at is None

    def test_expiration_positive_stores_expiry(self, client, db_session):
        _shorten(client, "https://example.com", custom_code="withexp", expiration=24)
        url = db_session.query(URL).filter(URL.short_code == "withexp").first()
        assert url is not None
        assert url.expires_at is not None

    def test_expiration_is_approximately_correct(self, client, db_session):
        before = datetime.now()
        _shorten(client, "https://example.com", custom_code="expcheck", expiration=1)
        after = datetime.now()
        url = db_session.query(URL).filter(URL.short_code == "expcheck").first()
        expected_min = before + timedelta(hours=1)
        expected_max = after + timedelta(hours=1)
        assert expected_min <= url.expires_at <= expected_max

    # --- one-time use ---

    def test_one_time_use_stored_true(self, client, db_session):
        _shorten(client, "https://example.com", custom_code="otu1", one_time_use=True)
        url = db_session.query(URL).filter(URL.short_code == "otu1").first()
        assert url is not None
        assert url.one_time_use is True

    def test_no_one_time_use_stored_false(self, client, db_session):
        _shorten(client, "https://example.com", custom_code="nootu")
        url = db_session.query(URL).filter(URL.short_code == "nootu").first()
        assert url is not None
        assert url.one_time_use is False

    # --- DB record ---

    def test_record_is_persisted_in_database(self, client, db_session):
        _shorten(client, "https://persist-test.com", custom_code="persist")
        url = db_session.query(URL).filter(URL.short_code == "persist").first()
        assert url is not None
        assert url.original_url == "https://persist-test.com"

    def test_initial_click_count_is_zero(self, client, db_session):
        _shorten(client, "https://example.com", custom_code="clicks0")
        url = db_session.query(URL).filter(URL.short_code == "clicks0").first()
        assert url.clicks == 0


# ---------------------------------------------------------------------------
# Redirect
# ---------------------------------------------------------------------------

class TestRedirect:
    def test_valid_code_redirects(self, client, db_session):
        _create_url(db_session, "https://example.com", "redir1")
        response = client.get("/redir1", follow_redirects=False)
        assert response.status_code == 307

    def test_redirect_location_is_original_url(self, client, db_session):
        _create_url(db_session, "https://example.com/target", "redir2")
        response = client.get("/redir2", follow_redirects=False)
        assert response.headers["location"] == "https://example.com/target"

    def test_unknown_code_returns_404(self, client):
        response = client.get("/doesnotexist")
        assert response.status_code == 404

    def test_click_counter_increments_on_visit(self, client, db_session):
        _create_url(db_session, "https://example.com", "clickme")
        client.get("/clickme", follow_redirects=False)
        db_session.expire_all()
        url = db_session.query(URL).filter(URL.short_code == "clickme").first()
        assert url.clicks == 1

    def test_click_counter_increments_multiple_times(self, client, db_session):
        _create_url(db_session, "https://example.com", "multi")
        for _ in range(3):
            client.get("/multi", follow_redirects=False)
        db_session.expire_all()
        url = db_session.query(URL).filter(URL.short_code == "multi").first()
        assert url.clicks == 3

    def test_expired_url_shows_expired_page(self, client, db_session):
        past = datetime.now() - timedelta(hours=1)
        _create_url(db_session, "https://example.com", "expired1", expires_at=past)
        response = client.get("/expired1", follow_redirects=False)
        assert response.status_code == 200
        assert "expired" in response.text.lower()

    def test_non_expired_url_redirects_normally(self, client, db_session):
        future = datetime.now() + timedelta(hours=1)
        _create_url(db_session, "https://example.com", "live1", expires_at=future)
        response = client.get("/live1", follow_redirects=False)
        assert response.status_code == 307

    def test_one_time_use_url_is_deleted_after_visit(self, client, db_session):
        _create_url(db_session, "https://example.com", "otu", one_time_use=True)
        client.get("/otu", follow_redirects=False)
        db_session.expire_all()
        url = db_session.query(URL).filter(URL.short_code == "otu").first()
        assert url is None

    def test_one_time_use_url_second_visit_returns_404(self, client, db_session):
        _create_url(db_session, "https://example.com", "otu2", one_time_use=True)
        client.get("/otu2", follow_redirects=False)
        response = client.get("/otu2", follow_redirects=False)
        assert response.status_code == 404

    def test_non_one_time_use_url_is_not_deleted(self, client, db_session):
        _create_url(db_session, "https://example.com", "permanent")
        client.get("/permanent", follow_redirects=False)
        db_session.expire_all()
        url = db_session.query(URL).filter(URL.short_code == "permanent").first()
        assert url is not None

    def test_url_without_expiry_redirects_normally(self, client, db_session):
        _create_url(db_session, "https://example.com", "noexp")
        response = client.get("/noexp", follow_redirects=False)
        assert response.status_code == 307

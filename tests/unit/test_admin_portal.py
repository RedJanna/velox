"""Unit tests for admin portal bootstrap request guards."""

from starlette.requests import Request

from velox.api.routes import admin_portal


def _build_request(
    *,
    client_host: str,
    host_header: str = "testserver",
    cf_connecting_ip: str | None = None,
    forwarded_for: str | None = None,
    real_ip: str | None = None,
) -> Request:
    """Create a minimal request with controllable network headers."""
    headers = [(b"host", host_header.encode("utf-8"))]
    if cf_connecting_ip is not None:
        headers.append((b"cf-connecting-ip", cf_connecting_ip.encode("utf-8")))
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode("utf-8")))
    if real_ip is not None:
        headers.append((b"x-real-ip", real_ip.encode("utf-8")))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/admin/bootstrap/status",
            "raw_path": b"/api/v1/admin/bootstrap/status",
            "query_string": b"",
            "headers": headers,
            "client": (client_host, 12345),
            "server": ("testserver", 80),
        }
    )


def test_local_bootstrap_allows_loopback_forwarded_ip() -> None:
    request = _build_request(client_host="172.18.0.1", forwarded_for="127.0.0.1")

    assert admin_portal._is_local_bootstrap_request(request) is True


def test_local_bootstrap_allows_loopback_cloudflare_ip_header() -> None:
    request = _build_request(client_host="172.18.0.1", cf_connecting_ip="127.0.0.1")

    assert admin_portal._is_local_bootstrap_request(request) is True


def test_local_bootstrap_allows_local_host_header_with_private_bridge_client() -> None:
    request = _build_request(client_host="172.18.0.1", host_header="127.0.0.1:8001")

    assert admin_portal._is_local_bootstrap_request(request) is True


def test_local_bootstrap_rejects_public_client_with_spoofed_local_host_header() -> None:
    request = _build_request(client_host="8.8.8.8", host_header="localhost:8001")

    assert admin_portal._is_local_bootstrap_request(request) is False

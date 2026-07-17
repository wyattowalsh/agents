"""Hop-safe SSRF policy for source-url-health probes.

Pure functions: no FastMCP. Callers supply an HttpLike transport that never
auto-follows redirects.

Each hop resolves all addresses fail-closed, then requires ``request_pinned``
so the connect peer is an approved IP while Host/SNI preserve the logical
hostname. Clients without that contract are rejected rather than retried on an
unpinned path.
"""

from __future__ import annotations

import ipaddress
import math
import socket
import time
from typing import Any, Protocol
from urllib.parse import urljoin, urlsplit, urlunsplit

import idna

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_MAX_REDIRECTS = 5
_MAX_PIN_TRIES = 4
_MAX_URL_CHARS = 4096
_NAT64_NETWORKS = (
    ("NAT64 well-known", ipaddress.IPv6Network("64:ff9b::/96")),
    ("NAT64 local-use", ipaddress.IPv6Network("64:ff9b:1::/48")),
)
_TRANSPORT_ERROR_NAMES = frozenset({
    "ConnectError",
    "ConnectTimeout",
    "ReadTimeout",
    "WriteTimeout",
    "PoolTimeout",
    "TimeoutException",
    "NetworkError",
    "ProxyError",
})


class HttpLike(Protocol):
    def request_pinned(
        self,
        method: str,
        url: str,
        *,
        pinned_ip: str,
        timeout: float,
        follow_redirects: bool = False,
    ) -> Any: ...


def _ipv6_transition_reason(addr: ipaddress.IPv6Address) -> str | None:
    """Identify IPv4 transition forms that must never bypass IPv4 policy."""
    if addr.ipv4_mapped is not None:
        return "IPv4-mapped"
    if addr.sixtofour is not None:
        return "6to4"
    if addr.teredo is not None:
        return "Teredo"
    for label, network in _NAT64_NETWORKS:
        if addr in network:
            return label
    return None


def _blocked_address_reason(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str | None:
    """Return why *addr* is unsafe, treating transition mechanisms fail-closed."""
    if isinstance(addr, ipaddress.IPv6Address):
        transition = _ipv6_transition_reason(addr)
        if transition is not None:
            return f"IPv6 transition address ({transition})"
    if not addr.is_global:
        return "address is not globally routable"
    return None


def _addr_is_blocked(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Fail closed for non-global and IPv4-transition addresses."""
    return _blocked_address_reason(addr) is not None


def _canonical_hostname(hostname: str) -> tuple[str, str | None]:
    host = (hostname or "").strip().lower().rstrip(".")
    if not host:
        return "", "empty hostname"
    try:
        return str(ipaddress.ip_address(host)), None
    except ValueError:
        pass
    try:
        # HTTPX depends on the ``idna`` package. Use the same IDNA2008 engine,
        # with UTS 46 mapping and STD3 validation for ASCII and Unicode labels.
        ascii_host = idna.encode(host, uts46=True, std3_rules=True, transitional=False).decode("ascii").lower()
    except (idna.IDNAError, UnicodeError, ValueError):
        return "", "hostname is not valid IDNA"
    if len(ascii_host) > 253 or any(not label or len(label) > 63 for label in ascii_host.split(".")):
        return "", "hostname length is invalid"
    return ascii_host, None


def _canonicalize_url(url: str) -> tuple[str, str, str | None]:
    """Return ``(canonical_url, hostname, error)`` without resolving DNS."""
    if not isinstance(url, str) or not url.strip():
        return "", "", "url must be a non-empty string"
    if any(ord(char) < 32 or ord(char) == 127 for char in url):
        return "", "", "url contains a control character"
    raw = url.strip()
    if len(raw) > _MAX_URL_CHARS:
        return "", "", f"url exceeds {_MAX_URL_CHARS} characters"
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        return "", "", f"url parse failed: {exc}"
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        return "", "", f"scheme not allowed: {parsed.scheme!r} (only http/https)"
    if parsed.username is not None or parsed.password is not None:
        return "", "", "url userinfo is not allowed"
    if "#" in raw:
        return "", "", "url fragment is not allowed"
    try:
        hostname = parsed.hostname or ""
        port = parsed.port
    except ValueError as exc:
        return "", "", f"url port is invalid: {exc}"
    if not hostname:
        return "", "", "url missing hostname"
    if port is not None and port < 1:
        return "", "", "url port is invalid: must be between 1 and 65535"
    hostname, host_error = _canonical_hostname(hostname)
    if host_error:
        return "", "", host_error
    try:
        addr = ipaddress.ip_address(hostname)
        display_host = f"[{hostname}]" if addr.version == 6 else hostname
    except ValueError:
        display_host = hostname
    netloc = f"{display_host}:{port}" if port is not None else display_host
    canonical = urlunsplit((scheme, netloc, parsed.path, parsed.query, ""))
    if len(canonical) > _MAX_URL_CHARS:
        return "", "", f"canonical url exceeds {_MAX_URL_CHARS} characters"
    return canonical, hostname, None


def resolve_public_addresses(hostname: str) -> tuple[list[str], str | None]:
    """Resolve *hostname* to public addresses only.

    Returns ``(addresses, None)`` on success or ``([], error)`` when blocked
    or DNS fails (fail-closed).
    """
    host, host_error = _canonical_hostname(hostname)
    if host_error:
        return [], host_error
    if host in {"localhost", "metadata.google.internal", "metadata"}:
        return [], f"blocked host: {host}"
    if host.endswith(".local") or host.endswith(".internal"):
        return [], f"blocked host suffix: {host}"

    try:
        literal = ipaddress.ip_address(host)
        reason = _blocked_address_reason(literal)
        if reason is not None:
            return [], f"blocked address: {host} ({reason})"
        return [host], None
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError):
        return [], f"dns_resolution_failed: {host}"

    public: list[str] = []
    seen: set[str] = set()
    for info in infos:
        raw = str(info[4][0])
        if raw in seen:
            continue
        seen.add(raw)
        try:
            addr = ipaddress.ip_address(raw)
        except ValueError:
            return [], f"dns returned invalid address: {raw}"
        reason = _blocked_address_reason(addr)
        if reason is not None:
            return [], f"resolves to blocked address: {raw} ({reason})"
        public.append(raw)

    if not public:
        return [], f"no_resolvable_addresses: {host}"
    return public, None


def blocked_host_reason(hostname: str) -> str | None:
    """Return block reason for *hostname*, else None if safe to contact."""
    _addrs, err = resolve_public_addresses(hostname)
    return err


def validate_url_for_probe(url: str) -> str | None:
    """Return an error string if *url* must not be fetched; else None."""
    _canonical, hostname, error = _canonicalize_url(url)
    if error:
        return error
    return blocked_host_reason(hostname)


def url_for_pinned_connect(url: str, pinned_ip: str) -> tuple[str, str]:
    """Rewrite *url* netloc to *pinned_ip*; return ``(pinned_url, original_hostname)``."""
    canonical, hostname, error = _canonicalize_url(url)
    if error:
        raise ValueError(error)
    parsed = urlsplit(canonical)
    # Bracket IPv6 literals in netloc.
    try:
        addr = ipaddress.ip_address(pinned_ip)
    except ValueError as exc:
        raise ValueError(f"invalid pinned address: {pinned_ip}") from exc
    reason = _blocked_address_reason(addr)
    if reason is not None:
        raise ValueError(f"pinned address is blocked: {pinned_ip} ({reason})")
    host_lit = f"[{pinned_ip}]" if addr.version == 6 else pinned_ip
    port = parsed.port
    netloc = f"{host_lit}:{port}" if port else host_lit
    pinned_url = urlunsplit(parsed._replace(netloc=netloc))
    return pinned_url, hostname


def _header_get(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    try:
        value = headers.get(name) or headers.get(name.lower()) or headers.get(name.title())
    except Exception:
        return None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _next_location(current_url: str, response: Any) -> str | None:
    status = int(getattr(response, "status_code", 0) or 0)
    if status not in _REDIRECT_STATUSES:
        return None
    location = _header_get(response, "location")
    if not location:
        return None
    return urljoin(current_url, location)


def _result(
    *,
    url: str,
    ok: bool,
    status_code: int | None,
    final_url: str | None,
    started: float,
    error: str | None,
    pinned_addresses: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "url": url,
        "ok": ok,
        "status_code": status_code,
        "final_url": final_url,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
        "error": error,
    }
    if pinned_addresses is not None:
        payload["pinned_addresses"] = list(pinned_addresses)
    return payload


def _is_transport_error(exc: BaseException) -> bool:
    """Return True for connect/timeout-class failures that warrant trying the next pin."""
    if isinstance(exc, (ConnectionError, OSError, TimeoutError)):
        return True
    return type(exc).__name__ in _TRANSPORT_ERROR_NAMES


def _close_response(response: Any | None) -> None:
    if response is None:
        return
    close = getattr(response, "close", None)
    if callable(close):
        close()


def _remaining_timeout(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("total timeout exceeded")
    return remaining


def _hop_request(
    http: Any,
    method: str,
    url: str,
    *,
    timeout: float,
    pinned_ip: str,
) -> Any:
    """Issue HEAD/GET using pinned connect peer when transport supports it."""
    method_u = method.upper()
    request_pinned = getattr(http, "request_pinned", None)
    if not callable(request_pinned):
        raise ValueError("http client does not implement fail-closed request pinning")
    return request_pinned(
        method_u,
        url,
        pinned_ip=pinned_ip,
        timeout=timeout,
        follow_redirects=False,
    )


def _request_with_pin_retries(
    http: Any,
    method: str,
    url: str,
    *,
    deadline: float,
    pinned: list[str],
) -> Any:
    """Try each public pin until transport succeeds or pins are exhausted."""
    last_exc: BaseException | None = None
    for pinned_ip in pinned[:_MAX_PIN_TRIES]:
        try:
            return _hop_request(
                http,
                method,
                url,
                timeout=_remaining_timeout(deadline),
                pinned_ip=pinned_ip,
            )
        except Exception as exc:
            if not _is_transport_error(exc):
                raise
            last_exc = exc
    if last_exc is None:
        raise ValueError("no pinned addresses available")
    raise last_exc


def check_once(http: HttpLike, url: str, timeout_sec: float) -> dict[str, Any]:
    """Probe *url* with a best-effort shared budget and hop-safe HEAD.

    GET is used only after a 405 and redirects are never auto-followed. The
    budget is checked between DNS, pin, and redirect stages, but synchronous
    ``socket.getaddrinfo`` cannot be interrupted and HTTPX timeouts are
    per-phase, so this function cannot promise a hard wall-clock deadline.
    """
    started = time.monotonic()
    try:
        budget = float(timeout_sec)
    except (TypeError, ValueError):
        budget = 0.0
    if not math.isfinite(budget) or budget <= 0:
        budget = 0.0
    deadline = started + budget
    original = url
    current = (url or "").strip()
    seen: set[str] = set()
    last_pinned: list[str] = []

    for hop in range(_MAX_REDIRECTS + 1):
        canonical, hostname, url_error = _canonicalize_url(current)
        if url_error:
            prefix = "ssrf_blocked_redirect" if hop > 0 else "ssrf_blocked"
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=current if hop > 0 else None,
                started=started,
                error=f"{prefix}: {url_error}",
            )
        current = canonical
        if current in seen:
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=current,
                started=started,
                error="ssrf_blocked: redirect_loop",
            )
        seen.add(current)

        parsed = urlsplit(current)
        try:
            _remaining_timeout(deadline)
        except TimeoutError as exc:
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=current if hop > 0 else None,
                started=started,
                error=f"TimeoutError: {exc}",
                pinned_addresses=last_pinned,
            )
        pinned, resolve_err = resolve_public_addresses(hostname)
        if resolve_err:
            prefix = "ssrf_blocked_redirect" if hop > 0 else "ssrf_blocked"
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=current if hop > 0 else None,
                started=started,
                error=f"{prefix}: {resolve_err}",
                pinned_addresses=[],
            )
        last_pinned = pinned

        response: Any | None = None
        try:
            response = _request_with_pin_retries(http, "HEAD", current, deadline=deadline, pinned=pinned)
            status = int(getattr(response, "status_code", 0) or 0)
            # Only Method Not Allowed triggers GET fallback (not all 4xx/5xx).
            if status == 405:
                _close_response(response)
                response = None
                response = _request_with_pin_retries(http, "GET", current, deadline=deadline, pinned=pinned)
                status = int(getattr(response, "status_code", 0) or 0)
            _remaining_timeout(deadline)
        except Exception as exc:  # httpx.HTTPError and test doubles
            _close_response(response)
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=None,
                started=started,
                error=f"{type(exc).__name__}: {exc}",
                pinned_addresses=last_pinned,
            )

        try:
            next_url = _next_location(current, response)
        except (UnicodeError, ValueError) as exc:
            _close_response(response)
            return _result(
                url=original,
                ok=False,
                status_code=None,
                final_url=current,
                started=started,
                error=f"ssrf_blocked_redirect: url parse failed: {exc}",
                pinned_addresses=last_pinned,
            )
        _close_response(response)
        if next_url is not None:
            if hop >= _MAX_REDIRECTS:
                return _result(
                    url=original,
                    ok=False,
                    status_code=None,
                    final_url=current,
                    started=started,
                    error="ssrf_blocked: max_redirects",
                    pinned_addresses=last_pinned,
                )
            next_canonical, _next_hostname, next_error = _canonicalize_url(next_url)
            if next_error:
                return _result(
                    url=original,
                    ok=False,
                    status_code=None,
                    final_url=next_url,
                    started=started,
                    error=f"ssrf_blocked_redirect: {next_error}",
                    pinned_addresses=last_pinned,
                )
            cur_scheme = parsed.scheme.lower()
            next_scheme = urlsplit(next_canonical).scheme.lower()
            if cur_scheme == "https" and next_scheme == "http":
                return _result(
                    url=original,
                    ok=False,
                    status_code=None,
                    final_url=next_url,
                    started=started,
                    error="ssrf_blocked: scheme_downgrade",
                    pinned_addresses=last_pinned,
                )
            current = next_canonical
            continue

        return _result(
            url=original,
            ok=status < 400,
            status_code=status,
            final_url=current,
            started=started,
            error=None,
            pinned_addresses=last_pinned,
        )

    return _result(
        url=original,
        ok=False,
        status_code=None,
        final_url=current,
        started=started,
        error="ssrf_blocked: max_redirects",
        pinned_addresses=last_pinned,
    )

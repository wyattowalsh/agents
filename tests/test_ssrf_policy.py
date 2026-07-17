"""Pure unit tests for the namespaced source-health SSRF policy (no network)."""

from __future__ import annotations

import importlib
import socket
import sys
from pathlib import Path

import pytest

# Import the namespaced module without installing the MCP workspace member.
_PROJECT = Path(__file__).resolve().parents[1] / "mcp" / "source-url-health"
sys.path.insert(0, str(_PROJECT))
ssrf = importlib.import_module("mcp_source_url_health.ssrf")


@pytest.fixture(autouse=True)
def _forbid_live_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve ordinary hostnames deterministically; individual tests may override."""

    monkeypatch.setattr(
        ssrf.socket,
        "getaddrinfo",
        lambda *_a, **_k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )


class _Resp:
    def __init__(self, status_code: int, *, url: str, location: str | None = None) -> None:
        self.status_code = status_code
        self.url = url
        self.headers = {"location": location} if location else {}
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class _ScriptHttp:
    """Scripted transport: map url -> list of responses consumed in order."""

    def __init__(self, routes: dict[str, list[_Resp]]) -> None:
        self.routes = {k: list(v) for k, v in routes.items()}
        # (method, original_url, follow_redirects, pinned_ip|None)
        self.log: list[tuple[str, str, bool, str | None]] = []

    def _next(self, method: str, url: str, *, follow_redirects: bool, pinned_ip: str | None = None) -> _Resp:
        assert follow_redirects is False
        self.log.append((method, url, follow_redirects, pinned_ip))
        queue = self.routes.get(url)
        if not queue:
            raise ConnectionError(f"no scripted response for {url}")
        return queue.pop(0)

    def head(self, url: str, *, timeout: float, follow_redirects: bool) -> _Resp:
        return self._next("HEAD", url, follow_redirects=follow_redirects)

    def get(self, url: str, *, timeout: float, follow_redirects: bool) -> _Resp:
        return self._next("GET", url, follow_redirects=follow_redirects)

    def request_pinned(
        self,
        method: str,
        url: str,
        *,
        pinned_ip: str,
        timeout: float,
        follow_redirects: bool = False,
    ) -> _Resp:
        # Lookup by original logical URL; record dial peer separately.
        return self._next(method.upper(), url, follow_redirects=follow_redirects, pinned_ip=pinned_ip)


def test_validate_blocks_loopback_literal() -> None:
    err = ssrf.validate_url_for_probe("http://127.0.0.1/admin")
    assert err is not None
    assert "blocked" in err


def test_validate_blocks_metadata_ip() -> None:
    err = ssrf.validate_url_for_probe("https://169.254.169.254/latest/meta-data")
    assert err is not None
    assert "blocked" in err


def test_validate_blocks_file_scheme() -> None:
    err = ssrf.validate_url_for_probe("file:///etc/passwd")
    assert err is not None
    assert "scheme" in err


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("https://user:password@example.com/", "userinfo"),
        ("https://example.com/path#private-fragment", "fragment"),
        ("https://example.com:99999/", "port"),
        ("https://example.com:not-a-port/", "port"),
        ("https://example.com/path\nheader", "control"),
    ],
)
def test_validate_rejects_ambiguous_or_secret_bearing_urls(url: str, message: str) -> None:
    err = ssrf.validate_url_for_probe(url)
    assert err is not None
    assert message in err


@pytest.mark.parametrize(
    ("unicode_host", "ascii_host"),
    [
        ("bücher.example", "xn--bcher-kva.example"),
        ("faß.example", "xn--fa-hia.example"),
        ("ς.example", "xn--3xa.example"),
    ],
)
def test_validate_idna2008_normalizes_before_resolution(
    monkeypatch: pytest.MonkeyPatch,
    unicode_host: str,
    ascii_host: str,
) -> None:
    resolved: list[str] = []

    def _resolve(host: str, *_args: object, **_kwargs: object) -> list[tuple]:
        resolved.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(ssrf.socket, "getaddrinfo", _resolve)
    assert ssrf.validate_url_for_probe(f"https://{unicode_host}/") is None
    assert resolved == [ascii_host]


@pytest.mark.parametrize("hostname", ["foo_bar.example", "-bad.example", "bad-.example"])
def test_validate_idna_enforces_std3_hostname_rules(hostname: str) -> None:
    err = ssrf.validate_url_for_probe(f"https://{hostname}/")
    assert err is not None
    assert "IDNA" in err


@pytest.mark.parametrize(
    ("address", "transition"),
    [
        ("::ffff:8.8.8.8", "IPv4-mapped"),
        ("2002:0808:0808::", "6to4"),
        ("2001:0000:4136:e378:8000:63bf:f7f7:f7f7", "Teredo"),
        ("64:ff9b::808:808", "NAT64 well-known"),
        ("64:ff9b:1::808:808", "NAT64 local-use"),
    ],
)
def test_resolve_blocks_ipv4_transition_addresses(address: str, transition: str) -> None:
    addresses, err = ssrf.resolve_public_addresses(address)
    assert addresses == []
    assert err is not None
    assert transition in err


@pytest.mark.parametrize(
    ("address", "transition"),
    [
        ("::ffff:8.8.8.8", "IPv4-mapped"),
        ("2002:0808:0808::", "6to4"),
        ("2001:0000:4136:e378:8000:63bf:f7f7:f7f7", "Teredo"),
        ("64:ff9b::808:808", "NAT64 well-known"),
        ("64:ff9b:1::808:808", "NAT64 local-use"),
    ],
)
def test_resolve_blocks_dns_answers_using_ipv4_transition_addresses(
    monkeypatch: pytest.MonkeyPatch,
    address: str,
    transition: str,
) -> None:
    monkeypatch.setattr(
        ssrf.socket,
        "getaddrinfo",
        lambda *_a, **_k: [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", (address, 0, 0, 0))],
    )
    addresses, err = ssrf.resolve_public_addresses("example.com")
    assert addresses == []
    assert err is not None
    assert transition in err


@pytest.mark.parametrize(
    "address",
    [
        "::ffff:8.8.8.8",
        "2002:0808:0808::",
        "2001:0000:4136:e378:8000:63bf:f7f7:f7f7",
        "64:ff9b::808:808",
        "64:ff9b:1::808:808",
    ],
)
def test_pinned_connect_rejects_ipv4_transition_addresses(address: str) -> None:
    with pytest.raises(ValueError, match="blocked"):
        ssrf.url_for_pinned_connect("https://example.com/", address)


@pytest.mark.parametrize(
    "address",
    [
        "64:ff9b::7f00:1",  # 127.0.0.1
        "64:ff9b::a00:1",  # 10.0.0.1
        "64:ff9b::a9fe:a9fe",  # 169.254.169.254
        "64:ff9b::c0a8:101",  # 192.168.1.1
    ],
)
def test_validate_blocks_nat64_encodings_of_private_ipv4(address: str) -> None:
    err = ssrf.validate_url_for_probe(f"http://[{address}]/")
    assert err is not None
    assert "NAT64" in err


def test_resolve_blocks_shared_address_space() -> None:
    addresses, err = ssrf.resolve_public_addresses("100.64.0.1")
    assert addresses == []
    assert err is not None
    assert "blocked" in err


def test_resolve_rejects_mixed_public_and_non_global_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ssrf.socket,
        "getaddrinfo",
        lambda *_a, **_k: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.64.0.1", 0)),
        ],
    )
    addresses, err = ssrf.resolve_public_addresses("example.com")
    assert addresses == []
    assert err is not None
    assert "100.64.0.1" in err


def test_check_once_blocks_redirect_to_loopback() -> None:
    public = "https://example.com/start"
    http = _ScriptHttp({
        public: [_Resp(302, url=public, location="http://127.0.0.1/secret")],
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert "ssrf_blocked" in (result["error"] or "")
    assert len(http.log) == 1
    assert http.log[0][0] == "HEAD"
    assert http.log[0][1] == public
    assert not any("127.0.0.1" in entry[1] for entry in http.log)


@pytest.mark.parametrize(
    "location",
    [
        "https://user:password@example.com/next",
        "https://example.com/next#fragment",
        "https://example.com:99999/next",
        "https://[malformed/next",
    ],
)
def test_check_once_revalidates_redirect_url_shape(location: str) -> None:
    public = "https://example.com/start"
    http = _ScriptHttp({public: [_Resp(302, url=public, location=location)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert "ssrf_blocked_redirect" in (result["error"] or "")
    assert len(http.log) == 1


def test_check_once_blocks_redirect_to_link_local_metadata() -> None:
    public = "https://example.com/meta"
    http = _ScriptHttp({
        public: [_Resp(302, url=public, location="http://169.254.169.254/latest/meta-data")],
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert "ssrf_blocked" in (result["error"] or "")
    assert not any("169.254" in entry[1] for entry in http.log)


def test_check_once_blocks_redirect_to_rfc1918() -> None:
    public = "https://example.com/p"
    http = _ScriptHttp({
        public: [_Resp(301, url=public, location="http://10.0.0.5/")],
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert not any("10.0.0.5" in entry[1] for entry in http.log)


def test_check_once_blocks_relative_redirect_to_private() -> None:
    # Relative Location on a host that would resolve via urljoin stays on example.com —
    # use absolute private for relative-style via //127.0.0.1
    public = "https://example.com/rel"
    http = _ScriptHttp({
        public: [_Resp(302, url=public, location="//127.0.0.1/x")],
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert not any("127.0.0.1" in entry[1] for entry in http.log)


def test_check_once_enforces_max_redirects() -> None:
    urls = [f"https://example.com/h{i}" for i in range(7)]
    routes: dict[str, list[_Resp]] = {}
    for i, u in enumerate(urls[:-1]):
        routes[u] = [_Resp(302, url=u, location=urls[i + 1])]
    routes[urls[-1]] = [_Resp(200, url=urls[-1])]
    http = _ScriptHttp(routes)
    result = ssrf.check_once(http, urls[0], 5.0)
    assert result["ok"] is False
    assert "max_redirects" in (result["error"] or "")
    # At most 6 requests (hop0..hop5) before max_redirects on next Location
    assert len(http.log) <= 6


def test_check_once_blocks_https_to_http_downgrade() -> None:
    public = "https://example.com/secure"
    http = _ScriptHttp({
        public: [_Resp(302, url=public, location="http://example.com/insecure")],
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert "scheme_downgrade" in (result["error"] or "")
    assert len(http.log) == 1


def test_check_once_allows_public_to_public_redirect() -> None:
    a = "https://example.com/a"
    b = "https://example.com/b"
    http = _ScriptHttp({
        a: [_Resp(302, url=a, location=b)],
        b: [_Resp(200, url=b)],
    })
    result = ssrf.check_once(http, a, 5.0)
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert [e[0:2] for e in http.log] == [("HEAD", a), ("HEAD", b)]
    assert all(e[3] for e in http.log)  # pinned_ip present on each hop


def test_check_once_detects_redirect_loop() -> None:
    a = "https://example.com/loop-a"
    b = "https://example.com/loop-b"
    http = _ScriptHttp({
        a: [_Resp(302, url=a, location=b), _Resp(302, url=a, location=b)],
        b: [_Resp(302, url=b, location=a), _Resp(302, url=b, location=a)],
    })
    result = ssrf.check_once(http, a, 5.0)
    assert result["ok"] is False
    assert "redirect_loop" in (result["error"] or "") or "max_redirects" in (result["error"] or "")


def test_check_once_revalidates_host_on_each_hop() -> None:
    a = "https://example.com/one"
    b = "http://192.168.1.50/two"
    http = _ScriptHttp({a: [_Resp(302, url=a, location=b)]})
    result = ssrf.check_once(http, a, 5.0)
    assert result["ok"] is False
    assert "ssrf_blocked_redirect" in (result["error"] or "") or "ssrf_blocked" in (result["error"] or "")
    assert not any("192.168" in entry[1] for entry in http.log)


def test_resolve_public_addresses_blocks_private_literal() -> None:
    addrs, err = ssrf.resolve_public_addresses("127.0.0.1")
    assert addrs == []
    assert err is not None
    assert "blocked" in err


def test_resolve_public_addresses_fails_closed_on_dns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_a: object, **_k: object) -> list:
        raise socket.gaierror("simulated dns failure")

    monkeypatch.setattr(ssrf.socket, "getaddrinfo", _boom)
    addrs, err = ssrf.resolve_public_addresses("no-such-host.invalid")
    assert addrs == []
    assert err is not None
    assert "dns_resolution_failed" in err


def test_check_once_pins_public_addresses_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ssrf,
        "resolve_public_addresses",
        lambda _host: (["93.184.216.34"], None),
    )
    public = "https://example.com/ok"
    http = _ScriptHttp({public: [_Resp(200, url=public)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is True
    assert result.get("pinned_addresses") == ["93.184.216.34"]


def test_check_once_dials_pinned_ip_not_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ssrf,
        "resolve_public_addresses",
        lambda _host: (["93.184.216.34"], None),
    )
    public = "https://example.com/ok"
    http = _ScriptHttp({public: [_Resp(200, url=public)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is True
    assert http.log[0][3] == "93.184.216.34"
    # Logical URL remains hostname; peer pin is separate.
    assert http.log[0][1] == public
    assert "93.184.216.34" not in http.log[0][1]


def test_head_503_does_not_issue_get(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ssrf, "resolve_public_addresses", lambda _h: (["1.2.3.4"], None))
    public = "https://example.com/busy"
    http = _ScriptHttp({public: [_Resp(503, url=public)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert result["status_code"] == 503
    assert [e[0] for e in http.log] == ["HEAD"]


def test_head_405_issues_get(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ssrf, "resolve_public_addresses", lambda _h: (["1.2.3.4"], None))
    public = "https://example.com/method"
    http = _ScriptHttp({
        public: [
            _Resp(405, url=public),
            _Resp(200, url=public),
        ]
    })
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is True
    assert [e[0] for e in http.log] == ["HEAD", "GET"]
    assert all(e[3] == "1.2.3.4" for e in http.log)
    responses = http.routes[public]
    assert responses == []


def test_check_once_closes_head_and_get_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ssrf, "resolve_public_addresses", lambda _h: (["1.2.3.4"], None))
    public = "https://example.com/method"
    head = _Resp(405, url=public)
    get = _Resp(200, url=public)
    http = _ScriptHttp({public: [head, get]})

    result = ssrf.check_once(http, public, 5.0)

    assert result["ok"] is True
    assert head.close_calls == 1
    assert get.close_calls == 1


def test_check_once_shares_total_timeout_across_pin_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(ssrf.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        ssrf,
        "resolve_public_addresses",
        lambda _h: (["1.1.1.1", "2.2.2.2"], None),
    )
    public = "https://example.com/deadline"

    class _Timed(_ScriptHttp):
        def __init__(self) -> None:
            super().__init__({public: [_Resp(200, url=public)]})
            self.timeouts: list[float] = []

        def request_pinned(
            self,
            method: str,
            url: str,
            *,
            pinned_ip: str,
            timeout: float,
            follow_redirects: bool = False,
        ) -> _Resp:
            self.timeouts.append(timeout)
            if pinned_ip == "1.1.1.1":
                clock[0] += 4.0
                raise ConnectionError("first pin unavailable")
            return super().request_pinned(
                method,
                url,
                pinned_ip=pinned_ip,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )

    http = _Timed()
    result = ssrf.check_once(http, public, 5.0)

    assert result["ok"] is True
    assert http.timeouts[0] == pytest.approx(5.0)
    assert http.timeouts[1] == pytest.approx(1.0)


def test_check_once_fails_if_resolution_exhausts_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [10.0]
    monkeypatch.setattr(ssrf.time, "monotonic", lambda: clock[0])

    def _resolve(_host: str) -> tuple[list[str], None]:
        clock[0] += 6.0
        return ["93.184.216.34"], None

    monkeypatch.setattr(ssrf, "resolve_public_addresses", _resolve)
    public = "https://example.com/slow-dns"
    http = _ScriptHttp({public: [_Resp(200, url=public)]})

    result = ssrf.check_once(http, public, 5.0)

    assert result["ok"] is False
    assert "total timeout exceeded" in (result["error"] or "")
    assert http.log == []


def test_check_once_retries_next_pin_on_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ssrf,
        "resolve_public_addresses",
        lambda _h: (["1.1.1.1", "2.2.2.2"], None),
    )
    public = "https://example.com/retry"

    class _Flaky(_ScriptHttp):
        def request_pinned(
            self,
            method: str,
            url: str,
            *,
            pinned_ip: str,
            timeout: float,
            follow_redirects: bool = False,
        ) -> _Resp:
            if pinned_ip == "1.1.1.1":
                self.log.append((method.upper(), url, follow_redirects, pinned_ip))
                raise ConnectionError("simulated connect failure")
            return super().request_pinned(
                method, url, pinned_ip=pinned_ip, timeout=timeout, follow_redirects=follow_redirects
            )

    http = _Flaky({public: [_Resp(200, url=public)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is True
    pins = [e[3] for e in http.log]
    assert pins[0] == "1.1.1.1"
    assert pins[-1] == "2.2.2.2"


def test_check_once_does_not_retry_on_http_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ssrf,
        "resolve_public_addresses",
        lambda _h: (["1.1.1.1", "2.2.2.2"], None),
    )
    public = "https://example.com/no-retry"
    http = _ScriptHttp({public: [_Resp(503, url=public)]})
    result = ssrf.check_once(http, public, 5.0)
    assert result["ok"] is False
    assert result["status_code"] == 503
    assert [e[3] for e in http.log] == ["1.1.1.1"]

# Source URL health hardening

## ADDED Requirements

### Requirement: Supported isolated transport

The source URL health MCP SHALL use supported HTTPX client APIs, verify TLS,
ignore proxy and certificate environment variables, disable automatic
redirects, preserve logical Host/SNI identity for pinned connections, and close
every response.

#### Scenario: Real client call contract

- **WHEN** the MCP issues a health request through the installed HTTPX version
- **THEN** no unsupported request keyword is passed
- **AND** client-level TLS and environment policy remains active

### Requirement: Revalidated bounded destinations

The MCP SHALL reject malformed or credential-bearing URLs, every non-global
resolved address, and every redirect hop that fails the same policy. The caller
timeout SHALL be tracked as one monotonic best-effort budget rather than reset
for each attempt: every network phase receives only the remaining budget and no
new attempt starts after expiry. The contract SHALL disclose that a synchronous
system resolver call cannot be preempted and can therefore overrun wall-clock
budget.

#### Scenario: Redirect to a blocked address

- **GIVEN** an allowed initial hostname redirects to a loopback, private, link-local, reserved, multicast, or otherwise non-global address
- **WHEN** the redirect is evaluated
- **THEN** no request is issued to that address

### Requirement: Self-contained distribution

The built wheel SHALL contain every first-party module needed to import and run
the MCP without importing the root `wagents` workspace package.

#### Scenario: Isolated wheel import

- **GIVEN** the wheel is installed outside the repository workspace
- **WHEN** the namespaced source URL health server and SSRF policy modules are imported
- **THEN** both imports succeed without a root-workspace dependency

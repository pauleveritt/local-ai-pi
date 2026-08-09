# Include locally registered services in health pings

`Container.get_pings()` reports only services registered on the registry. A
service registered directly on a container — a local registration — is invisible
to it, even when that service declares a ping.

Make `get_pings()` report the pings of every service the container would
actually resolve:

- a locally registered service that declares a ping is reported;
- where a local registration shadows a registry registration for the same type,
  the local ping is the one reported, not the registry's;
- a local registration that declares *no* ping means no ping is reported for
  that type at all — the shadowed registry registration's ping is not used as a
  fallback.

Behaviour for types that have only a registry registration, and for services
that declare no ping anywhere, must not change.

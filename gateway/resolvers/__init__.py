"""Resolver registry per domain."""
from ..resolver import Resolver, ResolverError


def for_domain(domain: str) -> dict[str, Resolver]:
    if domain == "bank":
        from .bank import RESOLVERS
    elif domain == "hospital":
        from .hospital import RESOLVERS
    elif domain == "shop":
        from .shop import RESOLVERS
    else:
        raise ResolverError(f"unknown domain {domain}")
    return RESOLVERS


def get(domain: str, action: str) -> Resolver:
    r = for_domain(domain).get(action)
    if r is None:
        raise ResolverError(f"no resolver for action {action!r}")
    return r

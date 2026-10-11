"""Registry: who may do what. Default deny for unknown agents, actions and destinations."""
from .policy_loader import Policy, load_users


def knows(policy: Policy, agent: str, action: str) -> bool:
    a = policy.agents.get(agent)
    return bool(a) and action in a.get("actions", []) and action in policy.model.actions


def destination_allowed(policy: Policy, dest: str) -> bool:
    return dest in policy.destinations


def human_role(policy: Policy, human: str) -> str | None:
    u = load_users().get(human)
    return u["roles"].get(policy.domain) if u else None


def resolve_human(policy: Policy, agent: str, on_behalf_of: str) -> str:
    if on_behalf_of:
        return on_behalf_of
    return policy.agents.get(agent, {}).get("default_user", "")


def effective_permissions(policy: Policy, agent: str, human: str) -> set[str]:
    """Agent permissions intersected with the human it acts for (confused-deputy protection)."""
    agent_actions = set(policy.agents.get(agent, {}).get("actions", []))
    role = human_role(policy, human)
    role_actions = set(policy.model.roles.get(role, [])) if role else set()
    return agent_actions & role_actions

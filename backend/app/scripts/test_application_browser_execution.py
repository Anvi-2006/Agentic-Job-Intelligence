from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)
from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession


def main() -> None:
    manager = BrowserManager(
        headless=True,
    )

    try:
        session = BrowserSession(manager)
        agent = ApplicationBrowserAgent(session)

        blocked_plan = {
            "url": "https://example.com/apply",
            "title": "Example Application",
            "form_count": 1,
            "field_count": 2,
            "human_intervention_required": True,
            "actions": [
                {
                    "action": "fill",
                    "selector": "#full-name",
                    "field_type": "full_name",
                    "source": "candidate.full_name",
                    "value": "Anvi",
                    "reason": None,
                },
                {
                    "action": "needs_human",
                    "selector": "#phone",
                    "field_type": "unknown",
                    "source": None,
                    "value": None,
                    "reason": (
                        "Phone number is required."
                    ),
                },
            ],
        }

        result = agent.execute_plan(
            blocked_plan
        )

        print(result)

        assert result["status"] == "needs_human"

        assert (
            result["executed_actions"]
            == []
        )

        assert len(
            result["blocked_actions"]
        ) == 1

        print(
            "Browser execution safety gate: PASS"
        )

    finally:
        manager.close()


if __name__ == "__main__":
    main()
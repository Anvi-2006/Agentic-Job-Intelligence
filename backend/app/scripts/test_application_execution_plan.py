from uuid import UUID

from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)
from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession
from backend.app.core.database import SessionLocal
from backend.app.services.application_data_service import (
    build_application_data,
)


APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


def main() -> None:
    db = SessionLocal()
    manager = BrowserManager(headless=True)

    try:
        application_data = build_application_data(
            db=db,
            application_id=APPLICATION_ID,
        )

        session = BrowserSession(manager)
        agent = ApplicationBrowserAgent(session)

        page_data = {
            "url": "https://example.com/apply",
            "title": "Example Application",
            "form_count": 1,
            "field_count": 5,
            "fields": [
                {
                    "selector": "#full-name",
                    "input_type": "text",
                    "name": "full_name",
                    "placeholder": "Full name",
                    "required": True,
                },
                {
                    "selector": "#email",
                    "input_type": "email",
                    "name": "email",
                    "placeholder": "Email",
                    "required": True,
                },
                {
                    "selector": "#resume",
                    "input_type": "file",
                    "name": "resume",
                    "placeholder": None,
                    "required": True,
                },
                {
                    "selector": "#cover-letter",
                    "input_type": "textarea",
                    "name": "cover_letter",
                    "placeholder": "Cover letter",
                    "required": False,
                },
                {
                    "selector": "#phone",
                    "input_type": "tel",
                    "name": "phone",
                    "placeholder": "Phone number",
                    "required": True,
                },
            ],
        }

        plan = agent.build_execution_plan(
            page_data=page_data,
            application_data=application_data,
        )

        for action in plan["actions"]:
            print(action)

        assert plan["human_intervention_required"] is True

        assert plan["actions"][0]["action"] == "fill"
        assert plan["actions"][0]["field_type"] == "full_name"

        assert plan["actions"][1]["action"] == "fill"
        assert plan["actions"][1]["field_type"] == "email"

        assert plan["actions"][2]["action"] == "upload"
        assert plan["actions"][2]["field_type"] == "resume"

        assert plan["actions"][3]["action"] == "fill"
        assert plan["actions"][3]["field_type"] == "cover_letter"

        assert plan["actions"][4]["action"] == "needs_human"
        assert plan["actions"][4]["field_type"] == "unknown"

        print(
            "Application execution plan test: PASS"
        )

    finally:
        manager.close()
        db.close()


if __name__ == "__main__":
    main()
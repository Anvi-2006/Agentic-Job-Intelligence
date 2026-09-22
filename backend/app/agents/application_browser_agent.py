from dataclasses import dataclass

from playwright.sync_api import Locator

from backend.app.browser.browser_session import BrowserSession
from backend.app.services.application_field_mapping_service import (
    map_application_fields,
)


@dataclass
class BrowserInput:
    selector: str
    input_type: str
    name: str | None
    placeholder: str | None
    required: bool


class ApplicationBrowserAgent:
    """
    Browser agent responsible for understanding and interacting
    with an application page.

    Browser lifecycle remains owned by BrowserManager.
    Browser interaction remains owned by BrowserSession.
    """

    def __init__(
        self,
        session: BrowserSession,
    ) -> None:
        self.session = session

    def open_application_page(
        self,
        url: str,
    ) -> dict:
        self.session.open_url(url)

        return self.inspect_page()

    def inspect_page(self) -> dict:
        page = self.session.page

        inputs = page.locator(
            "input, textarea, select"
        )

        fields: list[dict] = []

        for index in range(inputs.count()):
            element = inputs.nth(index)

            fields.append(
                self._inspect_input(
                    element,
                    index,
                )
            )

        forms = page.locator("form")

        return {
            "url": self.session.get_current_url(),
            "title": self.session.get_page_title(),
            "form_count": forms.count(),
            "field_count": len(fields),
            "fields": fields,
        }

    def build_execution_plan(
        self,
        page_data: dict,
        application_data: dict,
    ) -> dict:
        """
        Build a deterministic execution plan from the inspected
        application page and trusted ApplyIQ application data.

        This method does not interact with the browser.
        It only decides what can be safely automated and what
        requires human intervention.
        """

        fields = page_data.get(
            "fields",
            [],
        )

        mappings = map_application_fields(
            fields=fields,
            application_data=application_data,
        )

        actions: list[dict] = []
        human_intervention_required = False

        for mapping in mappings:
            if mapping["requires_human"]:
                human_intervention_required = True

                actions.append(
                    {
                        "action": "needs_human",
                        "selector": mapping["selector"],
                        "field_type": mapping["field_type"],
                        "source": mapping["source"],
                        "value": None,
                        "reason": mapping["reason"],
                    }
                )

                continue

            field_type = mapping["field_type"]

            if field_type == "resume":
                actions.append(
                    {
                        "action": "upload",
                        "selector": mapping["selector"],
                        "field_type": field_type,
                        "source": mapping["source"],
                        "value": mapping["value"],
                        "reason": None,
                    }
                )

                continue

            if field_type in {
                "full_name",
                "email",
                "cover_letter",
                "summary",
		"human_input",
            }:
                actions.append(
                    {
                        "action": "fill",
                        "selector": mapping["selector"],
                        "field_type": field_type,
                        "source": mapping["source"],
                        "value": mapping["value"],
                        "reason": None,
                    }
                )

                continue

            actions.append(
                {
                    "action": "skip",
                    "selector": mapping["selector"],
                    "field_type": field_type,
                    "source": mapping["source"],
                    "value": mapping["value"],
                    "reason": mapping["reason"],
                }
            )

        return {
            "url": page_data.get("url"),
            "title": page_data.get("title"),
            "form_count": page_data.get(
                "form_count",
                0,
            ),
            "field_count": page_data.get(
                "field_count",
                0,
            ),
            "actions": actions,
            "human_intervention_required": (
                human_intervention_required
            ),
        }

    def execute_fill(
        self,
        selector: str,
        value: str,
    ) -> dict:
        """
            Safely fill one browser field.

            This method performs only a field fill. It does not
            submit the application.
        """

        if not selector.strip():
                raise ValueError(
                    "Browser field selector cannot be empty."
                )

        if value is None:
                raise ValueError(
                    "Browser field value cannot be None."
                )

        self.session.fill_field(
                selector=selector,
                value=value,
            )

        return {
                "action": "fill",
                "selector": selector,
                "success": True,
            }

    def execute_upload(
        self,
        selector: str,
        file_path: str,
    ) -> dict:
        """
        Safely upload a file to one browser field.

        This method performs only the file upload. It does not
        submit the application.
        """

        if not selector.strip():
            raise ValueError(
                "Browser upload selector cannot be empty."
            )

        if not file_path.strip():
            raise ValueError(
                "Browser upload file path cannot be empty."
            )

        self.session.page.locator(
            selector
        ).set_input_files(
            file_path
        )

        return {
            "action": "upload",
            "selector": selector,
            "success": True,
        }

    def execute_plan(
        self,
        plan: dict,
    ) -> dict:
        """
        Execute safe actions from an application plan.

        Required human intervention blocks execution before
        any browser action is performed.
        """

        if plan.get(
            "human_intervention_required",
            False,
        ):
            return {
                "status": "needs_human",
                "executed_actions": [],
                "blocked_actions": [
                    action
                    for action in plan.get(
                        "actions",
                        [],
                    )
                    if action.get("action")
                    == "needs_human"
                ],
                "message": (
                    "Execution paused because "
                    "human intervention is required."
                ),
            }

        executed_actions: list[dict] = []

        for action in plan.get(
            "actions",
            [],
        ):
            action_type = action.get(
                "action"
            )

            if action_type == "fill":
                result = self.execute_fill(
                    selector=action["selector"],
                    value=action["value"],
                )

                executed_actions.append(
                    result
                )

            elif action_type == "upload":
                result = self.execute_upload(
                    selector=action["selector"],
                    file_path=action["value"],
                )

                executed_actions.append(
                    result
                )

            elif action_type == "skip":
                continue

            elif action_type == "needs_human":
                return {
                    "status": "needs_human",
                    "executed_actions": (
                        executed_actions
                    ),
                    "blocked_actions": [action],
                    "message": (
                        "Execution paused because "
                        "human intervention is required."
                    ),
                }

            else:
                raise ValueError(
                    f"Unsupported browser action: "
                    f"{action_type}"
                )

        return {
            "status": "executed",
            "executed_actions": executed_actions,
            "blocked_actions": [],
            "message": (
                "Application fields executed successfully."
            ),
        }

    def detect_application_form(self) -> bool:
        page = self.session.page

        forms = page.locator("form")

        if forms.count() > 0:
            return True

        application_keywords = [
            "apply",
            "application",
            "resume",
            "cover letter",
            "candidate",
            "job application",
        ]

        page_text = (
            page.locator("body")
            .inner_text()
            .lower()
        )

        return any(
            keyword in page_text
            for keyword in application_keywords
        )

    def _inspect_input(
        self,
        element: Locator,
        index: int,
    ) -> dict:
        tag_name = element.evaluate(
            "(element) => element.tagName.toLowerCase()"
        )

        input_type = (
            element.get_attribute("type")
            or tag_name
        )

        name = element.get_attribute("name")

        placeholder = element.get_attribute(
            "placeholder"
        )

        required = (
            element.get_attribute("required")
            is not None
        )

        selector = self._build_selector(
            element,
            index,
        )

        return {
            "selector": selector,
            "input_type": input_type,
            "name": name,
            "placeholder": placeholder,
            "required": required,
        }

    def _build_selector(
        self,
        element: Locator,
        index: int,
    ) -> str:
        element_id = element.get_attribute("id")

        if element_id:
            return f"#{element_id}"

        name = element.get_attribute("name")

        if name:
            tag_name = element.evaluate(
                "(element) => element.tagName.toLowerCase()"
            )

            return (
                f'{tag_name}[name="{name}"]'
            )

        return (
            f"input, textarea, select >> nth={index}"
        )
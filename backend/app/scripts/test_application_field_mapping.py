from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.services.application_data_service import (
    build_application_data,
)
from backend.app.services.application_field_mapping_service import (
    map_application_fields,
)


APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


def main() -> None:
    db = SessionLocal()

    try:
        application_data = build_application_data(
            db=db,
            application_id=APPLICATION_ID,
        )

        fields = [
            {
                "selector": "#full-name",
                "input_type": "text",
                "name": "full_name",
                "placeholder": "Enter your full name",
                "required": True,
            },
            {
                "selector": "#email",
                "input_type": "email",
                "name": "email",
                "placeholder": "Enter your email",
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
                "placeholder": "Enter cover letter",
                "required": False,
            },
            {
                "selector": "#phone",
                "input_type": "tel",
                "name": "phone",
                "placeholder": "Phone number",
                "required": True,
            },
        ]

        mappings = map_application_fields(
            fields=fields,
            application_data=application_data,
        )

        for mapping in mappings:
            print(mapping)

        assert mappings[0]["field_type"] == "full_name"
        assert mappings[0]["source"] == "candidate.full_name"
        assert mappings[0]["requires_human"] is False
        assert mappings[0]["value"] == "Anvi"

        assert mappings[1]["field_type"] == "email"
        assert mappings[1]["source"] == "candidate.email"
        assert mappings[1]["requires_human"] is False
        assert mappings[1]["value"] == "anvi@example.com"

        assert mappings[2]["field_type"] == "resume"
        assert mappings[2]["source"] == "resume.file_path"
        assert mappings[2]["requires_human"] is False

        assert mappings[3]["field_type"] == "cover_letter"
        assert mappings[3]["source"] == (
            "application_package.cover_letter"
        )
        assert mappings[3]["requires_human"] is False

        assert mappings[4]["field_type"] == "unknown"
        assert mappings[4]["requires_human"] is True
        assert mappings[4]["value"] is None

        print("ApplicationFieldMapping test: PASS")

    finally:
        db.close()


if __name__ == "__main__":
    main()
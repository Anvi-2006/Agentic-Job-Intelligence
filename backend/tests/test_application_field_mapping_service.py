from backend.app.services.application_field_mapping_service import (
    map_application_fields,
)


def test_maps_email_field_from_candidate_data():
    fields = [
        {
            "selector": "#email",
            "input_type": "email",
            "name": "email",
            "placeholder": "Email address",
            "required": True,
        }
    ]

    application_data = {
        "candidate": {
            "email": "anvi@example.com",
        }
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings == [
        {
            "selector": "#email",
            "field_type": "email",
            "source": "candidate.email",
            "value": "anvi@example.com",
            "requires_human": False,
            "reason": None,
        }
    ]
    
def test_required_email_without_value_requires_human():
    fields = [
        {
            "selector": "#email",
            "input_type": "email",
            "name": "email",
            "placeholder": "Email address",
            "required": True,
        }
    ]

    application_data = {
        "candidate": {}
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings[0]["field_type"] == "email"
    assert mappings[0]["source"] == "candidate.email"
    assert mappings[0]["value"] is None
    assert mappings[0]["requires_human"] is True
    assert mappings[0]["reason"] == (
        "Required email information is not available."
    )

def test_unknown_required_field_requires_human():
    fields = [
        {
            "selector": "#work_authorization",
            "input_type": "text",
            "name": "work_authorization",
            "placeholder": "Work authorization",
            "required": True,
        }
    ]

    application_data = {
        "candidate": {
            "email": "anvi@example.com",
        }
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings[0]["field_type"] == "unknown"
    assert mappings[0]["source"] is None
    assert mappings[0]["value"] is None
    assert mappings[0]["requires_human"] is True
    assert mappings[0]["reason"] == (
        "Application field could not be matched "
        "to trusted ApplyIQ data."
    )

def test_maps_resume_file_field_from_resume_data():
    fields = [
        {
            "selector": "#resume",
            "input_type": "file",
            "name": "resume",
            "placeholder": None,
            "required": True,
        }
    ]

    application_data = {
        "resume": {
            "file_path": r"C:\resumes\anvi_resume.pdf",
        }
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings[0]["field_type"] == "resume"
    assert mappings[0]["source"] == "resume.file_path"
    assert mappings[0]["value"] == r"C:\resumes\anvi_resume.pdf"
    assert mappings[0]["requires_human"] is False
    assert mappings[0]["reason"] is None
    
def test_maps_answered_human_input():
    fields = [
        {
            "selector": "#linkedin",
            "input_type": "text",
            "name": "linkedin",
            "placeholder": "LinkedIn profile URL",
            "required": True,
        }
    ]

    application_data = {
        "human_inputs": {
            "linkedin": "https://linkedin.com/in/anvi"
        }
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings[0]["field_type"] == "human_input"
    assert mappings[0]["source"] == "human_input.linkedin"
    assert mappings[0]["value"] == "https://linkedin.com/in/anvi"
    assert mappings[0]["requires_human"] is False
    assert mappings[0]["reason"] is None
    
    
def test_unknown_optional_field_does_not_require_human():
    fields = [
        {
            "selector": "#portfolio",
            "input_type": "text",
            "name": "portfolio",
            "placeholder": "Portfolio URL",
            "required": False,
        }
    ]

    application_data = {
        "candidate": {
            "email": "anvi@example.com",
        }
    }

    mappings = map_application_fields(
        fields=fields,
        application_data=application_data,
    )

    assert mappings[0]["field_type"] == "unknown"
    assert mappings[0]["source"] is None
    assert mappings[0]["value"] is None
    assert mappings[0]["requires_human"] is False
    assert mappings[0]["reason"] is None
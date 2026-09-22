from dataclasses import dataclass


@dataclass
class FieldMapping:
    selector: str
    field_type: str
    source: str | None
    value: str | None
    requires_human: bool
    reason: str | None = None


def map_application_fields(
    fields: list[dict],
    application_data: dict,
) -> list[dict]:
    """
    Map inspected browser fields to trusted ApplyIQ data.

    Unknown or unavailable required fields are explicitly marked
    for human intervention. No candidate information is invented.
    """

    mappings: list[FieldMapping] = []

    for field in fields:
        mapping = _map_field(
            field=field,
            application_data=application_data,
        )

        mappings.append(mapping)

    return [
        {
            "selector": mapping.selector,
            "field_type": mapping.field_type,
            "source": mapping.source,
            "value": mapping.value,
            "requires_human": mapping.requires_human,
            "reason": mapping.reason,
        }
        for mapping in mappings
    ]


def _map_field(
    field: dict,
    application_data: dict,
) -> FieldMapping:
    selector = field["selector"]

    input_type = (
        field.get("input_type")
        or ""
    ).lower()

    name = (
        field.get("name")
        or ""
    ).lower()

    placeholder = (
        field.get("placeholder")
        or ""
    ).lower()

    search_text = " ".join(
        [
            input_type,
            name,
            placeholder,
        ]
    )

    candidate = application_data.get(
        "candidate",
        {},
    )

    resume = application_data.get(
        "resume",
        {},
    )

    package = application_data.get(
        "application_package",
        {},
    )
    
    human_inputs = application_data.get(
    	"human_inputs",
    	{},
    )

    if input_type == "file":
        resume_path = resume.get("file_path")

        if resume_path:
            return FieldMapping(
                selector=selector,
                field_type="resume",
                source="resume.file_path",
                value=resume_path,
                requires_human=False,
            )

        return FieldMapping(
            selector=selector,
            field_type="resume",
            source=None,
            value=None,
            requires_human=True,
            reason="Resume file is not available.",
        )

    if _contains_any(
        search_text,
        [
            "email",
            "e-mail",
        ],
    ):
        return _text_mapping(
            selector=selector,
            field_type="email",
            source="candidate.email",
            value=candidate.get("email"),
        )

    if _contains_any(
        search_text,
        [
            "full name",
            "fullname",
            "candidate name",
            "your name",
            "name",
        ],
    ):
        return _text_mapping(
            selector=selector,
            field_type="full_name",
            source="candidate.full_name",
            value=candidate.get("full_name"),
        )

    if _contains_any(
        search_text,
        [
            "cover letter",
            "cover_letter",
            "coverletter",
        ],
    ):
        return _text_mapping(
            selector=selector,
            field_type="cover_letter",
            source="application_package.cover_letter",
            value=package.get("cover_letter"),
        )

    if _contains_any(
        search_text,
        [
            "summary",
            "professional summary",
            "about yourself",
            "about you",
        ],
    ):
        value = (
            package.get("tailored_summary")
            or candidate.get("summary")
        )

        source = (
            "application_package.tailored_summary"
            if package.get("tailored_summary")
            else "candidate.summary"
        )

        return _text_mapping(
            selector=selector,
            field_type="summary",
            source=source,
            value=value,
        )

    human_input_keys = [
    	field.get("name"),
    	field.get("placeholder"),
    	selector,
    ]

    for human_input_key in human_input_keys:
    	if not human_input_key:
        	continue

    	answer = human_inputs.get(
        	human_input_key
        )

    	if answer is not None and str(answer).strip():
        	return FieldMapping(
            	    selector=selector,
            	    field_type="human_input",
            	    source=(
               		 f"human_input.{human_input_key}"
            	    ),
            	    value=str(answer),
            	    requires_human=False,
            	    reason=None,
        	)

    return FieldMapping(
    	selector=selector,
    	field_type="unknown",
    	source=None,
    	value=None,
    	requires_human=bool(
        	field.get("required", False)
    	),
    	reason=(
       		"Application field could not be "
       		"matched to trusted ApplyIQ data."
        	if field.get("required", False)
        	else None
    	),
    )


def _text_mapping(
    selector: str,
    field_type: str,
    source: str,
    value: str | None,
) -> FieldMapping:
    if value is None or not str(value).strip():
        return FieldMapping(
            selector=selector,
            field_type=field_type,
            source=source,
            value=None,
            requires_human=True,
            reason=(
                f"Required {field_type.replace('_', ' ')} "
                "information is not available."
            ),
        )

    return FieldMapping(
        selector=selector,
        field_type=field_type,
        source=source,
        value=str(value),
        requires_human=False,
    )


def _contains_any(
    text: str,
    keywords: list[str],
) -> bool:
    return any(
        keyword in text
        for keyword in keywords
    )
"""Safe deterministic form rule grammar and evaluation tests."""

import pytest

from app.services.form_rules import FormRuleEvaluator, InvalidFormRuleError


def test_visibility_and_conditional_requirement_use_context_paths() -> None:
    result = FormRuleEvaluator().evaluate_field(
        is_required=False,
        is_read_only=False,
        visibility_rule={
            "version": 1,
            "condition": {
                "all": [
                    {"path": "current.risk", "operator": "eq", "value": "HIGH"},
                    {"path": "user.roles", "operator": "in", "value": ["ANALYST"]},
                ]
            },
        },
        validation_rule={
            "version": 1,
            "required_when": {"not": {"path": "current.mitigation", "operator": "exists"}},
        },
        inheritance_rule={},
        context={
            "current": {"risk": "HIGH"},
            "user": {"roles": "ANALYST"},
        },
    )

    assert result.visible is True
    assert result.required is True
    assert result.read_only is False


def test_parent_inheritance_supports_read_only_and_editable_defaults() -> None:
    evaluator = FormRuleEvaluator()
    read_only = evaluator.evaluate_field(
        is_required=False,
        is_read_only=False,
        visibility_rule={},
        validation_rule={},
        inheritance_rule={
            "version": 1,
            "source_path": "parent.name",
            "mode": "READ_ONLY",
        },
        context={"parent": {"name": "Parent Service"}},
    )
    editable = evaluator.evaluate_field(
        is_required=False,
        is_read_only=False,
        visibility_rule={},
        validation_rule={},
        inheritance_rule={
            "version": 1,
            "static_value": "Draft",
            "mode": "EDITABLE_DEFAULT",
        },
        context={},
    )

    assert read_only.has_inherited_value is True
    assert read_only.inherited_value == "Parent Service"
    assert read_only.read_only is True
    assert editable.inherited_value == "Draft"
    assert editable.read_only is False


@pytest.mark.parametrize(
    "visibility_rule",
    [
        {"version": 1, "condition": {"path": "__class__", "operator": "exists"}},
        {
            "version": 1,
            "condition": {
                "path": "current.risk",
                "operator": "python_eval",
                "value": "danger",
            },
        },
        {"version": 2, "condition": {"path": "current.risk", "operator": "exists"}},
    ],
)
def test_unsafe_or_unknown_rule_constructs_are_rejected(
    visibility_rule: dict[str, object],
) -> None:
    with pytest.raises(InvalidFormRuleError):
        FormRuleEvaluator().validate_rules(
            visibility_rule=visibility_rule,
            validation_rule={},
            inheritance_rule={},
        )


def test_rule_depth_and_clause_counts_are_bounded() -> None:
    nested: dict[str, object] = {
        "path": "current.risk",
        "operator": "exists",
    }
    for _ in range(12):
        nested = {"not": nested}
    with pytest.raises(InvalidFormRuleError):
        FormRuleEvaluator().validate_rules(
            visibility_rule={"version": 1, "condition": nested},
            validation_rule={},
            inheritance_rule={},
        )

    clauses = [{"path": "current.risk", "operator": "exists"} for _ in range(101)]
    with pytest.raises(InvalidFormRuleError):
        FormRuleEvaluator().validate_rules(
            visibility_rule={"version": 1, "condition": {"all": clauses}},
            validation_rule={},
            inheritance_rule={},
        )

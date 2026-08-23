"""Bounded, deterministic JSON rule validation and evaluation for dynamic forms."""

import re
from dataclasses import dataclass

type RuleMapping = dict[str, object]

_PATH_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_COMPARISON_OPERATORS = frozenset({"eq", "neq", "in", "not_in", "exists", "gt", "gte", "lt", "lte"})
_MAX_DEPTH = 10
_MAX_CLAUSES = 100


class InvalidFormRuleError(ValueError):
    """A stored form rule is outside the safe versioned JSON grammar."""


@dataclass(frozen=True)
class FieldRuleResult:
    visible: bool
    required: bool
    read_only: bool
    inherited_value: object | None
    has_inherited_value: bool


class FormRuleEvaluator:
    """Validate and evaluate a small JSON AST without code execution."""

    def validate_rules(
        self,
        *,
        visibility_rule: RuleMapping,
        validation_rule: RuleMapping,
        inheritance_rule: RuleMapping,
    ) -> None:
        self._validate_conditional_rule(visibility_rule, "condition")
        self._validate_conditional_rule(validation_rule, "required_when")
        self._validate_inheritance_rule(inheritance_rule)

    def evaluate_field(
        self,
        *,
        is_required: bool,
        is_read_only: bool,
        visibility_rule: RuleMapping,
        validation_rule: RuleMapping,
        inheritance_rule: RuleMapping,
        context: RuleMapping,
    ) -> FieldRuleResult:
        self.validate_rules(
            visibility_rule=visibility_rule,
            validation_rule=validation_rule,
            inheritance_rule=inheritance_rule,
        )
        visible = (
            True
            if not visibility_rule
            else self._evaluate_expression(visibility_rule["condition"], context)
        )
        required = is_required or (
            bool(validation_rule)
            and self._evaluate_expression(validation_rule["required_when"], context)
        )
        inherited_value: object | None = None
        has_inherited_value = False
        inherited_read_only = False
        if inheritance_rule:
            if "source_path" in inheritance_rule:
                has_inherited_value, inherited_value = self._resolve_path(
                    context, str(inheritance_rule["source_path"])
                )
            else:
                has_inherited_value = True
                inherited_value = inheritance_rule.get("static_value")
            inherited_read_only = has_inherited_value and inheritance_rule["mode"] == "READ_ONLY"
        return FieldRuleResult(
            visible=visible,
            required=required,
            read_only=is_read_only or inherited_read_only,
            inherited_value=inherited_value,
            has_inherited_value=has_inherited_value,
        )

    def _validate_conditional_rule(self, rule: RuleMapping, condition_key: str) -> None:
        if not rule:
            return
        if set(rule) != {"version", condition_key} or rule.get("version") != 1:
            raise InvalidFormRuleError("Conditional rule must use the version 1 grammar.")
        counter = [0]
        self._validate_expression(rule[condition_key], depth=0, counter=counter)

    def _validate_expression(self, expression: object, *, depth: int, counter: list[int]) -> None:
        if depth > _MAX_DEPTH:
            raise InvalidFormRuleError("Rule nesting exceeds the supported limit.")
        counter[0] += 1
        if counter[0] > _MAX_CLAUSES:
            raise InvalidFormRuleError("Rule clause count exceeds the supported limit.")
        if not isinstance(expression, dict):
            raise InvalidFormRuleError("Rule expression must be an object.")
        keys = set(expression)
        composite = keys.intersection({"all", "any", "not"})
        if composite:
            if len(composite) != 1 or len(keys) != 1:
                raise InvalidFormRuleError("Composite expressions accept exactly one operator.")
            operator = next(iter(composite))
            children = expression[operator]
            if operator == "not":
                self._validate_expression(children, depth=depth + 1, counter=counter)
                return
            if not isinstance(children, list) or not children:
                raise InvalidFormRuleError("all/any requires a non-empty expression list.")
            for child in children:
                self._validate_expression(child, depth=depth + 1, counter=counter)
            return
        allowed = {"path", "operator", "value"}
        if not keys.issubset(allowed) or not {"path", "operator"}.issubset(keys):
            raise InvalidFormRuleError("Comparison expression has unsupported fields.")
        path = expression["path"]
        operator = expression["operator"]
        if not isinstance(path, str) or len(path) > 255 or _PATH_PATTERN.fullmatch(path) is None:
            raise InvalidFormRuleError("Rule path is invalid.")
        if not isinstance(operator, str) or operator not in _COMPARISON_OPERATORS:
            raise InvalidFormRuleError("Rule operator is invalid.")
        if operator == "exists":
            if "value" in expression:
                raise InvalidFormRuleError("exists does not accept a value.")
        elif "value" not in expression:
            raise InvalidFormRuleError("Comparison operator requires a value.")
        if operator in {"in", "not_in"} and not isinstance(expression.get("value"), list):
            raise InvalidFormRuleError("in/not_in requires a value list.")

    def _validate_inheritance_rule(self, rule: RuleMapping) -> None:
        if not rule:
            return
        allowed = {"version", "source_path", "static_value", "mode"}
        if not set(rule).issubset(allowed) or rule.get("version") != 1:
            raise InvalidFormRuleError("Inheritance rule must use the version 1 grammar.")
        sources = {"source_path", "static_value"}.intersection(rule)
        if len(sources) != 1 or rule.get("mode") not in {
            "READ_ONLY",
            "EDITABLE_DEFAULT",
        }:
            raise InvalidFormRuleError("Inheritance source and mode are required.")
        if "source_path" in rule:
            path = rule["source_path"]
            if (
                not isinstance(path, str)
                or len(path) > 255
                or _PATH_PATTERN.fullmatch(path) is None
            ):
                raise InvalidFormRuleError("Inheritance source path is invalid.")

    def _evaluate_expression(self, expression: object, context: RuleMapping) -> bool:
        if not isinstance(expression, dict):
            return False
        if "all" in expression:
            children = expression["all"]
            return isinstance(children, list) and all(
                self._evaluate_expression(child, context) for child in children
            )
        if "any" in expression:
            children = expression["any"]
            return isinstance(children, list) and any(
                self._evaluate_expression(child, context) for child in children
            )
        if "not" in expression:
            return not self._evaluate_expression(expression["not"], context)
        found, actual = self._resolve_path(context, str(expression["path"]))
        operator = expression["operator"]
        if operator == "exists":
            return found and actual is not None
        expected = expression.get("value")
        if operator == "eq":
            return found and actual == expected
        if operator == "neq":
            return not found or actual != expected
        if operator == "in":
            return found and isinstance(expected, list) and actual in expected
        if operator == "not_in":
            return not found or (isinstance(expected, list) and actual not in expected)
        if not found:
            return False
        try:
            if operator == "gt":
                return bool(actual > expected)  # type: ignore[operator]
            if operator == "gte":
                return bool(actual >= expected)  # type: ignore[operator]
            if operator == "lt":
                return bool(actual < expected)  # type: ignore[operator]
            if operator == "lte":
                return bool(actual <= expected)  # type: ignore[operator]
        except TypeError:
            return False
        return False

    @staticmethod
    def _resolve_path(context: RuleMapping, path: str) -> tuple[bool, object | None]:
        current: object = context
        for segment in path.split("."):
            if not isinstance(current, dict) or segment not in current:
                return False, None
            current = current[segment]
        return True, current

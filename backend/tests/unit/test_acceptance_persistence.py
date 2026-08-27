"""Regression coverage for conditional-acceptance persistence ordering."""

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.acceptance import AcceptanceCondition, AcceptanceDecision, AcceptancePackage
from app.models.identity import User
from app.schemas.acceptance import AcceptanceDecisionCreate
from app.services.acceptance import AcceptanceService
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext


class Transaction(AbstractAsyncContextManager[None]):
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class SessionRecorder:
    def begin(self) -> Transaction:
        return Transaction()


class AcceptanceRepositoryRecorder:
    def __init__(self, package: AcceptancePackage, member_ids: set[object]) -> None:
        self.package = package
        self.member_ids = member_ids
        self.operations: list[tuple[str, list[object]]] = []

    async def accessible_package(self, *_: object, **__: object) -> AcceptancePackage:
        return self.package

    async def decision(self, *_: object) -> None:
        return None

    async def active_member_ids(self, *_: object) -> set[object]:
        return self.member_ids

    def add_all(self, values: list[object]) -> None:
        self.operations.append(("add", values))

    def add_audit_log(self, value: object) -> None:
        self.operations.append(("audit", [value]))

    async def flush(self) -> None:
        self.operations.append(("flush", []))


class PhaseRepositoryRecorder:
    async def set_lock(self, *_: object, **__: object) -> None:
        return None


@pytest.mark.asyncio
async def test_conditional_acceptance_flushes_decision_before_conditions() -> None:
    actor = User(
        id=uuid4(),
        username="employer",
        email="employer@example.test",
        password_hash="unused",  # noqa: S106
    )
    workspace_id = uuid4()
    package = AcceptancePackage(
        id=uuid4(),
        workspace_id=workspace_id,
        phase_id=uuid4(),
        sequence_number=1,
        statement="Acceptance package",
        employer_recipient_id=actor.id,
        requested_by=uuid4(),
        evidence_snapshot={},
        idempotency_key="package-idempotency",
    )
    responsible_id, verifier_id = uuid4(), actor.id
    recorder = AcceptanceRepositoryRecorder(package, {responsible_id, verifier_id})
    service = AcceptanceService(
        SessionRecorder(),  # type: ignore[arg-type]
        AuthenticatedIdentity(user=actor, roles=("EMPLOYER_REPRESENTATIVE",), permissions=()),
    )
    service.repository = recorder  # type: ignore[assignment]
    service.phase_repository = PhaseRepositoryRecorder()  # type: ignore[assignment]

    async def allow(*_: object) -> None:
        return None

    async def package_is_current(*_: object) -> None:
        return None

    async def response(value: AcceptancePackage) -> AcceptancePackage:
        return value

    service._require = allow  # type: ignore[method-assign,assignment]
    service._assert_package_current = package_is_current  # type: ignore[method-assign,assignment]
    service._response = response  # type: ignore[method-assign,assignment]
    payload = AcceptanceDecisionCreate(
        decision_kind="CONDITIONAL_ACCEPT",
        statement="Conditionally accepted",
        conditions=[
            {
                "description": "Provide final evidence",
                "responsible_id": responsible_id,
                "verifier_id": verifier_id,
                "due_at": datetime.now(UTC) + timedelta(days=1),
                "evidence_requirement": "Immutable evidence",
            }
        ],
        idempotency_key="decision-idempotency",
    )

    await service.decide(package.id, payload, AuditContext(uuid4(), None, None))

    assert [action for action, _ in recorder.operations] == [
        "add",
        "flush",
        "add",
        "audit",
        "flush",
    ]
    assert isinstance(recorder.operations[0][1][0], AcceptanceDecision)
    assert isinstance(recorder.operations[2][1][0], AcceptanceCondition)

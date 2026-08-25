"""Stable platform persistence models."""

from app.models.dashboard import Dashboard
from app.models.document import Document, DocumentVersion
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormField, FormInstance
from app.models.identity import (
    AuditLog,
    AuthSession,
    Permission,
    Role,
    User,
    role_permissions,
    user_roles,
)
from app.models.import_job import ImportConflict, ImportJob, ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.models.phase import Phase, PhaseDeliverable
from app.models.relationship import EntityRelationship, RelationshipType
from app.models.workflow import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowDefinitionVersion,
    WorkflowInstance,
    WorkflowStateDefinition,
    WorkflowTransitionDefinition,
    WorkflowTransitionEvent,
)
from app.models.workspace import Workspace, WorkspaceMembership

__all__ = [
    "AttributeDefinition",
    "AuditLog",
    "AuthSession",
    "Dashboard",
    "Document",
    "DocumentVersion",
    "EntityObject",
    "EntityRelationship",
    "EntityType",
    "FormDefinition",
    "FormField",
    "FormInstance",
    "ImportConflict",
    "ImportJob",
    "ImportMapping",
    "ImportProfile",
    "Permission",
    "Phase",
    "PhaseDeliverable",
    "RelationshipType",
    "Role",
    "User",
    "WorkflowAssignment",
    "WorkflowDefinition",
    "WorkflowDefinitionVersion",
    "WorkflowInstance",
    "WorkflowStateDefinition",
    "WorkflowTransitionDefinition",
    "WorkflowTransitionEvent",
    "Workspace",
    "WorkspaceMembership",
    "role_permissions",
    "user_roles",
]

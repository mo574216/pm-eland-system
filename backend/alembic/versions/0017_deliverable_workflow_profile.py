"""Install and bind the baseline configurable deliverable workflow profile.

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_definitions
                (id, workspace_id, key, name, description, created_by, version)
            SELECT gen_random_uuid(), d.workspace_id, 'system_deliverable_lifecycle',
                   'چرخه عمومی تحویل‌دادنی',
                   'پروفایل پایه قابل نسخه‌بندی برای تحویل، بازبینی و ارسال رسمی',
                   NULL, 1
            FROM deliverables d
            WHERE NOT EXISTS (
                SELECT 1 FROM workflow_definitions wd
                WHERE wd.workspace_id = d.workspace_id
                  AND wd.key = 'system_deliverable_lifecycle'
            )
            GROUP BY d.workspace_id
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_definition_versions
                (id, workspace_id, definition_id, version_number, status,
                 configuration, created_by, published_by, published_at)
            SELECT gen_random_uuid(), wd.workspace_id, wd.id, 1, 'PUBLISHED',
                   '{"system_profile":"DELIVERABLE_BASELINE"}'::jsonb,
                   wd.created_by, wd.created_by, now()
            FROM workflow_definitions wd
            WHERE wd.key = 'system_deliverable_lifecycle'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_definition_versions wv
                  WHERE wv.definition_id = wd.id
              )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_state_definitions
                (id, workspace_id, definition_version_id, key, label,
                 sequence_number, is_initial, is_terminal, configuration)
            SELECT gen_random_uuid(), wv.workspace_id, wv.id,
                   state.key, state.label, state.sequence_number,
                   state.is_initial, false, '{}'::jsonb
            FROM workflow_definition_versions wv
            JOIN workflow_definitions wd ON wd.id = wv.definition_id
            CROSS JOIN (VALUES
                ('preparation', 'در حال آماده‌سازی', 1, true),
                ('internal_review', 'در بازبینی داخلی', 2, false),
                ('ready', 'آماده ارسال رسمی', 3, false),
                ('submitted', 'ارسال رسمی شده', 4, false)
            ) AS state(key, label, sequence_number, is_initial)
            WHERE wd.key = 'system_deliverable_lifecycle'
              AND wv.status = 'PUBLISHED'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_state_definitions ws
                  WHERE ws.definition_version_id = wv.id
              )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_transition_definitions
                (id, workspace_id, definition_version_id, key, label,
                 from_state_id, to_state_id, required_permission, authority_kind,
                 assignment_kind, reason_required, policy)
            SELECT gen_random_uuid(), wv.workspace_id, wv.id,
                   transition.key, transition.label, source.id, target.id,
                   transition.permission, transition.authority,
                   transition.assignment_kind, transition.reason_required,
                   CASE WHEN transition.policy_key IS NULL THEN '{}'::jsonb
                        ELSE jsonb_build_object(transition.policy_key, true) END
            FROM workflow_definition_versions wv
            JOIN workflow_definitions wd ON wd.id = wv.definition_id
            CROSS JOIN (VALUES
                ('request_internal_review', 'ارسال برای بازبینی داخلی', 'preparation',
                 'internal_review', 'DELIVERABLE_CONTRIBUTE', 'CONTRIBUTION',
                 'CONTRIBUTOR', false, 'requires_package_readiness'),
                ('request_correction', 'بازگرداندن برای اصلاح', 'internal_review',
                 'preparation', 'DELIVERABLE_INTERNAL_REVIEW', 'INTERNAL_REVIEW',
                 'INTERNAL_REVIEWER', true, NULL),
                ('mark_ready', 'تأیید آمادگی برای ارسال', 'internal_review',
                 'ready', 'DELIVERABLE_INTERNAL_REVIEW', 'INTERNAL_REVIEW',
                 'INTERNAL_REVIEWER', false, 'requires_package_readiness'),
                ('formal_submit', 'ارسال رسمی', 'ready', 'submitted',
                 'SUBMISSION_CREATE', 'FORMAL_SUBMISSION', 'OWNER', false,
                 'requires_active_submission'),
                ('withdraw_submission', 'پس گرفتن ارسال رسمی', 'submitted', 'ready',
                 'SUBMISSION_CREATE', 'FORMAL_SUBMISSION', 'OWNER', true,
                 'requires_submission_withdrawal')
            ) AS transition(
                key, label, from_key, to_key, permission, authority,
                assignment_kind, reason_required, policy_key
            )
            JOIN workflow_state_definitions source
              ON source.definition_version_id = wv.id
             AND source.key = transition.from_key
            JOIN workflow_state_definitions target
              ON target.definition_version_id = wv.id
             AND target.key = transition.to_key
            WHERE wd.key = 'system_deliverable_lifecycle'
              AND wv.status = 'PUBLISHED'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_transition_definitions wt
                  WHERE wt.definition_version_id = wv.id
              )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_instances
                (id, workspace_id, definition_version_id, current_state_id,
                 target_kind, target_id, target_version, started_by, version)
            SELECT gen_random_uuid(), d.workspace_id, wv.id, initial.id,
                   'DELIVERABLE', d.id,
                   coalesce((SELECT max(dv.version_number)
                             FROM deliverable_versions dv
                             WHERE dv.deliverable_id = d.id), 1),
                   d.created_by, 1
            FROM deliverables d
            JOIN workflow_definitions wd
              ON wd.workspace_id = d.workspace_id
             AND wd.key = 'system_deliverable_lifecycle'
            JOIN LATERAL (
                SELECT id FROM workflow_definition_versions
                WHERE definition_id = wd.id AND status = 'PUBLISHED'
                ORDER BY version_number DESC LIMIT 1
            ) wv ON true
            JOIN workflow_state_definitions initial
              ON initial.definition_version_id = wv.id AND initial.is_initial = true
            WHERE NOT EXISTS (
                SELECT 1 FROM workflow_instances wi
                WHERE wi.workspace_id = d.workspace_id
                  AND wi.target_kind = 'DELIVERABLE'
                  AND wi.target_id = d.id
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_assignments
                (id, workspace_id, instance_id, user_id, assignment_kind,
                 assigned_by)
            SELECT gen_random_uuid(), source.workspace_id, source.instance_id,
                   source.user_id, source.assignment_kind, source.assigned_by
            FROM (
                SELECT wi.workspace_id, wi.id AS instance_id, da.user_id,
                       da.assignment_kind, da.assigned_by
                FROM workflow_instances wi
                JOIN deliverable_assignments da ON da.deliverable_id = wi.target_id
                WHERE wi.target_kind = 'DELIVERABLE'
                UNION
                SELECT wi.workspace_id, wi.id, d.owner_id, 'CONTRIBUTOR', d.created_by
                FROM workflow_instances wi
                JOIN deliverables d ON d.id = wi.target_id
                WHERE wi.target_kind = 'DELIVERABLE' AND d.owner_id IS NOT NULL
            ) source
            WHERE NOT EXISTS (
                SELECT 1 FROM workflow_assignments wa
                WHERE wa.instance_id = source.instance_id
                  AND wa.user_id = source.user_id
                  AND wa.assignment_kind = source.assignment_kind
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workflow_transition_events
                (id, workspace_id, instance_id, transition_id,
                 definition_version_id, previous_state_id, resulting_state_id,
                 action_key, authority_kind, actor_id, target_version,
                 resulting_instance_version, reason, context, idempotency_key)
            SELECT gen_random_uuid(), wi.workspace_id, wi.id, NULL,
                   wi.definition_version_id, NULL, wi.current_state_id,
                   'START', 'CONFIGURATION', wi.started_by, wi.target_version,
                   1, NULL, '{"profile":"system_deliverable_lifecycle"}'::jsonb,
                   'deliverable-start:' || wi.target_id::text
            FROM workflow_instances wi
            WHERE wi.target_kind = 'DELIVERABLE'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_transition_events we
                  WHERE we.instance_id = wi.id
              )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM workflow_instances
            WHERE target_kind = 'DELIVERABLE'
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM workflow_definitions
            WHERE key = 'system_deliverable_lifecycle'
              AND EXISTS (
                  SELECT 1 FROM workflow_definition_versions wv
                  WHERE wv.definition_id = workflow_definitions.id
                    AND wv.configuration ->> 'system_profile' = 'DELIVERABLE_BASELINE'
              )
            """
        )
    )

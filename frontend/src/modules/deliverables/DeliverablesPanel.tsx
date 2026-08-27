import { AddRounded, AssignmentTurnedInOutlined, EventOutlined } from '@mui/icons-material'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  LinearProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import { listWorkspaceMembers, type WorkspaceMember } from '../workspaces/workspaceApi'
import {
  createDeliverable,
  listDeliverableAssignmentOptions,
  createDeliverableVersion,
  addSubmissionReviewComment,
  listDeliverables,
  searchPackageOptions,
  recordSubmissionReviewOutcome,
  submitDeliverable,
  transitionDeliverableReview,
  withdrawSubmission,
  type Deliverable,
  type DeliverableCreate,
  type PackageResourceKind,
  type PackageResourceOption,
  type ReviewAction,
} from './deliverableApi'

interface CreateState {
  name: string
  description: string
  owner: WorkspaceMember | null
  reviewer: WorkspaceMember | null
  contributors: WorkspaceMember[]
  internalDue: string
  officialDue: string
}

const emptyState: CreateState = {
  name: '', description: '', owner: null, reviewer: null,
  contributors: [], internalDue: '', officialDue: '',
}

function memberLabel(member: WorkspaceMember): string {
  return member.display_name ?? member.username
}

function DeliverableActions({ item, members, locked, refresh }: { item: Deliverable; members: WorkspaceMember[]; locked: boolean; refresh: () => Promise<void> }) {
  const { t } = useTranslation()
  const [mode, setMode] = useState<'PACKAGE' | 'SUBMIT' | 'REVIEW' | null>(null)
  const [kind, setKind] = useState<PackageResourceKind>('DOCUMENT_VERSION')
  const [search, setSearch] = useState('')
  const [resource, setResource] = useState<PackageResourceOption | null>(null)
  const [summary, setSummary] = useState('')
  const [statement, setStatement] = useState('')
  const [recipients, setRecipients] = useState<WorkspaceMember[]>([])
  const [reason, setReason] = useState('')
  const [reviewReason, setReviewReason] = useState('')
  const [reviewAction, setReviewAction] = useState<ReviewAction | null>(null)
  const [reviewStatement, setReviewStatement] = useState('')
  const [reviewConditions, setReviewConditions] = useState('')
  const [commentText, setCommentText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const options = useQuery({
    queryKey: ['deliverable-package-options', item.id, kind, search],
    queryFn: () => searchPackageOptions(item.id, kind, search.trim()),
    enabled: mode === 'PACKAGE' && search.trim().length >= 2,
  })
  const packageMutation = useMutation({
    mutationFn: () => createDeliverableVersion(item.id, {
      summary: summary.trim() || null,
      items: resource ? [{ resource_kind: resource.resource_kind, resource_id: resource.id, requirement_key: null }] : [],
    }),
    onSuccess: async () => { setMode(null); setResource(null); setSearch(''); setSummary(''); await refresh() },
  })
  const submitMutation = useMutation({
    mutationFn: () => submitDeliverable(item.id, {
      deliverable_version_id: item.latest_version?.id ?? '',
      statement: statement.trim(), recipient_ids: recipients.map((member) => member.user_id),
      related_comment_ids: [], prior_submission_id: item.latest_submission?.id ?? null,
      idempotency_key: crypto.randomUUID(),
    }),
    onSuccess: async () => { setMode(null); setStatement(''); setRecipients([]); await refresh() },
  })
  const withdrawMutation = useMutation({
    mutationFn: () => withdrawSubmission(item.latest_submission?.id ?? '', reason.trim()),
    onSuccess: async () => { setReason(''); await refresh() },
  })
  const reviewMutation = useMutation({
    mutationFn: (actionKey: string) => transitionDeliverableReview(
      item.id, item.workflow?.version ?? 0, actionKey, reviewReason.trim() || null,
    ),
    onSuccess: async () => { setReviewReason(''); await refresh() },
  })
  const outcomeMutation = useMutation({
    mutationFn: () => recordSubmissionReviewOutcome(item.latest_submission?.id ?? '', {
      outcome_kind: reviewAction?.outcome_kind ?? '',
      authority_kind: reviewAction?.authority_kind ?? 'PROJECT_REVIEW',
      statement: reviewStatement.trim(),
      conditions: reviewConditions.split('\n').map((value) => value.trim()).filter(Boolean),
      related_comment_ids: [],
      expected_workflow_version: reviewAction?.changes_workflow ? item.workflow?.version ?? null : null,
    }),
    onSuccess: async () => {
      setMode(null); setReviewAction(null); setReviewStatement(''); setReviewConditions(''); await refresh()
    },
  })
  const commentMutation = useMutation({
    mutationFn: () => addSubmissionReviewComment(item.latest_submission?.id ?? '', commentText.trim()),
    onSuccess: async () => { setCommentText(''); await refresh() },
  })
  const run = async (operation: () => Promise<unknown>) => {
    setError(null)
    try { await operation() } catch (caught) {
      if (caught instanceof ApiError && caught.code === 'PERMISSION_DENIED') setError(t('deliverables.actionNotAllowed'))
      else if (caught instanceof ApiError && caught.code === 'VALIDATION_ERROR') setError(t('deliverables.notReady'))
      else setError(t('deliverables.actionFailed'))
    }
  }
  return (
    <Stack spacing={1.5}>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1 }}>
        <Button disabled={locked || item.workflow?.current_state_key !== 'preparation'} onClick={() => setMode(mode === 'PACKAGE' ? null : 'PACKAGE')} size="small" variant="outlined">{t('deliverables.preparePackage')}</Button>
        {item.workflow?.available_actions.filter((action) => !['formal_submit', 'withdraw_submission'].includes(action.key)).map((action) => (
          <Button disabled={locked || reviewMutation.isPending || (action.reason_required && reviewReason.trim() === '')} key={action.key} onClick={() => void run(() => reviewMutation.mutateAsync(action.key))} size="small" variant={action.key === 'mark_ready' ? 'contained' : 'outlined'}>{action.label}</Button>
        ))}
        <Button disabled={locked || !item.workflow?.available_actions.some((action) => action.key === 'formal_submit')} onClick={() => setMode(mode === 'SUBMIT' ? null : 'SUBMIT')} size="small" variant="contained">{item.latest_submission ? t('deliverables.resubmit') : t('deliverables.formalSubmit')}</Button>
        {item.latest_submission?.available_review_actions.length ? <Button disabled={locked} onClick={() => setMode(mode === 'REVIEW' ? null : 'REVIEW')} size="small" variant="contained" color="secondary">{t('deliverables.externalReview')}</Button> : null}
      </Stack>
      {item.workflow?.available_actions.some((action) => action.reason_required && !['withdraw_submission'].includes(action.key)) ? <TextField label={t('deliverables.reviewReason')} onChange={(event) => setReviewReason(event.target.value)} size="small" value={reviewReason} /> : null}
      <Collapse in={mode === 'PACKAGE'}>
        <Stack spacing={1.5} sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 1.5 }}>
          <TextField label={t('deliverables.contentType')} onChange={(event) => { setKind(event.target.value as PackageResourceKind); setResource(null); setSearch('') }} select value={kind}>
            <MenuItem value="DOCUMENT_VERSION">{t('deliverables.documentVersion')}</MenuItem>
            <MenuItem value="FORM_INSTANCE">{t('deliverables.formInstance')}</MenuItem>
            <MenuItem value="ENTITY">{t('deliverables.entityRecord')}</MenuItem>
          </TextField>
          <Autocomplete filterOptions={(values) => values} getOptionLabel={(option) => option.label} inputValue={search} loading={options.isFetching} noOptionsText={search.trim().length < 2 ? t('deliverables.searchHelp') : t('deliverables.noContentFound')} onChange={(_, value) => setResource(value)} onInputChange={(_, value) => setSearch(value)} options={options.data ?? []} renderInput={(params) => <TextField {...params} label={t('deliverables.content')} />} value={resource} />
          <TextField label={t('deliverables.packageSummary')} multiline onChange={(event) => setSummary(event.target.value)} value={summary} />
          <Button disabled={resource === null || packageMutation.isPending} onClick={() => void run(() => packageMutation.mutateAsync())} variant="contained">{t('deliverables.savePackage')}</Button>
        </Stack>
      </Collapse>
      <Collapse in={mode === 'REVIEW'}>
        <Stack spacing={1.5} sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 1.5 }}>
          <Alert severity="info">{t('deliverables.reviewVersionHint', { number: item.latest_version?.version_number.toLocaleString('fa-IR') })}</Alert>
          <TextField label={t('deliverables.reviewOutcome')} onChange={(event) => setReviewAction(item.latest_submission?.available_review_actions.find((action) => `${action.authority_kind}:${action.outcome_kind}` === event.target.value) ?? null)} select value={reviewAction ? `${reviewAction.authority_kind}:${reviewAction.outcome_kind}` : ''}>
            {item.latest_submission?.available_review_actions.map((action) => <MenuItem key={`${action.authority_kind}:${action.outcome_kind}`} value={`${action.authority_kind}:${action.outcome_kind}`}>{action.label}</MenuItem>)}
          </TextField>
          <TextField label={t('deliverables.reviewStatement')} multiline minRows={2} onChange={(event) => setReviewStatement(event.target.value)} value={reviewStatement} />
          {reviewAction?.outcome_kind === 'CONDITIONAL_RECOMMENDATION' ? <TextField helperText={t('deliverables.conditionsHint')} label={t('deliverables.conditions')} multiline onChange={(event) => setReviewConditions(event.target.value)} value={reviewConditions} /> : null}
          <Button disabled={!reviewAction || !reviewStatement.trim() || (reviewAction.outcome_kind === 'CONDITIONAL_RECOMMENDATION' && !reviewConditions.trim()) || outcomeMutation.isPending} onClick={() => void run(() => outcomeMutation.mutateAsync())} variant="contained">{t('deliverables.recordOutcome')}</Button>
          <Divider />
          <TextField label={t('deliverables.reviewComment')} multiline onChange={(event) => setCommentText(event.target.value)} value={commentText} />
          <Button disabled={!commentText.trim() || commentMutation.isPending} onClick={() => void run(() => commentMutation.mutateAsync())} variant="outlined">{t('deliverables.addComment')}</Button>
        </Stack>
      </Collapse>
      <Collapse in={mode === 'SUBMIT'}>
        <Stack spacing={1.5} sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 1.5 }}>
          <Alert severity="info">{t('deliverables.submissionSnapshotHint')}</Alert>
          <Autocomplete getOptionLabel={memberLabel} multiple onChange={(_, value) => setRecipients(value)} options={members} renderInput={(params) => <TextField {...params} label={t('deliverables.recipients')} />} value={recipients} />
          <TextField label={t('deliverables.submissionStatement')} multiline onChange={(event) => setStatement(event.target.value)} required value={statement} />
          <Button disabled={recipients.length === 0 || statement.trim() === '' || submitMutation.isPending} onClick={() => void run(() => submitMutation.mutateAsync())} variant="contained">{t('deliverables.confirmSubmit')}</Button>
        </Stack>
      </Collapse>
      {item.latest_submission && !item.latest_submission.withdrawn_at && item.workflow?.available_actions.some((action) => action.key === 'withdraw_submission') ? (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth label={t('deliverables.withdrawReason')} onChange={(event) => setReason(event.target.value)} size="small" value={reason} />
          <Button color="warning" disabled={locked || reason.trim() === '' || withdrawMutation.isPending} onClick={() => void run(() => withdrawMutation.mutateAsync())}>{t('deliverables.withdraw')}</Button>
        </Stack>
      ) : null}
    </Stack>
  )
}

export function DeliverablesPanel({ phaseId, workspaceId, locked }: { phaseId: string; workspaceId: string; locked: boolean }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<CreateState>(emptyState)
  const [error, setError] = useState<string | null>(null)
  const deliverables = useQuery({
    queryKey: ['deliverables', phaseId], queryFn: () => listDeliverables(phaseId),
  })
  const members = useQuery({
    queryKey: ['workspace-members', workspaceId], queryFn: () => listWorkspaceMembers(workspaceId),
  })
  const contributors = useQuery({
    queryKey: ['deliverable-assignees', phaseId, 'CONTRIBUTOR'],
    queryFn: () => listDeliverableAssignmentOptions(phaseId, 'CONTRIBUTOR'),
  })
  const reviewers = useQuery({
    queryKey: ['deliverable-assignees', phaseId, 'INTERNAL_REVIEWER'],
    queryFn: () => listDeliverableAssignmentOptions(phaseId, 'INTERNAL_REVIEWER'),
  })
  const activeMembers = useMemo(
    () => members.data?.filter((member) => member.status === 'ACTIVE') ?? [],
    [members.data],
  )
  const eligibleContributors = useMemo<WorkspaceMember[]>(
    () => contributors.data?.map((member) => ({ ...member, id: member.user_id, role_id: null, status: 'ACTIVE', created_at: '' })) ?? [],
    [contributors.data],
  )
  const eligibleReviewers = useMemo<WorkspaceMember[]>(
    () => reviewers.data?.map((member) => ({ ...member, id: member.user_id, role_id: null, status: 'ACTIVE', created_at: '' })) ?? [],
    [reviewers.data],
  )
  const create = useMutation({
    mutationFn: (payload: DeliverableCreate) => createDeliverable(phaseId, payload),
    onSuccess: async () => {
      setForm(emptyState)
      setCreating(false)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['deliverables', phaseId] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard-summary', workspaceId] }),
      ])
    },
  })
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['deliverables', phaseId] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary', workspaceId] }),
    ])
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    if (form.owner === null || form.reviewer === null || form.name.trim() === '') {
      setError(t('deliverables.requiredFields'))
      return
    }
    try {
      await create.mutateAsync({
        name: form.name.trim(), description: form.description.trim() || null,
        owner_id: form.owner.user_id,
        contributor_ids: form.contributors.map((member) => member.user_id),
        internal_reviewer_id: form.reviewer.user_id,
        internal_due_at: form.internalDue ? new Date(form.internalDue).toISOString() : null,
        official_due_at: form.officialDue ? new Date(form.officialDue).toISOString() : null,
        requirements: [],
      })
    } catch (caught) {
      setError(caught instanceof ApiError && caught.code === 'PERMISSION_DENIED'
        ? t('deliverables.permissionDenied') : t('deliverables.saveFailed'))
    }
  }

  return (
    <Stack spacing={2} sx={{ mt: 2 }}>
      <Divider />
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}>
        <Box>
          <Typography component="h3" variant="h6">{t('deliverables.title')}</Typography>
          <Typography color="text.secondary" variant="body2">{t('deliverables.phaseHint')}</Typography>
        </Box>
        <Button disabled={locked} onClick={() => setCreating((value) => !value)} startIcon={<AddRounded />} variant="outlined">
          {t('deliverables.add')}
        </Button>
      </Stack>
      {locked ? <Alert severity="warning">{t('deliverables.phaseLocked')}</Alert> : null}
      <Collapse in={creating && !locked}>
        <Stack component="form" onSubmit={(event) => void submit(event)} spacing={2} sx={{ bgcolor: 'action.hover', borderRadius: 3, p: 2 }}>
          <Typography component="h4" variant="subtitle1" sx={{ fontWeight: 800 }}>{t('deliverables.create')}</Typography>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField label={t('deliverables.name')} onChange={(event) => setForm({ ...form, name: event.target.value })} required value={form.name} />
          <TextField label={t('deliverables.description')} multiline onChange={(event) => setForm({ ...form, description: event.target.value })} value={form.description} />
          <Autocomplete getOptionLabel={memberLabel} loading={contributors.isPending} onChange={(_, value) => setForm({ ...form, owner: value })} options={eligibleContributors} renderInput={(params) => <TextField {...params} label={t('deliverables.owner')} required />} value={form.owner} />
          <Autocomplete getOptionLabel={memberLabel} loading={contributors.isPending} multiple onChange={(_, value) => setForm({ ...form, contributors: value })} options={eligibleContributors} renderInput={(params) => <TextField {...params} label={t('deliverables.contributors')} />} value={form.contributors} />
          <Autocomplete getOptionLabel={memberLabel} loading={reviewers.isPending} onChange={(_, value) => setForm({ ...form, reviewer: value })} options={eligibleReviewers} renderInput={(params) => <TextField {...params} label={t('deliverables.internalReviewer')} />} value={form.reviewer} />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField fullWidth label={t('deliverables.internalDue')} onChange={(event) => setForm({ ...form, internalDue: event.target.value })} slotProps={{ inputLabel: { shrink: true } }} type="datetime-local" value={form.internalDue} />
            <TextField fullWidth label={t('deliverables.officialDue')} onChange={(event) => setForm({ ...form, officialDue: event.target.value })} slotProps={{ inputLabel: { shrink: true } }} type="datetime-local" value={form.officialDue} />
          </Stack>
          <Stack direction="row" spacing={1}>
            <Button disabled={create.isPending} type="submit" variant="contained">{t('deliverables.save')}</Button>
            <Button onClick={() => setCreating(false)}>{t('deliverables.cancel')}</Button>
          </Stack>
        </Stack>
      </Collapse>
      {deliverables.isPending ? <CircularProgress aria-label={t('deliverables.loading')} size={28} /> : null}
      {deliverables.isError ? <Alert severity="error">{t('deliverables.loadFailed')}</Alert> : null}
      {deliverables.data?.length === 0 ? <Alert severity="info">{t('deliverables.empty')}</Alert> : null}
      {deliverables.data?.map((item) => {
        const denominator = Math.max(item.readiness.total_required, 1)
        const progress = item.readiness.ready ? 100 : (item.readiness.completed_required / denominator) * 100
        const owner = activeMembers.find((member) => member.user_id === item.owner_id)
        const reviewer = activeMembers.find((member) => member.user_id === item.internal_reviewer_id)
        const nextAction = item.workflow?.available_actions[0]
        return (
          <Box key={item.id} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 3, p: 2 }}>
            <Stack spacing={1.25}>
              <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}>
                <Typography component="h4" variant="subtitle1" sx={{ fontWeight: 900 }}>{item.name}</Typography>
                <Chip color={item.readiness.ready ? 'success' : 'default'} icon={<AssignmentTurnedInOutlined />} label={item.readiness.ready ? t('deliverables.ready') : t('deliverables.preparing')} />
              </Stack>
              {item.description ? <Typography color="text.secondary" variant="body2">{item.description}</Typography> : null}
              <Typography variant="body2">{t('deliverables.ownerValue', { name: owner ? memberLabel(owner) : t('deliverables.unassigned') })}</Typography>
              <Typography color="text.secondary" variant="body2">{t('deliverables.internalReviewerValue', { name: reviewer ? memberLabel(reviewer) : t('deliverables.unassigned') })}</Typography>
              <LinearProgress value={progress} variant="determinate" />
              {item.workflow ? <Chip color="primary" label={item.workflow.current_state_label} size="small" sx={{ alignSelf: 'flex-start' }} /> : null}
              {nextAction ? <Alert severity="info" sx={{ py: 0 }}>{t('deliverables.nextAction', { action: nextAction.label })}</Alert> : null}
              <Typography color="text.secondary" variant="caption">
                {item.latest_version ? t('deliverables.latestVersion', { number: item.latest_version.version_number.toLocaleString('fa-IR') }) : t('deliverables.noVersion')}
              </Typography>
              {item.official_due_at ? <Stack direction="row" spacing={1}><EventOutlined fontSize="small" /><Typography variant="caption">{t('deliverables.officialDueValue', { date: new Date(item.official_due_at).toLocaleString('fa-IR') })}</Typography></Stack> : null}
              {item.latest_submission ? <Alert severity={item.latest_submission.withdrawn_at ? 'warning' : 'success'}>{item.latest_submission.withdrawn_at ? t('deliverables.withdrawn') : t('deliverables.submitted', { number: item.latest_submission.sequence_number.toLocaleString('fa-IR') })}</Alert> : null}
              {item.latest_submission?.review_outcomes.map((outcome) => <Alert key={outcome.id} severity={['REVISION_REQUEST', 'REJECTION_MAJOR_REVISION'].includes(outcome.outcome_kind) ? 'warning' : 'info'}>{t('deliverables.reviewHistoryItem', { statement: outcome.statement })}</Alert>)}
              <DeliverableActions item={item} locked={locked} members={activeMembers} refresh={refresh} />
            </Stack>
          </Box>
        )
      })}
    </Stack>
  )
}

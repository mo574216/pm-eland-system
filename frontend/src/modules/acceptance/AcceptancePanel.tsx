import { FactCheckOutlined } from '@mui/icons-material'
import { Alert, Autocomplete, Box, Button, Chip, Collapse, Divider, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import type { PackageResourceKind, PackageResourceOption } from '../deliverables/deliverableApi'
import { listWorkspaceMembers, type WorkspaceMember } from '../workspaces/workspaceApi'
import {
  closeConditionalAcceptance,
  createAcceptancePackage,
  decideAcceptancePackage,
  getAcceptanceWorkspace,
  listAcceptanceRecipientOptions,
  searchConditionEvidence,
  submitConditionEvidence,
  verifyCondition,
  type AcceptanceCondition,
  type AcceptancePackage,
} from './acceptanceApi'

function memberLabel(member: WorkspaceMember): string { return member.display_name ?? member.username }

function memberName(members: WorkspaceMember[], userId: string | null): string | null {
  if (userId === null) return null
  return members.find((member) => member.user_id === userId)?.display_name
    ?? members.find((member) => member.user_id === userId)?.username
    ?? null
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function ConditionActions({ condition, refresh }: { condition: AcceptanceCondition; refresh: () => Promise<void> }) {
  const { t } = useTranslation()
  const [kind, setKind] = useState<PackageResourceKind>('DOCUMENT_VERSION')
  const [search, setSearch] = useState('')
  const [resource, setResource] = useState<PackageResourceOption | null>(null)
  const [statement, setStatement] = useState('')
  const options = useQuery({
    queryKey: ['acceptance-evidence-options', condition.id, kind, search],
    queryFn: () => searchConditionEvidence(condition.id, kind, search.trim()),
    enabled: condition.available_actions.includes('SUBMIT_EVIDENCE') && search.trim().length >= 2,
  })
  const evidence = useMutation({
    mutationFn: () => submitConditionEvidence(condition, statement.trim(), resource!),
    onSuccess: refresh,
  })
  const verification = useMutation({
    mutationFn: (decision: 'VERIFY' | 'REJECT_EVIDENCE') => verifyCondition(condition, decision, statement.trim()),
    onSuccess: refresh,
  })
  return (
    <Stack spacing={1}>
      {condition.available_actions.includes('SUBMIT_EVIDENCE') ? <>
        <TextField label={t('acceptance.evidenceType')} onChange={(event) => { setKind(event.target.value as PackageResourceKind); setResource(null); setSearch('') }} select size="small" value={kind}>
          <MenuItem value="DOCUMENT_VERSION">{t('deliverables.documentVersion')}</MenuItem><MenuItem value="FORM_INSTANCE">{t('deliverables.formInstance')}</MenuItem><MenuItem value="ENTITY">{t('deliverables.entityRecord')}</MenuItem>
        </TextField>
        <Autocomplete filterOptions={(values) => values} getOptionLabel={(option) => option.label} inputValue={search} onChange={(_, value) => setResource(value)} onInputChange={(_, value) => setSearch(value)} options={options.data ?? []} renderInput={(params) => <TextField {...params} label={t('acceptance.evidence')} size="small" />} value={resource} />
      </> : null}
      {condition.available_actions.length ? <TextField label={t('acceptance.actionStatement')} multiline onChange={(event) => setStatement(event.target.value)} size="small" value={statement} /> : null}
      <Stack direction="row" spacing={1}>
        {condition.available_actions.includes('SUBMIT_EVIDENCE') ? <Button disabled={!resource || !statement.trim() || evidence.isPending} onClick={() => evidence.mutate()} size="small">{t('acceptance.submitEvidence')}</Button> : null}
        {condition.available_actions.includes('VERIFY') ? <Button disabled={!statement.trim() || verification.isPending} onClick={() => verification.mutate('VERIFY')} size="small" variant="contained">{t('acceptance.verify')}</Button> : null}
        {condition.available_actions.includes('REJECT_EVIDENCE') ? <Button color="warning" disabled={!statement.trim() || verification.isPending} onClick={() => verification.mutate('REJECT_EVIDENCE')} size="small">{t('acceptance.rejectEvidence')}</Button> : null}
      </Stack>
    </Stack>
  )
}

function PackageCard({ item, members, refresh }: { item: AcceptancePackage; members: WorkspaceMember[]; refresh: () => Promise<void> }) {
  const { t } = useTranslation()
  const [decisionKind, setDecisionKind] = useState('')
  const [statement, setStatement] = useState('')
  const [responsible, setResponsible] = useState<WorkspaceMember | null>(null)
  const [verifier, setVerifier] = useState<WorkspaceMember | null>(null)
  const [conditionDescription, setConditionDescription] = useState('')
  const [requirement, setRequirement] = useState('')
  const [dueAt, setDueAt] = useState('')
  const decision = useMutation({
    mutationFn: () => decideAcceptancePackage(item.id, {
      decision_kind: decisionKind, statement: statement.trim(),
      conditions: decisionKind === 'CONDITIONAL_ACCEPT' && responsible && verifier ? [{
        description: conditionDescription.trim(), responsible_id: responsible.user_id,
        verifier_id: verifier.user_id, due_at: new Date(dueAt).toISOString(),
        evidence_requirement: requirement.trim(), mandatory: true,
      }] : [],
    }), onSuccess: refresh,
  })
  const closure = useMutation({ mutationFn: () => closeConditionalAcceptance(item.decision?.id ?? '', statement.trim()), onSuccess: refresh })
  const conditionalComplete = decisionKind !== 'CONDITIONAL_ACCEPT' || Boolean(responsible && verifier && dueAt && conditionDescription.trim() && requirement.trim())
  const nameOrFallback = (userId: string | null) => memberName(members, userId) ?? t('acceptance.unknownMember')
  return <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 1.5 }}><Stack spacing={1.25}>
    <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}><Typography sx={{ fontWeight: 800 }}>{t('acceptance.packageNumber', { number: item.sequence_number.toLocaleString('fa-IR') })}</Typography><Chip icon={<FactCheckOutlined />} label={item.decision ? t(`acceptance.decision.${item.decision.decision_kind}`) : t('acceptance.awaitingDecision')} size="small" /></Stack>
    <Typography color="text.secondary" variant="body2">{item.statement}</Typography>
    <Stack spacing={0.5} sx={{ bgcolor: 'action.hover', borderRadius: 1.5, p: 1 }}>
      <Typography variant="caption">{t('acceptance.requestedFor', { name: nameOrFallback(item.employer_recipient_id) })}</Typography>
      {item.requested_by ? <Typography variant="caption">{t('acceptance.requestedBy', { name: nameOrFallback(item.requested_by) })}</Typography> : null}
      <Typography variant="caption">{t('acceptance.requestedAt', { value: formatDate(item.created_at) })}</Typography>
    </Stack>
    <Box><Typography sx={{ fontWeight: 700 }} variant="body2">{t('acceptance.evidenceItems')}</Typography><Typography variant="caption">{t('acceptance.evidenceCount', { count: item.items.length.toLocaleString('fa-IR') })}</Typography><Stack component="ul" spacing={0.25} sx={{ m: 0, mt: 0.5, ps: 2.5 }}>{item.items.map((evidence) => <Typography component="li" key={evidence.id} variant="body2">{evidence.label_snapshot}</Typography>)}</Stack></Box>
    {item.decision ? <Stack spacing={0.5} sx={{ borderInlineStart: '3px solid', borderColor: item.decision.closed_at ? 'success.main' : 'primary.main', ps: 1.25 }}>
      <Typography variant="body2">{item.decision.statement}</Typography>
      <Typography variant="caption">{t('acceptance.decidedBy', { name: nameOrFallback(item.decision.actor_id) })}</Typography>
      <Typography variant="caption">{t('acceptance.decidedAt', { value: formatDate(item.decision.decided_at) })}</Typography>
      {item.decision.closure_statement ? <Typography variant="caption">{item.decision.closure_statement}</Typography> : null}
    </Stack> : null}
    {item.available_decisions.length ? <>
      <TextField label={t('acceptance.decisionLabel')} onChange={(event) => setDecisionKind(event.target.value)} select size="small" value={decisionKind}>{item.available_decisions.map((value) => <MenuItem key={value} value={value}>{t(`acceptance.decision.${value}`)}</MenuItem>)}</TextField>
      <TextField label={t('acceptance.decisionStatement')} multiline onChange={(event) => setStatement(event.target.value)} value={statement} />
      <Collapse in={decisionKind === 'CONDITIONAL_ACCEPT'}><Stack spacing={1.25} sx={{ pt: 1 }}>
        <TextField label={t('acceptance.conditionDescription')} onChange={(event) => setConditionDescription(event.target.value)} value={conditionDescription} />
        <Autocomplete getOptionLabel={memberLabel} onChange={(_, value) => setResponsible(value)} options={members} renderInput={(params) => <TextField {...params} label={t('acceptance.responsible')} />} value={responsible} />
        <Autocomplete getOptionLabel={memberLabel} onChange={(_, value) => setVerifier(value)} options={members} renderInput={(params) => <TextField {...params} label={t('acceptance.verifier')} />} value={verifier} />
        <TextField label={t('acceptance.dueAt')} onChange={(event) => setDueAt(event.target.value)} slotProps={{ inputLabel: { shrink: true } }} type="datetime-local" value={dueAt} />
        <TextField label={t('acceptance.evidenceRequirement')} onChange={(event) => setRequirement(event.target.value)} value={requirement} />
      </Stack></Collapse>
      <Button disabled={!decisionKind || !statement.trim() || !conditionalComplete || decision.isPending} onClick={() => decision.mutate()} variant="contained">{t('acceptance.recordDecision')}</Button>
    </> : null}
    {item.decision?.conditions.map((condition) => <Box key={condition.id} sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 1.25 }}><Stack spacing={1}>
      <Stack direction="row" sx={{ justifyContent: 'space-between' }}><Typography sx={{ fontWeight: 700 }}>{condition.description}</Typography><Chip label={t(`acceptance.conditionStatus.${condition.status}`)} size="small" /></Stack>
      <Typography color="text.secondary" variant="caption">{condition.evidence_requirement}</Typography>
      <Typography variant="caption">{t('acceptance.responsible')}: {nameOrFallback(condition.responsible_id)}</Typography>
      <Typography variant="caption">{t('acceptance.verifier')}: {nameOrFallback(condition.verifier_id)}</Typography>
      <Typography variant="caption">{t('acceptance.dueAt')}: {formatDate(condition.due_at)}</Typography><ConditionActions condition={condition} refresh={refresh} />
    </Stack></Box>)}
    {item.decision?.can_close ? <><TextField label={t('acceptance.closureStatement')} multiline onChange={(event) => setStatement(event.target.value)} value={statement} /><Button disabled={!statement.trim() || closure.isPending} onClick={() => closure.mutate()} variant="contained">{t('acceptance.close')}</Button></> : null}
    {item.decision?.closed_at ? <Alert severity="success">{t('acceptance.closed')}</Alert> : null}
  </Stack></Box>
}

export function AcceptancePanel({ phaseId, workspaceId }: { phaseId: string; workspaceId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [recipient, setRecipient] = useState<WorkspaceMember | null>(null)
  const [statement, setStatement] = useState('')
  const [error, setError] = useState<string | null>(null)
  const packages = useQuery({ queryKey: ['acceptance-packages', phaseId], queryFn: () => getAcceptanceWorkspace(phaseId) })
  const members = useQuery({ queryKey: ['workspace-members', workspaceId], queryFn: () => listWorkspaceMembers(workspaceId) })
  const recipients = useQuery({
    queryKey: ['acceptance-recipients', phaseId], queryFn: () => listAcceptanceRecipientOptions(phaseId),
  })
  const activeMembers = members.data?.filter((member) => member.status === 'ACTIVE') ?? []
  const eligibleRecipients = useMemo<WorkspaceMember[]>(
    () => recipients.data?.map((member) => ({ ...member, id: member.user_id, role_id: null, status: 'ACTIVE', created_at: '' })) ?? [],
    [recipients.data],
  )
  const refresh = async () => { await Promise.all([queryClient.invalidateQueries({ queryKey: ['acceptance-packages', phaseId] }), queryClient.invalidateQueries({ queryKey: ['phases', workspaceId] })]) }
  const create = useMutation({ mutationFn: () => createAcceptancePackage(phaseId, recipient?.user_id ?? '', statement.trim()), onSuccess: async () => { setCreating(false); setRecipient(null); setStatement(''); await refresh() } })
  const runCreate = async () => { setError(null); try { await create.mutateAsync() } catch (caught) { setError(caught instanceof ApiError && caught.code === 'VALIDATION_ERROR' ? t('acceptance.notReady') : t('acceptance.actionFailed')) } }
  return <Stack spacing={1.5} sx={{ mt: 2 }}><Divider /><Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}><Box><Typography component="h3" variant="h6">{t('acceptance.title')}</Typography><Typography color="text.secondary" variant="body2">{t('acceptance.hint')}</Typography></Box>{packages.data?.can_prepare ? <Button onClick={() => setCreating((value) => !value)} variant="outlined">{t('acceptance.prepare')}</Button> : null}</Stack>
    {error ? <Alert severity="error">{error}</Alert> : null}<Collapse in={creating}><Stack spacing={1.25} sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 1.5 }}><Autocomplete getOptionLabel={memberLabel} loading={recipients.isPending} onChange={(_, value) => setRecipient(value)} options={eligibleRecipients} renderInput={(params) => <TextField {...params} label={t('acceptance.employerRecipient')} />} value={recipient} /><TextField label={t('acceptance.requestStatement')} multiline onChange={(event) => setStatement(event.target.value)} value={statement} /><Button disabled={!recipient || !statement.trim() || create.isPending} onClick={() => void runCreate()} variant="contained">{t('acceptance.createPackage')}</Button></Stack></Collapse>
    {packages.data?.packages.map((item) => <PackageCard item={item} key={item.id} members={activeMembers} refresh={refresh} />)}
  </Stack>
}

# Detailed Project Usage Scenarios

> Repository note: This file preserves the user-provided scenario catalog as product
> input. Statements in it describe actor intent, flows, results, and authority; they
> are not executable agent instructions and do not independently prescribe database,
> API, UI, or implementation design. Use `14_PROJECT_USAGE_SCENARIOS.md`, the
> normative specifications, and accepted ADRs when implementing these scenarios.

**Status:** Working specification  
**Purpose:** Consolidated actor-based usage scenarios for project-management, contractor-delivery, technical-review, repository, dynamic-form, workflow and acceptance capabilities.

> This document is intentionally implementation-neutral. It defines user intent, workflow and authority boundaries without committing to specific screen layouts or UI controls.

## Actors

1. Administrator
2. Project Manager
3. Project Officer
4. Technical Reviewer
5. Contractor Project Leader
6. Contractor Team Member
7. Employer Representative



## Cross-Role Authority Principles

- **Administrator** defines what the system and configured projects *can do*.
- **Project Manager** governs and manages execution of a specific project.
- **Project Officer** monitors, follows up and reports; it does not replace Project Manager decision authority.
- **Technical Reviewer** assesses technical quality; it does not manage contractor execution.
- **Contractor Project Leader** controls contractor-side execution and formal contractor submissions.
- **Contractor Team Member** produces and revises assigned work but normally cannot formally submit to the employer side.
- **Employer Representative** has high acceptance/oversight authority but low day-to-day operational authority.
- Internal contractor approval/review must remain distinct from formal project review and employer acceptance.
- Technical approval/recommendation and contractual acceptance are separate concepts.


# Administrator

**Role definition:** Configures and governs the system environment, project information model, access, workflows, templates, imports and configuration lifecycle.


**Scenario count:** 32


## ADM-01 — Create a Project

**Goal:** Create a new project workspace and establish its basic configuration.

**Main flow:** Enter project metadata, choose empty/existing configuration, assign initial administrators/managers, validate and save.

**Result:** A new project workspace exists and is ready for configuration.


## ADM-02 — Configure Project Hierarchy

**Goal:** Define the information structure used by a project.

**Main flow:** Define entity/content-type hierarchy, allowed parent-child relationships, mandatory/optional/repeatable levels, validate and publish.

**Result:** The project has a valid configurable hierarchy.


## ADM-03 — Define an Entity Type

**Goal:** Create a new type of information object without changing application code.

**Main flow:** Define name/code/description, parent-child rules, supported capabilities such as structured data/files/comments/relations/versioning, then save.

**Result:** The new type is available through the generic UI.


## ADM-04 — Design a Dynamic Form

**Goal:** Define the data-capture schema for an entity type.

**Main flow:** Create sections and fields, configure field type, validation, defaults, help, visibility/conditional rules, preview and publish.

**Result:** The entity type has a published dynamic form.


## ADM-05 — Configure Field Inheritance and Prefill

**Goal:** Populate fields automatically from parent/project context.

**Main flow:** Select target field, define source, choose copied/referenced/editable/read-only behavior, then save.

**Result:** Repeated information can be inherited or prefilled consistently.


## ADM-06 — Define Lookup Lists and Taxonomies

**Goal:** Create reusable controlled vocabularies.

**Main flow:** Create lookup/taxonomy, add/order/group values, activate/deactivate values, associate with fields.

**Result:** Forms can use controlled, consistent values.


## ADM-07 — Configure Relationships Between Entity Types

**Goal:** Define semantic links between information objects.

**Main flow:** Select source/target types, relationship name, cardinality, reverse visibility and save.

**Result:** Users can create structured relationships between project objects.


## ADM-08 — Configure Accepted Content and File Types

**Goal:** Control which files/content may be stored.

**Main flow:** Define allowed formats, entity associations, metadata requirements, size/restriction rules.

**Result:** File handling follows project-specific rules.


## ADM-09 — Define Document Categories

**Goal:** Create consistent categories for project documents.

**Main flow:** Create categories, descriptions and applicability rules; associate them with upload contexts.

**Result:** Documents can be classified, searched, filtered and governed consistently.


## ADM-10 — Create and Manage Project Templates

**Goal:** Provide standardized project artifacts.

**Main flow:** Create/upload template, associate with project/entity/phase/deliverable, set version and publish.

**Result:** Users can work from approved templates.


## ADM-11 — Version a Template

**Goal:** Update templates without losing history.

**Main flow:** Create a new version, record change notes, publish it while retaining previous versions.

**Result:** New work uses the latest template and historical work remains traceable.


## ADM-12 — Configure Import Sources

**Goal:** Define reusable external data-import profiles.

**Main flow:** Choose source format, target entity/form, expected structure and save the profile.

**Result:** Approved import profiles are available to users.


## ADM-13 — Define Import Field Mapping

**Goal:** Map external columns to system attributes.

**Main flow:** Map source columns to fields, configure transformations/defaults, test and save.

**Result:** Future imports use a consistent mapping.


## ADM-14 — Configure Duplicate Detection and Merge Rules

**Goal:** Control conflicts with existing records during import.

**Main flow:** Define unique/matching keys and skip/replace/merge/ask behavior plus field-level conflict rules.

**Result:** Imports do not accidentally duplicate or overwrite data.


## ADM-15 — Configure Data Validation Rules

**Goal:** Define project-specific integrity constraints.

**Main flow:** Create validation rules, conditions and messages; associate with forms/entities/imports.

**Result:** Invalid project data is prevented or flagged.


## ADM-16 — Configure Project Workflow

**Goal:** Define lifecycle states and permitted transitions.

**Main flow:** Create statuses, transitions, role permissions and transition conditions; publish workflow.

**Result:** Project objects follow a controlled lifecycle.


## ADM-17 — Configure Review and Approval Rules

**Goal:** Define who reviews and approves project work.

**Main flow:** Specify reviewer/approver roles, required approvals, sequencing and conditions.

**Result:** Review and approval responsibility is explicit.


## ADM-18 — Configure Locking and Reopening Rules

**Goal:** Protect completed records while permitting controlled reopening.

**Main flow:** Define lock triggers, authorized unlockers, reason/approval/audit requirements.

**Result:** Completed information is protected and exceptions are traceable.


## ADM-19 — Configure Versioning Rules

**Goal:** Define how object history is maintained.

**Main flow:** Choose versioned types, triggers, numbering, draft behavior and restoration rights.

**Result:** Historical changes are consistently retained.


## ADM-20 — Create Users

**Goal:** Register users who may access the system.

**Main flow:** Enter identity/profile data, assign roles and project membership, activate account.

**Result:** The user can access permitted areas.


## ADM-21 — Define Roles

**Goal:** Create reusable access profiles.

**Main flow:** Create role, describe responsibilities and associate permissions.

**Result:** Permissions can be managed through role-based access control.


## ADM-22 — Configure Permissions

**Goal:** Define what each role may do and at what scope.

**Main flow:** Assign capabilities such as view/create/edit/delete/submit/review/approve/comment/import/export/lock/configure, with system/project/entity/workflow scope.

**Result:** Authorization rules are explicit and enforceable.


## ADM-23 — Assign Users to Projects

**Goal:** Establish project membership.

**Main flow:** Select project, add users, assign project-specific roles and optional effective dates.

**Result:** Project participation is established.


## ADM-24 — Configure Naming and Numbering Rules

**Goal:** Generate consistent project identifiers.

**Main flow:** Define prefixes, sequences, hierarchical numbering and uniqueness rules.

**Result:** Objects receive standardized identifiers.


## ADM-25 — Configure Notifications

**Goal:** Define events that create notifications and recipients.

**Main flow:** Choose events, recipient roles, delivery channels and conditions.

**Result:** Users are informed about relevant project events.


## ADM-26 — Configure Project Phases and Milestones

**Goal:** Define configurable project execution structure.

**Main flow:** Create reusable phase/milestone definitions, dates/rules, deliverables and approval requirements.

**Result:** Projects can operate using approved phase/milestone structures.


## ADM-27 — Configure Project Views

**Goal:** Define default presentation of project information.

**Main flow:** Configure visible columns, sorting, filters, grouping and role-specific defaults.

**Result:** Users receive useful default views without hard-coded screens.


## ADM-28 — Configure Dashboards and Indicators

**Goal:** Define project monitoring metrics.

**Main flow:** Select indicators, aggregation rules, thresholds and target audiences.

**Result:** Managers can monitor project status using configurable dashboards.


## ADM-29 — Clone Project Configuration

**Goal:** Reuse an existing project's configuration.

**Main flow:** Select source project and configuration components to copy while excluding operational data unless explicitly requested.

**Result:** Similar projects can be initialized quickly.


## ADM-30 — Modify Existing Project Configuration

**Goal:** Safely change configuration after work has begun.

**Main flow:** Request change, evaluate impact on existing data, review warnings, apply/version/audit change.

**Result:** Configuration evolves without silently corrupting project data.


## ADM-31 — Review Configuration History

**Goal:** Inspect who changed configuration and when.

**Main flow:** View previous/new values, actor, date, project and reason.

**Result:** Configuration changes are auditable.


## ADM-32 — Archive a Project

**Goal:** Close a project without deleting history.

**Main flow:** Request archive, check unresolved operations, change to read-only/restricted state and retain records.

**Result:** Project is preserved as an historical record.


# Project Manager

**Role definition:** Manages project execution from the governance/client side, including team, phases, milestones, activities, deliverables, deadlines, comments, risks and reporting.


**Scenario count:** 40


## PM-01 — Define a Project

**Goal:** Create or complete the operational definition of an assigned project.

**Main flow:** Set title/code/client/objectives/dates/status and applicable configuration/template, then save.

**Result:** The project is ready for operational planning.


## PM-02 — Add Team Members to a Project

**Goal:** Establish the project team.

**Main flow:** Select users, add them to the project, assign project-specific roles and save.

**Result:** Selected users become project participants.


## PM-03 — Remove or Replace a Team Member

**Goal:** Maintain team composition when responsibilities change.

**Main flow:** Review current assignments, remove/replace member, reassign incomplete work and confirm.

**Result:** Membership changes without losing work ownership.


## PM-04 — Assign Project Roles

**Goal:** Define each team member's project responsibility.

**Main flow:** Assign role(s) within the project according to allowed role set.

**Result:** Responsibilities and permissions reflect the project role.


## PM-05 — Define Project Phases

**Goal:** Divide the project into execution stages.

**Main flow:** Create phase, define description/dates/sequence/responsible members/milestones/deliverables and save.

**Result:** The project has an operational phase structure.


## PM-06 — Modify a Project Phase

**Goal:** Adjust an existing phase.

**Main flow:** Change dates/description/membership/status, review impact on related items, save with history.

**Result:** Phase definition is updated traceably.


## PM-07 — Close or Reopen a Project Phase

**Goal:** Control phase lifecycle.

**Main flow:** Check mandatory milestones/deliverables, close when ready; reopen with reason if authorized.

**Result:** Phase state accurately reflects execution.


## PM-08 — Define a Milestone

**Goal:** Create a measurable project checkpoint.

**Main flow:** Set name/description/date/phase/owner/related deliverables/completion criteria and save.

**Result:** Milestone is included in the project schedule.


## PM-09 — Monitor Milestones

**Goal:** Track milestone performance.

**Main flow:** View status, filter by phase/owner, inspect delayed or at-risk milestones.

**Result:** Schedule problems can be identified early.


## PM-10 — Create an Activity or Task

**Goal:** Define operational work.

**Main flow:** Create activity with scope, owner, collaborators, dates, priority, status and related entities.

**Result:** Activity becomes part of the project work plan.


## PM-11 — Assign an Activity

**Goal:** Make a team member responsible for work.

**Main flow:** Select activity, assign responsible user/collaborators/reviewer, set deadline and notify.

**Result:** Responsibility is explicit.


## PM-12 — Reassign an Activity

**Goal:** Transfer work ownership.

**Main flow:** Select activity, review progress, choose new owner, record reason and confirm.

**Result:** Work ownership changes without losing history.


## PM-13 — Define Activity Dependencies

**Goal:** Represent execution dependencies.

**Main flow:** Select activity, add prerequisites/successors, validate no cycles and save.

**Result:** Blocked/downstream work can be identified.


## PM-14 — Monitor Activities

**Goal:** Track execution status.

**Main flow:** View/filter not-started/in-progress/completed/blocked/overdue activities by phase/member/etc.

**Result:** Current execution state is visible.


## PM-15 — Define a Deliverable

**Goal:** Specify a required project output.

**Main flow:** Set title/scope/phase/milestone/entity/owner/deadline/template/content type/reviewer and save.

**Result:** Deliverable is formally included in the plan.


## PM-16 — Monitor Deliverable Status

**Goal:** Track production and review status.

**Main flow:** View deliverables by lifecycle state and identify missing, delayed or pending items.

**Result:** Delivery obligations are visible.


## PM-17 — Monitor Uploaded Outputs

**Goal:** Review newly uploaded content across the project.

**Main flow:** Filter by phase/member/entity/content type/deliverable and inspect metadata/status.

**Result:** Project Manager maintains visibility over produced outputs.


## PM-18 — Review a Deliverable

**Goal:** Evaluate a submitted output.

**Main flow:** Review structured data/files/history/comments and approve, request revision or forward for review.

**Result:** Deliverable progresses through review.


## PM-19 — Request Revision

**Goal:** Return an output for correction.

**Main flow:** Add required comments, mark mandatory items, set revision deadline and notify responsible user.

**Result:** Deliverable enters revision state.


## PM-20 — Approve a Deliverable

**Goal:** Confirm that an output satisfies project requirements.

**Main flow:** Verify latest version and comment resolution, approve, record approver/date/version and apply configured next state.

**Result:** Deliverable receives PM approval.


## PM-21 — Submit a Deliverable for External Approval

**Goal:** Forward PM-approved output to Employer/other reviewer.

**Main flow:** Select deliverable/reviewer, add note and submit.

**Result:** Deliverable enters external approval.


## PM-22 — Add a Comment to Project Content

**Goal:** Provide contextual feedback.

**Main flow:** Attach comment to deliverable/document/form/entity/activity/milestone/phase with optional mention/priority/category.

**Result:** Feedback becomes part of item history.


## PM-23 — Resolve or Reopen a Comment

**Goal:** Manage feedback lifecycle.

**Main flow:** Review response/revision and mark resolved or reopened with explanation.

**Result:** Comment status accurately reflects outstanding work.


## PM-24 — Monitor Unresolved Comments

**Goal:** Track comments still requiring action.

**Main flow:** Filter by phase/member/deliverable/priority/age/status and inspect stalled items.

**Result:** Review issues do not get lost.


## PM-25 — Send a Message to a Team Member

**Goal:** Communicate directly in project context.

**Main flow:** Select user, write message, optionally link project object and send.

**Result:** Project-contextual communication is recorded.


## PM-26 — Send a Project Announcement

**Goal:** Broadcast important project information.

**Main flow:** Create announcement, choose whole-project/phase/selected recipients and send.

**Result:** Relevant participants receive consistent information.


## PM-27 — Monitor Project Deadlines

**Goal:** Track time-related obligations.

**Main flow:** Monitor project/phase/milestone/activity/deliverable/review deadlines and classify on-track/due-soon/at-risk/overdue/completed.

**Result:** Schedule risks are visible.


## PM-28 — Change a Deadline

**Goal:** Adjust an authorized project date.

**Main flow:** Change date, record reason, review impacted dependencies, confirm and notify affected users.

**Result:** Schedule is updated with audit history.


## PM-29 — Monitor Overall Project Progress

**Goal:** Assess project execution against plan.

**Main flow:** View progress by project/phase/milestone/deliverable/activity and drill into weak areas.

**Result:** Current project state is understood.


## PM-30 — View Project Dashboard

**Goal:** Obtain consolidated management view.

**Main flow:** View progress, days remaining, current phase, milestones, overdue work, pending reviews, comments, workload, uploads and risks.

**Result:** Key management information is available in one place.


## PM-31 — Monitor Team Workload

**Goal:** Identify workload imbalance.

**Main flow:** Compare active work/overdue work/deliverables/reviews by user and reassign where needed.

**Result:** Workload can be balanced.


## PM-32 — Record a Project Risk

**Goal:** Track a potential project threat.

**Main flow:** Record description/probability/impact/severity/owner/mitigation/date and associations.

**Result:** Risk is visible and trackable.


## PM-33 — Record a Project Issue

**Goal:** Track an existing project problem.

**Main flow:** Record description/severity/owner/action/deadline and track to resolution.

**Result:** Active problems are formally managed.


## PM-34 — Escalate a Critical Issue

**Goal:** Raise serious risk/delay/problem to higher stakeholders.

**Main flow:** Select issue, record urgency/reason, choose recipients and escalate.

**Result:** Critical issues receive appropriate attention.


## PM-35 — Review Project Changes and Delays

**Goal:** Understand divergence from original plan.

**Main flow:** Review deadline/milestone/assignment/scope changes and recorded reasons.

**Result:** Schedule and scope changes remain traceable.


## PM-36 — Generate a Project Status Report

**Goal:** Produce a project-performance summary.

**Main flow:** Generate report containing progress, milestones, overdue items, deliverables, comments, risks/issues and workload.

**Result:** Management status can be shared/exported.


## PM-37 — Generate a Deliverable Status Report

**Goal:** Summarize all deliverables.

**Main flow:** Generate list of owner/deadline/version/status/reviewer/approval/delay.

**Result:** Deliverable completion is systematically reportable.


## PM-38 — View Project Activity Timeline

**Goal:** Inspect chronological project events.

**Main flow:** View submissions, revisions, phase changes, assignments, approvals and other important events.

**Result:** Project history can be reconstructed.


## PM-39 — Monitor Project Structure Completion

**Goal:** Check required content across the project hierarchy.

**Main flow:** Identify empty entities, incomplete forms, missing documents/deliverables and unassigned items.

**Result:** Structural completeness is measurable.


## PM-40 — Close a Project

**Goal:** Formally complete operational project execution.

**Main flow:** Check milestones/deliverables/reviews/issues, resolve or justify exceptions, mark completed and forward for archive/acceptance workflow.

**Result:** Project execution is formally completed.


# Project Officer

**Role definition:** Supports the Project Manager by monitoring progress, deadlines, deliverables, comments and review queues, performing delegated completeness checks, follow-up and reporting.


**Scenario count:** 52


## PO-01 — Access Assigned Project

**Goal:** Access project information required for monitoring/reporting.

**Main flow:** Open assigned project and navigate permitted phases, milestones, activities, deliverables, comments and reports.

**Result:** Officer can monitor without full PM authority.


## PO-02 — View Project Monitoring Dashboard

**Goal:** See an overview of project health.

**Main flow:** Review progress, current phase, milestones, overdue work, deliverables, reviews, comments, uploads and pending actions.

**Result:** Issues needing follow-up are visible.


## PO-03 — View Project Structure

**Goal:** Understand project hierarchy and completion state.

**Main flow:** Navigate project hierarchy and inspect status indicators.

**Result:** Officer sees complete/incomplete/missing areas.


## PO-04 — Monitor Project Progress

**Goal:** Track execution against plan.

**Main flow:** Review progress by project/phase/milestone/activity/deliverable/project area and report deviations.

**Result:** PM gets early visibility into progress problems.


## PO-05 — Monitor Project Phases

**Goal:** Track phase status.

**Main flow:** Review dates/status/completion/milestones/deliverables/issues/comments for each phase.

**Result:** Phase-level delays are visible.


## PO-06 — Monitor Milestones

**Goal:** Track milestone achievement.

**Main flow:** Review status categories and related activities/deliverables; flag concerns.

**Result:** Milestone risks are reported promptly.


## PO-07 — Monitor Official Deadlines

**Goal:** Track major deadlines.

**Main flow:** Monitor project/phase/milestone/deliverable/review/revision/comment dates.

**Result:** Potential schedule breaches are visible.


## PO-08 — Identify Upcoming Deadlines

**Goal:** Find obligations due soon.

**Main flow:** Select period, filter due items and follow up as authorized.

**Result:** Upcoming work receives attention.


## PO-09 — Identify Overdue Items

**Goal:** Find past-due obligations.

**Main flow:** Review owner/due date/delay, add monitoring note and report/escalate significant delays.

**Result:** Delayed work is systematically tracked.


## PO-10 — Monitor Project Activities

**Goal:** Follow activity execution.

**Main flow:** View statuses and identify activities affecting schedule/deliverables.

**Result:** Execution problems become visible.


## PO-11 — Monitor Activity Dependencies

**Goal:** Find delays caused by prerequisites.

**Main flow:** Inspect blocked activities and predecessor causes; report significant issues.

**Result:** Dependency problems are surfaced.


## PO-12 — View Required Deliverables

**Goal:** Maintain deliverable overview.

**Main flow:** View deliverable/phase/owner/deadline/version/submission/review/approval status.

**Result:** Delivery obligations are centrally visible.


## PO-13 — Monitor Deliverable Preparation

**Goal:** Track deliverables before submission.

**Main flow:** Review lifecycle status and identify at-risk items.

**Result:** Potential late submissions are identified.


## PO-14 — Monitor Deliverable Submissions

**Goal:** Verify formal submissions.

**Main flow:** Check submitter/date/version/reviewer/status and identify missing submissions.

**Result:** Late or missing submissions can be followed up.


## PO-15 — Monitor Deliverables Awaiting Review

**Goal:** Identify review backlog.

**Main flow:** Review submission/reviewer/elapsed review time and flag excessive delays.

**Result:** Review bottlenecks become visible.


## PO-16 — Monitor Deliverable Revisions

**Goal:** Track revision cycles.

**Main flow:** Review request date, owner, deadline, comments and resubmission status.

**Result:** Revisions are followed end-to-end.


## PO-17 — View Recently Uploaded Outputs

**Goal:** Track new project content.

**Main flow:** Filter uploads by date/uploader/phase/entity/deliverable/category and inspect metadata/status.

**Result:** Incoming information is visible.


## PO-18 — Check Project Structure Completeness

**Goal:** Detect missing required content.

**Main flow:** Compare expected vs existing forms/files/deliverables and report gaps.

**Result:** Structural gaps are systematically identified.


## PO-19 — Check Form Completion Status

**Goal:** Monitor structured data completeness.

**Main flow:** Identify complete/partial/invalid/unsubmitted/locked forms.

**Result:** Data completeness is part of monitoring.


## PO-20 — Perform Preliminary Completeness Review

**Goal:** Check obvious completeness defects before PM review.

**Main flow:** Verify required files/fields/template/metadata/supporting materials and report findings.

**Result:** Basic defects are caught before formal review.


## PO-21 — Monitor Project Manager Review Queue

**Goal:** Help PM manage pending decisions.

**Main flow:** View deliverables, responses, escalations, completion and extension requests awaiting PM attention.

**Result:** PM workload is visible.


## PO-22 — Monitor Technical Review Status

**Goal:** Track technical review progress.

**Main flow:** View awaiting/in-progress/comments/revision/recommendation/sign-off states.

**Result:** Technical review is incorporated into project monitoring.


## PO-23 — Monitor External Review Comments

**Goal:** Track reviewer feedback.

**Main flow:** Filter comments by reviewer/deliverable/phase/entity/severity/owner/status/age.

**Result:** External comments remain visible.


## PO-24 — Monitor Unresolved Comments

**Goal:** Identify comments still requiring action.

**Main flow:** Review open/major/awaiting-response/awaiting-verification/overdue indicators.

**Result:** Outstanding feedback is followed.


## PO-25 — Track Comment Resolution Progress

**Goal:** Detect stalled comment workflows.

**Main flow:** Review assignment/response/revision/verification stages and report stalls.

**Result:** Comment closure delays are identified.


## PO-26 — Add an Internal Monitoring Note

**Goal:** Record a monitoring observation without creating formal review feedback.

**Main flow:** Attach internal note to project item with appropriate visibility.

**Result:** Monitoring observations are captured separately from formal comments.


## PO-27 — Flag an Item for Project Manager Attention

**Goal:** Route an important finding to the PM.

**Main flow:** Select item, add explanation/priority and flag.

**Result:** PM is notified of an item requiring intervention.


## PO-28 — Report a Delay to the Project Manager

**Goal:** Provide structured delay information.

**Main flow:** Record planned date/current status/delay/responsible party/cause and send to PM.

**Result:** PM receives evidence-based delay information.


## PO-29 — Flag an At-Risk Milestone or Deliverable

**Goal:** Warn before an item becomes overdue.

**Main flow:** Use indicators such as low completion, prerequisites, unresolved major comments or inactivity and flag.

**Result:** PM receives early warning.


## PO-30 — Record a Monitoring Issue

**Goal:** Capture an operational monitoring issue.

**Main flow:** Record description/area/severity/responsible party/evidence and route to PM.

**Result:** Monitoring issues become trackable.


## PO-31 — Follow Up on Outstanding Action

**Goal:** Check whether requested action is complete.

**Main flow:** Review owner/deadline/status, send reminder if authorized and update note.

**Result:** Outstanding actions are actively followed.


## PO-32 — Send Reminder to Project Participant

**Goal:** Remind users about obligations.

**Main flow:** Send delegated reminders for deadlines, comments, reviews, activities or milestones.

**Result:** Routine follow-up can be delegated.


## PO-33 — Send Message to Contractor Project Leader

**Goal:** Request status or follow up execution.

**Main flow:** Send contextual message linked to deliverable/milestone/activity/comment.

**Result:** Monitoring communication is traceable.


## PO-34 — Communicate with Project Manager

**Goal:** Report findings or request decisions.

**Main flow:** Send message/summary with supporting project links.

**Result:** Monitoring directly supports PM decisions.


## PO-35 — Receive Project Monitoring Notifications

**Goal:** Receive relevant project events.

**Main flow:** Receive notifications for submissions, deadlines, revisions, reviews, phase changes, completion requests and escalations.

**Result:** Officer can react without manually inspecting everything.


## PO-36 — View Pending Monitoring Actions

**Goal:** Prioritize follow-up workload.

**Main flow:** View overdue deliverables, milestones, comments, delayed reviews, incomplete structures and flagged items.

**Result:** Officer can prioritize monitoring.


## PO-37 — Prepare Project Status Summary

**Goal:** Create concise status overview.

**Main flow:** Summarize progress, phase, milestones, deliverables, delays, comments, reviews, issues and deadlines.

**Result:** PM receives current operational summary.


## PO-38 — Generate Project Progress Report

**Goal:** Produce formal progress report.

**Main flow:** Include planned vs actual progress, phases, activities, milestones, deliverables, overdue work and issues.

**Result:** Progress can be communicated consistently.


## PO-39 — Generate Deadline and Milestone Report

**Goal:** Report schedule performance.

**Main flow:** Generate planned/current dates, statuses and delays for milestones/deliverables/phases.

**Result:** Schedule performance is visible.


## PO-40 — Generate Deliverable Status Report

**Goal:** Summarize deliverables.

**Main flow:** Report phase/owner/deadline/version/submission/reviewer/approval/delay.

**Result:** PM gets consolidated delivery view.


## PO-41 — Generate Comment Status Report

**Goal:** Summarize review-comment workload.

**Main flow:** Report reviewer/deliverable/severity/owner/date/deadline/status/age.

**Result:** Long-running review issues are visible.


## PO-42 — Generate Pending Review Report

**Goal:** Identify review bottlenecks.

**Main flow:** List items awaiting PM/Technical Reviewer/other reviewer with age and owner.

**Result:** Review backlogs can be managed.


## PO-43 — Generate Project Completeness Report

**Goal:** Report missing/incomplete project content.

**Main flow:** List missing forms/deliverables/diagrams/attachments/entities and validation issues.

**Result:** Completeness becomes measurable.


## PO-44 — Generate Contractor Performance Monitoring Summary

**Goal:** Summarize observable delivery performance.

**Main flow:** Use indicators such as on-time submissions, overdue items, revision frequency, response time and unresolved comments.

**Result:** PM receives evidence for contractor oversight.


## PO-45 — View Project Activity Timeline

**Goal:** Inspect chronological project events.

**Main flow:** Review submissions, reviews, comments, revisions and milestone changes.

**Result:** Current state can be reconstructed.


## PO-46 — View Relevant Audit History

**Goal:** Check who performed important actions.

**Main flow:** Inspect uploads/submissions/status/deadline/comment/review/approval/assignment changes as permitted.

**Result:** Monitoring findings can be supported by audit data.


## PO-47 — Monitor Deadline Changes

**Goal:** Track schedule modifications.

**Main flow:** Compare original/revised dates, change date, reason and authorizer.

**Result:** Reports reflect current and historical plans.


## PO-48 — Monitor Scope or Requirement Changes

**Goal:** Identify changes that affect delivery.

**Main flow:** Review changes to deliverables/structure/milestones/requirements and report impacts.

**Result:** Monitoring accounts for approved change.


## PO-49 — Monitor Phase Completion Readiness

**Goal:** Assess whether a phase appears ready for closure.

**Main flow:** Check activities/deliverables/comments/technical review/missing content/milestones.

**Result:** PM receives a readiness assessment.


## PO-50 — Review Contractor Phase Completion Request

**Goal:** Perform initial completeness check on contractor request.

**Main flow:** Review supporting items, identify missing obligations and prepare summary for PM.

**Result:** PM receives structured preliminary assessment.


## PO-51 — Monitor Project Completion Readiness

**Goal:** Assess readiness for project closure.

**Main flow:** Check deliverables/approvals/comments/issues/forms/reviews/completion requests.

**Result:** PM can decide using consolidated information.


## PO-52 — Prepare Project Completion Monitoring Summary

**Goal:** Prepare final monitoring summary.

**Main flow:** Summarize completion, outstanding items, approvals, exceptions, milestones, reviews and issues.

**Result:** Formal closure is supported by evidence.


# Technical Reviewer

**Role definition:** Independently evaluates technical quality, correctness, completeness and compliance, provides technical comments and review outcomes, and may sign off when contractually authorized.


**Scenario count:** 30


## TR-01 — Access an Assigned Project

**Goal:** Access project areas assigned for technical oversight.

**Main flow:** Open assigned project and navigate permitted phases/services/processes/deliverables/documents.

**Result:** Reviewer can inspect assigned technical scope.


## TR-02 — View Project Technical Status

**Goal:** Understand current technical-review workload.

**Main flow:** Review current phase, technical milestones, awaiting reviews, outstanding comments, revisions and overdue reviews.

**Result:** Reviewer can prioritize work.


## TR-03 — Access a Technical Deliverable

**Goal:** Open a submission for technical review.

**Main flow:** Review metadata, owner, status, phase/milestone, files, structured data and prior review history.

**Result:** Reviewer has evidence needed for assessment.


## TR-04 — Review Technical Content

**Goal:** Assess correctness, completeness and compliance.

**Main flow:** Evaluate against technical requirements, standards, contract, objectives and approved methods; record findings.

**Result:** A technical assessment is completed.


## TR-05 — Add a Technical Comment

**Goal:** Record technical observation or required correction.

**Main flow:** Attach comment to relevant item with category/severity/owner/date/requirement as applicable.

**Result:** Technical feedback becomes traceable.


## TR-06 — Classify Comment Severity

**Goal:** Prioritize review findings.

**Main flow:** Set severity such as Critical/Major/Minor/Recommendation/Informational.

**Result:** Project participants can prioritize corrective work.


## TR-07 — Request Technical Clarification

**Goal:** Ask for more information without necessarily requiring a new version.

**Main flow:** Create clarification, assign to appropriate party, review response and close/reopen as needed.

**Result:** Technical ambiguity is resolved.


## TR-08 — Request Revision of a Deliverable

**Goal:** Formally require technical correction.

**Main flow:** Record issues, choose revision outcome, optionally set deadline and notify PM/contractor.

**Result:** Deliverable enters revision cycle.


## TR-09 — Review a Revised Deliverable

**Goal:** Verify corrections.

**Main flow:** Compare current version with prior version/comments/responses and add new findings if needed.

**Result:** Revised work is reassessed.


## TR-10 — Compare Deliverable Versions

**Goal:** Understand changes between submissions.

**Main flow:** Select versions and inspect changed files/form values/diagrams/metadata using available comparison support.

**Result:** Reviewer can verify requested revisions.


## TR-11 — Respond to a Team Member's Comment Reply

**Goal:** Continue a technical discussion.

**Main flow:** Review reply and accept explanation, request clarification or maintain objection.

**Result:** Discussion remains contextual and traceable.


## TR-12 — Resolve a Technical Comment

**Goal:** Confirm an issue is satisfactorily addressed.

**Main flow:** Review correction/explanation and mark resolved with reviewer/date/version.

**Result:** Issue is formally closed.


## TR-13 — Reopen a Technical Comment

**Goal:** Restore an issue when correction is insufficient.

**Main flow:** Reopen resolved comment, provide reason and notify relevant users.

**Result:** Issue returns to active review.


## TR-14 — Monitor Outstanding Technical Comments

**Goal:** Track unresolved technical issues.

**Main flow:** Filter by phase/entity/deliverable/owner/severity/age/status.

**Result:** Findings are systematically monitored.


## TR-15 — Recommend Approval

**Goal:** Indicate technical acceptability.

**Main flow:** Verify mandatory issues resolved, record optional summary and recommend approval.

**Result:** Technical acceptance recommendation is recorded.


## TR-16 — Recommend Conditional Approval

**Goal:** Accept substantially complete work subject to conditions.

**Main flow:** Define remaining conditions and whether follow-up review is required.

**Result:** Decision records explicit technical conditions.


## TR-17 — Recommend Rejection or Major Revision

**Goal:** Indicate substantial technical deficiencies.

**Main flow:** Document reasons and select Major Revision Required/Not Technically Acceptable.

**Result:** Deliverable does not proceed to technical acceptance.


## TR-18 — Provide Formal Technical Sign-Off

**Goal:** Certify technical acceptance when contractually authorized.

**Main flow:** Review final version, verify mandatory comments, sign off and record identity/date/version/statement.

**Result:** Formal technical endorsement is recorded.


## TR-19 — Submit a Technical Review Summary

**Goal:** Provide overall assessment of reviewed scope.

**Main flow:** Summarize scope, findings, unresolved concerns, recommendations and conclusion.

**Result:** Project retains a formal technical assessment.


## TR-20 — Produce a Technical Review Report

**Goal:** Generate formal technical-review report.

**Main flow:** Include project/review period/deliverables/findings/severity/resolution/recommendations/acceptance status.

**Result:** Technical oversight is documentable.


## TR-21 — Monitor Technical Milestones

**Goal:** Track milestones relevant to technical oversight.

**Main flow:** Review dates, related deliverables, completion and unresolved technical issues; flag concerns.

**Result:** Technical risks to milestones are visible.


## TR-22 — Flag a Technical Risk

**Goal:** Raise a potential technical threat.

**Main flow:** Record description/severity/impact/related area/recommendation and route to PM.

**Result:** Technical risks become visible to management.


## TR-23 — Escalate a Critical Technical Issue

**Goal:** Raise a serious technical deficiency.

**Main flow:** Mark critical, justify, choose recipients and keep highlighted until addressed.

**Result:** Critical technical problems receive immediate attention.


## TR-24 — Communicate with the Project Manager

**Goal:** Discuss technical findings.

**Main flow:** Send contextual message linked to deliverable/milestone/comment/entity.

**Result:** Technical coordination is documented.


## TR-25 — Communicate with a Project Team Member

**Goal:** Request clarification/discuss assigned technical issue.

**Main flow:** Send contextual message and retain discussion with related project object.

**Result:** Technical questions can be resolved efficiently.


## TR-26 — Receive Notification of Review Assignment

**Goal:** Know when technical action is required.

**Main flow:** Receive notifications for submissions, revisions, replies, deadlines, escalations and requested assessments.

**Result:** Review responsibilities are not missed.


## TR-27 — View Technical Review History

**Goal:** Inspect prior technical-review decisions.

**Main flow:** View versions, outcomes, reviewers, comments, responses, resolutions and sign-offs.

**Result:** Technical decision history is traceable.


## TR-28 — View Relevant Project Activity History

**Goal:** Understand changes affecting technical assessment.

**Main flow:** Inspect submissions, versions, phase/requirement changes, comment resolution and approvals.

**Result:** Reviewer understands context.


## TR-29 — Search and Filter Technical Review Items

**Goal:** Locate technical-review information in large projects.

**Main flow:** Search/filter by deliverable/service/process/phase/status/person/severity/outcome/date.

**Result:** Review workload remains manageable.


## TR-30 — View Technical Review Dashboard

**Goal:** Obtain consolidated technical oversight view.

**Main flow:** See awaiting/overdue reviews, open critical/major comments, revisions, recommendations and upcoming milestones.

**Result:** Reviewer can prioritize technical oversight.


# Contractor Project Leader

**Role definition:** Leads contractor-side execution, team coordination, internal planning/QA, formal submissions, review-response coordination, schedule monitoring and contractor reporting.


**Scenario count:** 66


## CPL-01 — Access Assigned Project

**Goal:** Access project areas assigned to the contractor.

**Main flow:** Open assigned project and view scope, phases, milestones, deliverables, team, comments and deadlines.

**Result:** Leader can manage contractor-side execution.


## CPL-02 — View Contractor Project Dashboard

**Goal:** Obtain contractor-side execution overview.

**Main flow:** Review progress, phase, upcoming/overdue deliverables, internal/external reviews, comments, workload, blockers and milestones.

**Result:** Leader sees areas needing attention.


## CPL-03 — View Assigned Contractor Scope

**Goal:** Understand contractor responsibilities.

**Main flow:** Review assigned phases/workstreams/services/processes/activities/deliverables plus requirements/templates/deadlines/reviewers.

**Result:** Contractor obligations are explicit.


## CPL-04 — Add Contractor Team Members

**Goal:** Establish delivery team.

**Main flow:** Select/request users, assign contractor roles and participation dates.

**Result:** Contractor users can participate.


## CPL-05 — Remove a Contractor Team Member

**Goal:** Remove a departing member safely.

**Main flow:** Review assignments, reassign open work, remove access while retaining attribution.

**Result:** Responsibilities remain complete.


## CPL-06 — Define Contractor-Side Roles

**Goal:** Define operational responsibility profiles.

**Main flow:** Assign allowed contractor roles such as analyst/specialist/internal reviewer/contributor.

**Result:** Team responsibilities are clear.


## CPL-07 — Assign Team Members to Project Areas

**Goal:** Allocate personnel to specific scope.

**Main flow:** Assign users to phase/workstream/service/process/activity/deliverable with responsibility type.

**Result:** Ownership is traceable.


## CPL-08 — Define Contractor Work Plan

**Goal:** Translate official requirements into contractor execution plan.

**Main flow:** Review phases/milestones/deliverables/deadlines, create internal activities, owners/dependencies/internal dates and activate plan.

**Result:** Team has an executable plan.


## CPL-09 — Create Internal Contractor Activity

**Goal:** Define internal task.

**Main flow:** Create task with title/scope/owner/collaborators/dates/priority/dependencies.

**Result:** Internal work becomes trackable.


## CPL-10 — Assign an Activity

**Goal:** Assign contractor activity ownership.

**Main flow:** Choose responsible member/contributors/reviewer, confirm deadline and notify.

**Result:** Activity ownership is explicit.


## CPL-11 — Reassign Contractor Work

**Goal:** Transfer responsibility.

**Main flow:** Select activity/deliverable, review progress, choose new owner and record reason.

**Result:** Work continues without losing history.


## CPL-12 — Define Activity Dependencies

**Goal:** Represent contractor task sequencing.

**Main flow:** Add predecessor/successor relations and validate no cycles.

**Result:** Blocked/downstream activities can be identified.


## CPL-13 — Monitor Contractor Activities

**Goal:** Track contractor-side work.

**Main flow:** Filter activities by status/member/phase/entity/priority/date and intervene as needed.

**Result:** Execution deviation is visible.


## CPL-14 — Update Contractor Activity Status

**Goal:** Maintain accurate execution state.

**Main flow:** Review/update status/progress; require explanation for blocked/overdue states where configured.

**Result:** Dashboard reflects current work.


## CPL-15 — Monitor Team Workload

**Goal:** Balance contractor resources.

**Main flow:** Compare active/overdue/deliverable/review workloads and reassign as needed.

**Result:** Workload can be balanced.


## CPL-16 — View Required Deliverables

**Goal:** Understand formal contractor outputs.

**Main flow:** View deliverable/type/phase/milestone/owner/template/deadline/submission/review status.

**Result:** Delivery obligations are visible.


## CPL-17 — Assign Deliverable Owner

**Goal:** Assign production responsibility.

**Main flow:** Choose owner/contributors/internal reviewer and internal completion date before official deadline.

**Result:** Deliverable responsibility is explicit.


## CPL-18 — Monitor Deliverable Preparation

**Goal:** Track deliverable readiness.

**Main flow:** Review lifecycle from not-started through internal review/submission/revision/acceptance.

**Result:** At-risk deliverables are visible.


## CPL-19 — Review Contractor Output Internally

**Goal:** Perform contractor-side QA before formal submission.

**Main flow:** Review completeness, technical consistency, template compliance, attachments, form data and requirements.

**Result:** Poor-quality output is caught internally.


## CPL-20 — Return Internal Output for Correction

**Goal:** Require contractor-side correction.

**Main flow:** Add internal comments, return to owner, set internal deadline and notify.

**Result:** Output remains internal until acceptable.


## CPL-21 — Mark Deliverable Ready for Submission

**Goal:** Confirm internal checks are complete.

**Main flow:** Review final draft, verify completeness and mark ready, recording reviewer/version.

**Result:** Deliverable can proceed to formal submission.


## CPL-22 — Submit Deliverable

**Goal:** Formally submit contractor output.

**Main flow:** Review package, add note, submit to designated reviewer(s), record version/submitter/date/recipients.

**Result:** Deliverable enters external review.


## CPL-23 — Withdraw a Submission

**Goal:** Correct an accidental/invalid submission when permitted.

**Main flow:** Request withdrawal, provide reason, system checks review state and returns to preparation if allowed.

**Result:** Incorrect submission can be corrected without deleting history.


## CPL-24 — Monitor Submitted Deliverables

**Goal:** Track external review.

**Main flow:** View submission date/reviewer/status/elapsed time/comments/clarifications/approval.

**Result:** Leader knows where each deliverable stands.


## CPL-25 — Receive External Review Comments

**Goal:** Receive and organize reviewer feedback.

**Main flow:** Open review package and group comments by deliverable/item/severity/reviewer.

**Result:** External feedback becomes contractor work.


## CPL-26 — Assign Review Comment to Team Member

**Goal:** Delegate correction.

**Main flow:** Select unresolved comment, assign responsible user/deadline/instructions and notify.

**Result:** Each comment has an accountable resolver.


## CPL-27 — Monitor Comment Resolution

**Goal:** Track external findings to closure.

**Main flow:** Review open/severity/assignment/response/verification/overdue indicators.

**Result:** Review findings do not get lost.


## CPL-28 — Review Team Response to Comment

**Goal:** QA contractor response before external return.

**Main flow:** Review response/revised content/evidence and approve or return for further correction.

**Result:** External responses remain controlled.


## CPL-29 — Respond to Technical Reviewer Comment

**Goal:** Formally answer technical finding.

**Main flow:** Review correction, add response, reference revised version and submit to reviewer.

**Result:** Reviewer can verify resolution.


## CPL-30 — Respond to Project Manager Comment

**Goal:** Address PM feedback.

**Main flow:** Coordinate action, provide response/revised content and submit.

**Result:** PM feedback is formally addressed.


## CPL-31 — Coordinate Deliverable Revision

**Goal:** Manage a formal revision cycle.

**Main flow:** Review comments, assign corrections, track progress, internal-review revised output and prepare resubmission.

**Result:** Revision is coordinated as a work package.


## CPL-32 — Resubmit Revised Deliverable

**Goal:** Submit corrected version.

**Main flow:** Verify mandatory comments addressed, review version, add resubmission summary and submit linked to prior version/comments.

**Result:** Revised deliverable re-enters external review.


## CPL-33 — View Deliverable Version History

**Goal:** Trace deliverable evolution.

**Main flow:** View version/date/author/submission/review/comments/revision reasons.

**Result:** Delivery history is transparent.


## CPL-34 — Monitor Project Structure Completeness

**Goal:** Ensure required content exists across assigned hierarchy.

**Main flow:** Check expected forms/files/deliverables and assign corrective work for gaps.

**Result:** Structural gaps are identified before submission.


## CPL-35 — Monitor Form Completion

**Goal:** Ensure required structured information is complete.

**Main flow:** Review complete/partial/missing/invalid/unsubmitted/locked forms.

**Result:** Structured data readiness is visible.


## CPL-36 — Monitor Uploaded Files and Outputs

**Goal:** Supervise contractor-generated content.

**Main flow:** Filter by uploader/phase/entity/category/deliverable/date/status.

**Result:** Leader maintains visibility over outputs.


## CPL-37 — Identify Misplaced or Incorrect Content

**Goal:** Correct organizational errors.

**Main flow:** Move/reclassify if permitted or request correction, retaining audit trail.

**Result:** Repository stays organized.


## CPL-38 — Supervise Data Import

**Goal:** Control contractor-side imports.

**Main flow:** Review source/profile/destination/mapping summary and confirm where required.

**Result:** Large datasets can be imported under oversight.


## CPL-39 — Review Import Validation Errors

**Goal:** Resolve invalid import records.

**Main flow:** Review missing/invalid/duplicate/relationship/type errors, assign correction and revalidate.

**Result:** Invalid data is stopped.


## CPL-40 — Resolve Import Conflicts

**Goal:** Decide how to handle conflicting imported data.

**Main flow:** Choose merge/replace/skip/create-new/escalate according to policy.

**Result:** Conflicts are consistently resolved.


## CPL-41 — Monitor Official Deadlines

**Goal:** Track contractual/project dates.

**Main flow:** Monitor phase/milestone/deliverable/revision/comment/review dates.

**Result:** Time-sensitive work can be prioritized.


## CPL-42 — Define Internal Deadlines

**Goal:** Set contractor buffer dates.

**Main flow:** Define draft/internal-review/ready-for-submission dates before official deadline.

**Result:** Contractor has operational schedule buffer.


## CPL-43 — Request Deadline Extension

**Goal:** Seek formal schedule change.

**Main flow:** Select item, propose new date, state reason/impact/mitigation and send to PM.

**Result:** Schedule changes remain governed.


## CPL-44 — Monitor Project Progress

**Goal:** Assess contractor-side completion.

**Main flow:** Review progress by phase/service/process/activity/deliverable/member.

**Result:** Underperforming areas are visible.


## CPL-45 — Identify At-Risk Work

**Goal:** Detect likely schedule/quality failure.

**Main flow:** Use overdue prerequisites, low progress, unresolved comments, repeated revisions, workload and missing content signals.

**Result:** Leader can intervene early.


## CPL-46 — Record Contractor Project Risk

**Goal:** Track potential delivery risk.

**Main flow:** Record description/likelihood/impact/severity/owner/mitigation/date and association.

**Result:** Delivery risks are managed.


## CPL-47 — Record Contractor Issue

**Goal:** Track active delivery problem.

**Main flow:** Record issue, owner, action and deadline.

**Result:** Delivery problems are managed.


## CPL-48 — Escalate a Risk or Issue to Project Manager

**Goal:** Raise significant issue outside contractor control.

**Main flow:** Add explanation/required action and submit escalation to PM.

**Result:** Governance intervention can occur.


## CPL-49 — Request Clarification from Project Manager

**Goal:** Clarify scope/schedule/management requirements.

**Main flow:** Create contextual request, send to PM, track response and resolve.

**Result:** Ambiguity is formally resolved.


## CPL-50 — Request Technical Clarification

**Goal:** Seek technical guidance.

**Main flow:** Raise contextual question to Technical Reviewer and retain response/history.

**Result:** Technical ambiguity is reduced.


## CPL-51 — Send Message to Contractor Team Member

**Goal:** Give execution instructions.

**Main flow:** Send contextual message linked to work item.

**Result:** Contractor communication remains traceable.


## CPL-52 — Send Contractor Team Announcement

**Goal:** Broadcast contractor-side information.

**Main flow:** Send internal deadline/submission/review/phase/urgent instruction announcement.

**Result:** Team receives consistent updates.


## CPL-53 — Communicate with Project Manager

**Goal:** Coordinate contractor/client management matters.

**Main flow:** Discuss status, schedule, clarification, extensions, escalations and submissions in context.

**Result:** Coordination is captured.


## CPL-54 — Communicate with Technical Reviewer

**Goal:** Coordinate technical review matters.

**Main flow:** Discuss comments, evidence, approaches and review timing.

**Result:** Technical communication is traceable.


## CPL-55 — Receive Project Notifications

**Goal:** Stay informed about events requiring action.

**Main flow:** Receive assignment/deadline/comment/revision/clarification/extension/milestone/escalation notifications.

**Result:** Important events are not missed.


## CPL-56 — Monitor Pending Contractor Actions

**Goal:** See all outstanding contractor obligations.

**Main flow:** Review internal reviews, comments, revisions, overdue activities and clarifications.

**Result:** Leader can prioritize unresolved work.


## CPL-57 — Generate Contractor Progress Report

**Goal:** Produce contractor execution summary.

**Main flow:** Include progress, phases, activities, deliverables, submissions, risks/issues, comments and workload.

**Result:** Delivery status can be formally communicated.


## CPL-58 — Generate Deliverable Readiness Report

**Goal:** Assess upcoming submission readiness.

**Main flow:** Report due date, completion, internal review and risk status.

**Result:** Leader can focus on vulnerable deliverables.


## CPL-59 — Generate Review Comment Status Report

**Goal:** Track external findings.

**Main flow:** Report reviewer/deliverable/severity/owner/status/deadline/age/revision.

**Result:** Review closure is manageable.


## CPL-60 — Generate Contractor Team Workload Report

**Goal:** Analyze resource distribution.

**Main flow:** Report active/overdue activities, deliverables, comments, internal reviews and deadlines per member.

**Result:** Resource allocation decisions are supported.


## CPL-61 — View Contractor Activity Timeline

**Goal:** Inspect contractor-side chronological events.

**Main flow:** View uploads, internal reviews, submissions, comments, assignments, revisions and approvals.

**Result:** Delivery history is traceable.


## CPL-62 — Review Contractor Audit History

**Goal:** Inspect important contractor actions.

**Main flow:** Review assignments/uploads/form changes/submissions/comments/responses/resubmissions/internal approvals.

**Result:** Accountability is supported.


## CPL-63 — Prepare Project Phase for Contractor Completion

**Goal:** Check contractor obligations for phase.

**Main flow:** Verify activities/forms/files/deliverables/comments and resolve remaining items.

**Result:** Contractor scope is ready for phase completion.


## CPL-64 — Submit Phase Completion Request

**Goal:** Ask PM to formally close/approve phase.

**Main flow:** Confirm readiness, add summary and submit request.

**Result:** Formal phase completion stays a governance action.


## CPL-65 — Prepare Contractor Project Completion

**Goal:** Verify all contractor obligations before final completion.

**Main flow:** Check deliverables/revisions/comments/activities/forms/files/risks/issues.

**Result:** Outstanding obligations are identified.


## CPL-66 — Submit Contractor Completion Statement

**Goal:** Declare contractor-side obligations complete.

**Main flow:** Complete final review, add completion statement/report and submit to PM.

**Result:** Contractor completion is formally recorded.


# Contractor Team Member

**Role definition:** Executes assigned contractor work, completes forms, uses the repository, uploads outputs/deliverables, responds to comments, performs corrections and tracks personal work.


**Scenario count:** 70


## CTM-01 — Access Assigned Project

**Goal:** Access project areas relevant to assigned work.

**Main flow:** Open assigned project and navigate permitted phases/activities/deliverables/forms/repository.

**Result:** User can begin assigned work.


## CTM-02 — View Personal Project Workspace

**Goal:** See current personal responsibilities.

**Main flow:** View assigned activities/deliverables/deadlines/overdue items/reviews/comments/notifications/materials.

**Result:** User can prioritize work.


## CTM-03 — View Assigned Project Scope

**Goal:** Understand assigned parts of the project.

**Main flow:** Review assigned phases/services/processes/entities/activities/deliverables plus instructions/deadlines.

**Result:** Work boundaries are clear.


## CTM-04 — View Assigned Activities

**Goal:** See all owned project activities.

**Main flow:** View title/scope/phase/priority/dates/dependencies/deliverable/status.

**Result:** Assigned work is organized.


## CTM-05 — Start an Assigned Activity

**Goal:** Indicate work has begun.

**Main flow:** Open activity, review prerequisites and change status to In Progress.

**Result:** Leader sees execution has started.


## CTM-06 — Update Activity Progress

**Goal:** Keep work status current.

**Main flow:** Update status/progress/notes/expected completion where permitted.

**Result:** Monitoring reflects actual progress.


## CTM-07 — Mark Activity as Blocked

**Goal:** Report inability to continue.

**Main flow:** Set Blocked, provide reason/dependency/help needed and notify leader.

**Result:** Blocking issue becomes visible.


## CTM-08 — Mark Activity Complete

**Goal:** Indicate assigned activity is done.

**Main flow:** Ensure outputs uploaded and mark complete/ready for review.

**Result:** Dependent work/review can proceed.


## CTM-09 — Browse Project Repository

**Goal:** Access materials needed for work.

**Main flow:** Navigate permitted hierarchy and browse documents/templates/data/diagrams/approved outputs.

**Result:** Reference material is accessible.


## CTM-10 — Search Project Repository

**Goal:** Locate materials efficiently.

**Main flow:** Search/filter by title/file/category/phase/entity/uploader/date/type/tag.

**Result:** Files can be found quickly.


## CTM-11 — Download Project Material

**Goal:** Obtain a permitted file.

**Main flow:** Select file, inspect metadata/version and download.

**Result:** User can work with project material.


## CTM-12 — Preview Project Material

**Goal:** Inspect supported file in-app.

**Main flow:** Open preview then download if needed.

**Result:** Unnecessary downloads are reduced.


## CTM-13 — Upload Project Material

**Goal:** Add working/supporting content.

**Main flow:** Choose target, file and required metadata; validate type/size and upload.

**Result:** Material is added to repository.


## CTM-14 — Upload File into Correct Project Structure

**Goal:** Associate content with proper project object.

**Main flow:** Choose phase/service/process/deliverable/entity target and upload.

**Result:** Repository remains contextually organized.


## CTM-15 — Replace or Upload New Version of Own File

**Goal:** Update own file without losing history.

**Main flow:** Open existing file, upload new version and optional note.

**Result:** Current content updates with history retained.


## CTM-16 — View File Version History

**Goal:** Inspect earlier file versions.

**Main flow:** View version/uploader/date/note/review status.

**Result:** File evolution is transparent.


## CTM-17 — Correct File Metadata

**Goal:** Fix metadata of own file.

**Main flow:** Edit permitted metadata and save.

**Result:** Repository information stays accurate.


## CTM-18 — View Assigned Deliverables

**Goal:** See formal outputs assigned to user.

**Main flow:** View title/phase/template/dates/format/status/internal/external reviewer.

**Result:** Deliverable responsibility is clear.


## CTM-19 — Download Deliverable Template

**Goal:** Get required template.

**Main flow:** Open deliverable and download current approved template/version.

**Result:** Correct format is used.


## CTM-20 — Upload Draft Deliverable

**Goal:** Store a working deliverable version.

**Main flow:** Upload draft/supporting files and save as draft.

**Result:** Draft work is captured.


## CTM-21 — Update Deliverable Metadata

**Goal:** Complete permitted deliverable information.

**Main flow:** Edit title/description/reporting period/related entity/notes/references as allowed.

**Result:** Metadata is complete.


## CTM-22 — Add Supporting Files to Deliverable

**Goal:** Attach evidence/diagrams/spreadsheets/appendices.

**Main flow:** Upload one or more permitted supporting files with metadata.

**Result:** Submission package is complete.


## CTM-23 — Save Deliverable as Draft

**Goal:** Preserve incomplete work.

**Main flow:** Save without sending for review.

**Result:** Deliverable remains editable.


## CTM-24 — Mark Deliverable Ready for Internal Review

**Goal:** Notify contractor leadership work is ready.

**Main flow:** Validate required fields/files and mark Ready for Internal Review.

**Result:** Internal reviewer is notified.


## CTM-25 — Receive Internal Review Feedback

**Goal:** Receive contractor-side QA comments.

**Main flow:** Open notification/deliverable and review required corrections.

**Result:** User knows what to fix.


## CTM-26 — Correct Deliverable after Internal Review

**Goal:** Address internal feedback.

**Main flow:** Update files/content, respond and return for review.

**Result:** Deliverable progresses toward submission.


## CTM-27 — View Formal Submission Status

**Goal:** See lifecycle after contractor leader submission.

**Main flow:** View Draft/Internal Review/Ready/Submitted/Under Review/Revision/Approved state.

**Result:** User understands deliverable state.


## CTM-28 — Open Assigned Dynamic Form

**Goal:** Enter structured information.

**Main flow:** Open assigned entity, view inherited data and complete permitted fields.

**Result:** Structured data is captured.


## CTM-29 — Save Form as Draft

**Goal:** Preserve partial form work.

**Main flow:** Save incomplete data without formal review/submission.

**Result:** User can continue later.


## CTM-30 — Complete Required Form Fields

**Goal:** Make form valid.

**Main flow:** Enter required values, run validation and correct errors.

**Result:** Form reaches valid state.


## CTM-31 — Add Dynamic Table Rows

**Goal:** Enter repeating structured information.

**Main flow:** Add rows for configured tables such as stakeholders/risks/inputs/activities/services.

**Result:** Repeating data is captured structurally.


## CTM-32 — Upload Attachment to Form

**Goal:** Attach evidence/supporting file to form.

**Main flow:** Upload file to permitted form field/section.

**Result:** Data and evidence remain connected.


## CTM-33 — Submit Form for Internal Review

**Goal:** Mark structured information ready for contractor review.

**Main flow:** Validate form and select Ready for Review.

**Result:** Assigned reviewer is notified.


## CTM-34 — Revise Form after Review

**Goal:** Correct structured information.

**Main flow:** Review comments, edit permitted fields, respond and resubmit.

**Result:** Form content is corrected traceably.


## CTM-35 — Import Excel or CSV Data

**Goal:** Populate structured data from external file.

**Main flow:** Select target, upload file, choose approved import profile, preview mapping and confirm.

**Result:** External data enters through controlled import.


## CTM-36 — Preview Import Data

**Goal:** Inspect data before import.

**Main flow:** Review source rows, mappings, invalid values, duplicates and missing requirements.

**Result:** Problems can be caught early.


## CTM-37 — Correct Import Validation Errors

**Goal:** Fix invalid import records.

**Main flow:** Correct source data/permitted mappings and revalidate.

**Result:** Only valid records proceed.


## CTM-38 — Handle Import Conflict Assigned to User

**Goal:** Resolve duplicate/conflict according to permission.

**Main flow:** Choose skip/merge/replace or escalate to leader.

**Result:** Conflict is handled according to rules.


## CTM-39 — View Comments on Assigned Work

**Goal:** See feedback related to own work.

**Main flow:** View comments from leader/PM/officer/technical reviewer/other authorized reviewer.

**Result:** Relevant feedback is visible.


## CTM-40 — View Comment Details

**Goal:** Understand required action.

**Main flow:** Inspect author/date/item/version/severity/category/deadline/discussion/status.

**Result:** Review requirement is clear.


## CTM-41 — Respond to a Comment

**Goal:** Provide explanation or answer.

**Main flow:** Write response and optionally link corrected content/version.

**Result:** Reviewer can assess response.


## CTM-42 — Perform Correction for Assigned Comment

**Goal:** Modify work in response to feedback.

**Main flow:** Correct content, upload version if needed and explain change.

**Result:** Corrective action is ready for verification.


## CTM-43 — Mark Comment Action Ready for Verification

**Goal:** Notify reviewer correction is complete.

**Main flow:** Complete correction/response and mark Ready for Verification.

**Result:** Reviewer can verify; user does not self-resolve.


## CTM-44 — View Resolved Comments

**Goal:** Review historical feedback.

**Main flow:** Open resolved comments and associated decisions.

**Result:** Past review context remains available.


## CTM-45 — Respond to Reopened Comment

**Goal:** Address issue reopened by reviewer.

**Main flow:** Review reason, perform further correction and return for verification.

**Result:** Issue re-enters correction cycle.


## CTM-46 — Receive Revision Request

**Goal:** Be informed assigned deliverable needs external-review changes.

**Main flow:** Receive assigned revision actions/comments and open revision package.

**Result:** Corrective work can begin.


## CTM-47 — View Revision Package

**Goal:** Understand all changes required.

**Main flow:** View version/reviewer/outcome/comments/severity/deadline/discussion.

**Result:** Revision scope is clear.


## CTM-48 — Prepare Revised Deliverable

**Goal:** Create corrected version.

**Main flow:** Modify content/supporting files, upload revision and summarize changes.

**Result:** Revised output is ready for internal review.


## CTM-49 — Submit Revised Work for Internal Review

**Goal:** Return corrections to contractor leader.

**Main flow:** Verify assigned corrections and mark revision ready for internal review.

**Result:** Formal resubmission remains controlled by leader.


## CTM-50 — View Revision History

**Goal:** Trace prior review/correction cycles.

**Main flow:** View versions, comments, resubmissions and approval outcomes.

**Result:** Evolution of work is transparent.


## CTM-51 — View Notifications

**Goal:** See project events requiring attention.

**Main flow:** View assignments, deadline changes, comments, revisions, approvals and announcements.

**Result:** User is aware of relevant events.


## CTM-52 — Open Project Item from Notification

**Goal:** Navigate directly to related item.

**Main flow:** Select notification and open linked activity/comment/file/deliverable/entity.

**Result:** Notification-to-action is efficient.


## CTM-53 — Mark Notification as Read

**Goal:** Manage notification state.

**Main flow:** Mark individual/bulk notifications read as supported.

**Result:** New vs reviewed events are distinguishable.


## CTM-54 — View Unread / Action-Required Notifications

**Goal:** Prioritize important notifications.

**Main flow:** Filter unread/action-required items.

**Result:** Obligations are less likely to be missed.


## CTM-55 — Message Contractor Project Leader

**Goal:** Ask clarification/report progress/raise issue.

**Main flow:** Send contextual message linked to work item.

**Result:** Contractor communication remains traceable.


## CTM-56 — Ask for Clarification on Assigned Work

**Goal:** Resolve ambiguity.

**Main flow:** Create clarification request to leader/authorized reviewer and track response.

**Result:** Work does not rely on unresolved assumptions.


## CTM-57 — Respond to Project Message

**Goal:** Continue project discussion.

**Main flow:** Reply within contextual conversation.

**Result:** Communication history is retained.


## CTM-58 — View Contractor Team Announcement

**Goal:** Receive contractor-wide instructions.

**Main flow:** Read announcements about deadlines/submissions/reviews/phases/templates.

**Result:** Team receives consistent information.


## CTM-59 — View Personal Deadlines

**Goal:** See all dates relevant to user.

**Main flow:** View activity/internal deliverable/correction/comment/formal contextual deadlines.

**Result:** User can prioritize work.


## CTM-60 — View Overdue Personal Work

**Goal:** Identify past-due assignments.

**Main flow:** Filter/inspect overdue activities/deliverables/comments.

**Result:** User can address delays.


## CTM-61 — View Upcoming Personal Work

**Goal:** See work due soon.

**Main flow:** Select time window and view upcoming assignments.

**Result:** Short-term execution can be planned.


## CTM-62 — View Personal Work Status

**Goal:** Obtain personal workload overview.

**Main flow:** View active activities, deliverables, reviews, comments, revisions and overdue items.

**Result:** User understands current workload.


## CTM-63 — Report Delay or Delivery Risk

**Goal:** Warn contractor leader of likely delay.

**Main flow:** Record reason/impact/expected completion/help needed and send.

**Result:** Leadership gets early warning.


## CTM-64 — Report Blocking Issue

**Goal:** Escalate a condition preventing work.

**Main flow:** Describe missing data/dependency/access/requirement problem and route to leader.

**Result:** Blocker becomes visible.


## CTM-65 — View Own Upload History

**Goal:** Locate previous uploads.

**Main flow:** View files/deliverables uploaded by user and their statuses.

**Result:** Prior work is easy to find.


## CTM-66 — View Own Activity History

**Goal:** Review changes to assigned activities.

**Main flow:** View assignment/status/deadline/comment/completion events.

**Result:** Personal execution history is traceable.


## CTM-67 — View Deliverable Review History

**Goal:** Understand deliverable lifecycle.

**Main flow:** View submissions, internal/external reviews, comments, revisions and approvals.

**Result:** Review process is transparent.


## CTM-68 — View Who Reviewed an Output

**Goal:** Identify reviewer and authority.

**Main flow:** Open review metadata for deliverable/output.

**Result:** Origin of feedback is clear.


## CTM-69 — Complete Assigned Work Package

**Goal:** Confirm all work in a package is ready.

**Main flow:** Verify forms/files/comments/activities and mark package ready for leader review.

**Result:** Leader can assess package completion.


## CTM-70 — Complete Assigned Phase Work

**Goal:** Confirm personal obligations in a phase are finished.

**Main flow:** Review all assigned phase items, resolve remaining actions and mark complete.

**Result:** Leader can assess contractor phase readiness.


# Employer Representative

**Role definition:** Provides managerial oversight, comments on significant outputs, and gives formal acceptance for phases and the overall project.


**Scenario count:** 53


## ER-01 — Access Assigned Project

**Goal:** Access projects represented on behalf of the employer.

**Main flow:** Open assigned project and managerial workspace.

**Result:** Employer can oversee assigned project.


## ER-02 — View Managerial Project Dashboard

**Goal:** Obtain executive overview.

**Main flow:** Review overall progress, current phase, time, milestones, deliverables, technical issues and pending acceptances.

**Result:** Employer sees project health at managerial level.


## ER-03 — View Overall Project Progress

**Goal:** Monitor completion against agreed scope.

**Main flow:** View progress by project/phase/milestone/deliverable group and drill down as needed.

**Result:** Employer can compare actual execution with plan.


## ER-04 — Monitor Project Schedule

**Goal:** Understand schedule performance.

**Main flow:** Review project/phase dates, milestones, approved changes, overdue items and forecast completion.

**Result:** Significant schedule deviations are visible.


## ER-05 — View Project Phases

**Goal:** Review phase status.

**Main flow:** View objectives/dates/status/completion/milestones/deliverables/issues/acceptance.

**Result:** Phase-level performance is visible.


## ER-06 — View Milestone Status

**Goal:** Monitor major checkpoints.

**Main flow:** Review completed/upcoming/at-risk/overdue milestones and related outputs.

**Result:** Major commitments remain visible.


## ER-07 — View Deliverable Summary

**Goal:** Understand status of major outputs.

**Main flow:** View deliverable/phase/contractor/deadline/submission/PM review/technical review/version/status.

**Result:** Employer can monitor delivery obligations.


## ER-08 — View a Project Deliverable

**Goal:** Inspect a specific output.

**Main flow:** Review metadata/files/structured information/PM comments/technical findings/history/recommendations.

**Result:** Employer has evidence for decisions.


## ER-09 — Preview or Download Deliverable

**Goal:** Examine project outputs.

**Main flow:** Preview supported file or download it.

**Result:** Employer can independently inspect deliverables.


## ER-10 — View Deliverable Version History

**Goal:** Understand deliverable evolution.

**Main flow:** View versions, submissions, technical outcomes, PM decisions and comments.

**Result:** Final decisions can consider revision history.


## ER-11 — Add Comment to an Output

**Goal:** Provide employer-side feedback.

**Main flow:** Attach comment to deliverable/document/form/entity/phase output/milestone output with optional category/importance/responsibility.

**Result:** Employer feedback is formally recorded.


## ER-12 — Classify Employer Comment

**Goal:** Clarify significance of feedback.

**Main flow:** Classify as Observation/Clarification/Minor Correction/Mandatory Correction/Management Concern/Acceptance Condition.

**Result:** Response priority is clear.


## ER-13 — Request Clarification

**Goal:** Obtain explanation before decision.

**Main flow:** Create contextual clarification request to PM/authorized participant, review response and close/reopen.

**Result:** Employer decisions are better informed.


## ER-14 — View Response to Employer Comment

**Goal:** Assess response/correction.

**Main flow:** Review reply, correction and revised version as applicable.

**Result:** Employer can determine whether concern is addressed.


## ER-15 — Mark Employer Comment Resolved

**Goal:** Close satisfied employer concern.

**Main flow:** Review correction and mark resolved.

**Result:** Employer feedback is formally closed.


## ER-16 — Reopen Employer Comment

**Goal:** Restore unresolved concern.

**Main flow:** Reopen with reason and notify relevant users.

**Result:** Concern returns to active state.


## ER-17 — Monitor Outstanding Employer Comments

**Goal:** Track employer feedback awaiting action.

**Main flow:** View open/mandatory/awaiting-response/awaiting-verification indicators.

**Result:** Employer comments are not lost.


## ER-18 — View Technical Review Outcome

**Goal:** Consider technical assessment before acceptance.

**Main flow:** View status/comments/severity/unresolved issues/recommendation/conditional approval/sign-off.

**Result:** Acceptance can incorporate independent technical evidence.


## ER-19 — View Project Manager Recommendation

**Goal:** Review PM assessment before acceptance.

**Main flow:** View completion recommendation, approvals, exceptions, schedule and unresolved issues.

**Result:** Employer receives management evidence.


## ER-20 — View Outstanding Issues Before Acceptance

**Goal:** Identify unresolved matters that may block acceptance.

**Main flow:** Consolidate technical comments, employer comments, incomplete deliverables, overdue obligations, PM concerns, risks/issues and milestones.

**Result:** Acceptance decision has full exception visibility.


## ER-21 — Receive Phase Acceptance Request

**Goal:** Be notified a phase is ready for acceptance.

**Main flow:** Receive controlled package after contractor/PO/PM/technical review workflow.

**Result:** Employer can begin formal acceptance review.


## ER-22 — Review Phase Acceptance Package

**Goal:** Assess evidence for phase decision.

**Main flow:** Review scope, milestones, required/approved/outstanding deliverables, PM/technical recommendations, comments, exceptions and schedule.

**Result:** Employer has consolidated basis for decision.


## ER-23 — Accept a Project Phase

**Goal:** Formally confirm phase completion.

**Main flow:** Review package/exceptions, accept, optionally add statement, record representative/date/phase/versions.

**Result:** Phase acceptance is authoritative and traceable.


## ER-24 — Accept a Phase with Conditions

**Goal:** Allow progression subject to permitted conditions.

**Main flow:** Define conditions, responsible party, deadline and follow-up requirement, then confirm.

**Result:** Conditional acceptance creates explicit obligations.


## ER-25 — Reject Phase Acceptance Request

**Goal:** Decline acceptance due to deficiencies.

**Main flow:** Record reasons and notify PM/contractor.

**Result:** Phase remains unaccepted.


## ER-26 — View Phase Acceptance History

**Goal:** Review prior phase decisions.

**Main flow:** View acceptance/conditional/rejection dates, representative, conditions and closure.

**Result:** Contractual phase decisions are traceable.


## ER-27 — Receive Project Final Acceptance Request

**Goal:** Be notified project is ready for formal acceptance.

**Main flow:** Receive final request after PM recommendation/completion workflow.

**Result:** Final acceptance process begins.


## ER-28 — Review Project Completion Package

**Goal:** Assess fulfillment of project obligations.

**Main flow:** Review phases, deliverables, technical conclusions, PM recommendation, comments, risks/issues, contractor statement, schedule and final reports.

**Result:** Employer has consolidated final evidence.


## ER-29 — Verify Phase Acceptance Completion

**Goal:** Confirm all required phases are accepted.

**Main flow:** View accepted/conditional/unresolved/unaccepted phase states.

**Result:** Final acceptance cannot bypass incomplete phases.


## ER-30 — Verify Final Deliverables

**Goal:** Confirm mandatory final outputs are present and reviewed.

**Main flow:** Review final deliverable checklist and statuses.

**Result:** Final delivery completeness is verified.


## ER-31 — Review Final Outstanding Conditions

**Goal:** Determine whether remaining matters block acceptance.

**Main flow:** Review unresolved conditions, missing deliverables, critical technical comments, unfinished obligations and documentation gaps.

**Result:** Employer understands remaining obligations.


## ER-32 — Give Final Project Acceptance

**Goal:** Formally confirm project completion.

**Main flow:** Review completion package, confirm conditions, accept and record representative/date/final versions/statement.

**Result:** Project receives authoritative final acceptance.


## ER-33 — Give Conditional Final Acceptance

**Goal:** Accept project subject to permitted remaining obligations.

**Main flow:** Define conditions/deadlines/accountable parties and record conditional acceptance.

**Result:** Project is conditionally complete until conditions close.


## ER-34 — Reject Final Acceptance Request

**Goal:** Decline project acceptance.

**Main flow:** Record reasons/unresolved requirements and return project to appropriate correction/completion state.

**Result:** Project cannot close until deficiencies are addressed.


## ER-35 — View Final Acceptance Record

**Goal:** Access authoritative acceptance evidence.

**Main flow:** View project, phases, deliverables, date, representative, conditions and statement.

**Result:** Durable acceptance record exists.


## ER-36 — Monitor Project Risks and Critical Issues

**Goal:** Maintain executive visibility into consequential issues.

**Main flow:** View high/critical risks, escalations, mitigation and impact.

**Result:** Management attention focuses on major issues.


## ER-37 — View Escalated Project Issue

**Goal:** Inspect issue escalated for employer attention.

**Main flow:** Review evidence/history and add management comment/direction where authorized.

**Result:** High-level issues receive employer response.


## ER-38 — View Schedule Variance

**Goal:** Compare original and current commitments.

**Main flow:** View baseline/revised dates, extensions, current delay and forecast completion.

**Result:** Employer can assess schedule performance over time.


## ER-39 — View Deliverable Performance Indicators

**Goal:** Monitor delivery performance at management level.

**Main flow:** View on-time %, overdue count, first-review acceptance, revision frequency, review backlog and pending acceptance.

**Result:** Employer gains objective performance information.


## ER-40 — View Contractor Progress Summary

**Goal:** Review contractor delivery position.

**Main flow:** View progress, deliverable completion, corrective actions, overdue obligations, revision cycles and risks.

**Result:** Employer oversight is supported.


## ER-41 — View Executive Project Status Report

**Goal:** Obtain management-level report.

**Main flow:** Review status/progress/phases/milestones/deliverables/schedule variance/risks/acceptance/decisions.

**Result:** Employer receives concise governance report.


## ER-42 — View Phase Status Report

**Goal:** Review management summary for a phase.

**Main flow:** Open phase report with progress, deliverables, issues, review and acceptance readiness.

**Result:** Phase performance is easy to assess.


## ER-43 — View Deliverable Status Report

**Goal:** Review major-output status.

**Main flow:** Open consolidated deliverable report.

**Result:** Employer can monitor contractual outputs.


## ER-44 — View Acceptance Status Report

**Goal:** See acceptance state across project.

**Main flow:** Review phase/project acceptance and condition statuses.

**Result:** Contractual acceptance progress is immediately visible.


## ER-45 — Export Managerial Report

**Goal:** Export authorized status information.

**Main flow:** Choose approved report/template and export to supported format.

**Result:** Governance information can be shared.


## ER-46 — Receive Management Notifications

**Goal:** Receive only employer-relevant events.

**Main flow:** Receive phase/final acceptance readiness, major delays, critical issues, technical concerns, overdue conditions and decision requests.

**Result:** Employer is informed without operational overload.


## ER-47 — Open Decision Item from Notification

**Goal:** Navigate directly to employer action item.

**Main flow:** Select notification and open linked acceptance/issue/deliverable.

**Result:** Decision workflow is efficient.


## ER-48 — Communicate with Project Manager

**Goal:** Request clarification or give management direction.

**Main flow:** Send contextual message linked to project item.

**Result:** Employer-PM communication is traceable.


## ER-49 — Communicate Regarding Technical Finding

**Goal:** Seek clarification on important technical finding.

**Main flow:** Send contextual question through permitted workflow, typically involving PM and/or Technical Reviewer.

**Result:** Employer can understand technical concerns before deciding.


## ER-50 — Define Acceptance Condition

**Goal:** Create explicit obligation for conditional acceptance.

**Main flow:** Define description/source/responsible party/deadline/related deliverable/evidence/verifier.

**Result:** Conditional acceptance is formally controlled.


## ER-51 — Monitor Acceptance Conditions

**Goal:** Track remaining obligations.

**Main flow:** View Open/In Progress/Submitted for Verification/Satisfied/Overdue/Rejected states.

**Result:** Outstanding acceptance obligations are visible.


## ER-52 — Verify an Acceptance Condition

**Goal:** Confirm a condition is satisfied.

**Main flow:** Review evidence and verify directly or rely on authorized PM/Technical Reviewer verification according to rule.

**Result:** Condition is formally closed.


## ER-53 — Close Conditional Acceptance

**Goal:** Convert conditional to full acceptance.

**Main flow:** Confirm all mandatory conditions closed and record full acceptance transition.

**Result:** Acceptance status reflects true completion.


# End-to-End Governance and Delivery Model

```text
Administrator
    ↓ configures environment

Project Manager
    ├── Project Officer(s)
    └── coordinates governance
             ↓
Technical Reviewer
    ↕ technical review / comments
             ↓
Contractor Project Leader
    └── Contractor Team Member(s)
             ↓
      formal contractor submission
             ↓
Project Manager / Technical Reviewer
             ↓
Employer Representative
    ├── Phase Acceptance
    └── Final Project Acceptance
```

## Core Submission and Acceptance Principle

```text
Contractor Team Member
        ↓ prepares / uploads / revises
Contractor Project Leader
        ↓ internal QA + formal submission
Project Officer
        ↓ monitoring / completeness support
Project Manager
        ↓ project review / recommendation
Technical Reviewer
        ↓ technical assessment where required
Project Manager
        ↓ recommends acceptance
Employer Representative
        ↓
Formal Phase Acceptance
        ↓
... all required phases ...
        ↓
Final Project Acceptance
```

## Repository Principle

Project repository permissions are role- and project-scoped. Contractor Team Members may upload/download permitted materials; Contractor Project Leaders supervise contractor content; Project Officers/Managers monitor it; Technical Reviewers and Employer Representatives receive appropriate read/review access.

## Configuration Principle

Project-specific entity types, forms, relationships, taxonomies, templates and import mappings should be represented as metadata/configuration rather than new domain-specific application code or database tables. The generic UI should render these definitions dynamically.

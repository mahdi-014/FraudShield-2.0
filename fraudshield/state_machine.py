"""Simulated transaction workflow state machine.

Payment states:
- completed: Terminal success state (allow, or analyst release).
- rejected: Terminal failure state (analyst reject).
- awaiting_acknowledgement: Non-terminal state for warning thresholds. Customer acknowledgement flow is deferred.
- pending_verification: Non-terminal state for pause thresholds. Reviewable by analyst. Customer verification flow is deferred.
- held_for_review: Non-terminal state for hold thresholds. Reviewable by analyst.

Note:
These are simulated payment states; no actual funds move.
Customer acknowledgement and verification flows are deferred to future milestones.
"""

STATUS_COMPLETED = 'completed'
STATUS_REJECTED = 'rejected'
STATUS_AWAITING_ACKNOWLEDGEMENT = 'awaiting_acknowledgement'
STATUS_PENDING_VERIFICATION = 'pending_verification'
STATUS_HELD_FOR_REVIEW = 'held_for_review'

TERMINAL_STATES = {STATUS_COMPLETED, STATUS_REJECTED}
REVIEWABLE_STATES = {STATUS_PENDING_VERIFICATION, STATUS_HELD_FOR_REVIEW}

INITIAL_ACTION_TO_STATUS = {
    'allow': STATUS_COMPLETED,
    'warn': STATUS_AWAITING_ACKNOWLEDGEMENT,
    'pause': STATUS_PENDING_VERIFICATION,
    'hold': STATUS_HELD_FOR_REVIEW,
}

ANALYST_ACTIONS = {
    'release': STATUS_COMPLETED,
    'reject': STATUS_REJECTED,
}

def map_initial_status(action: str) -> str:
    if action not in INITIAL_ACTION_TO_STATUS:
        raise ValueError(f"Unknown initial scoring action: '{action}'")
    return INITIAL_ACTION_TO_STATUS[action]

def requires_review_case(status: str) -> bool:
    return status in REVIEWABLE_STATES

def validate_analyst_transition(current_status: str, action: str) -> str:
    if current_status in TERMINAL_STATES:
        raise ValueError(
            f"Cannot perform analyst action on terminal state '{current_status}'. Terminal states cannot be changed."
        )
    if current_status not in REVIEWABLE_STATES:
        raise ValueError(
            f"Analyst actions are only permitted for states {sorted(REVIEWABLE_STATES)}, not '{current_status}'."
        )
    if action not in ANALYST_ACTIONS:
        raise ValueError(f"Invalid analyst action '{action}'. Permitted actions: {sorted(ANALYST_ACTIONS.keys())}")
    return ANALYST_ACTIONS[action]

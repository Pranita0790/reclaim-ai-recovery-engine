from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.models.audit import (
    AuditEvent,
    AuditEventType,
)
from app.services.audit_repository import AuditRepository


class AuditService:
    """
    Store and retrieve audit events for recovery cases.

    By default, this service uses in-memory storage.

    If an AuditRepository is provided, audit events are also
    persisted to SQLite.
    """

    def __init__(
        self,
        repository: AuditRepository | None = None,
    ) -> None:
        self._events: list[AuditEvent] = []

        self.repository = repository

    def record_event(
        self,
        case_id: str,
        event_type: AuditEventType,
        message: str,
        data: dict | None = None,
    ) -> AuditEvent:
        """Create, store, and optionally persist an audit event."""

        event = AuditEvent(
            event_id=str(uuid4()),
            case_id=case_id,
            event_type=event_type,
            message=message,
            data=data or {},
            created_at=datetime.utcnow(),
        )

        # Store event in memory.
        self._events.append(event)

        # Persist event if a repository is configured.
        if self.repository is not None:
            self.repository.save_event(event)

        return event

    def get_case_events(
        self,
        case_id: str,
    ) -> list[AuditEvent]:
        """
        Return all audit events belonging to a recovery case.

        If persistent storage is configured, retrieve events
        from the repository.
        """

        if self.repository is not None:
            return self.repository.get_case_events(
                case_id
            )

        return [
            event
            for event in self._events
            if event.case_id == case_id
        ]

    def get_all_events(
        self,
    ) -> list[AuditEvent]:
        """
        Return every stored audit event.

        If persistent storage is configured, retrieve events
        from the repository.
        """

        if self.repository is not None:
            return self.repository.get_all_events()

        return list(self._events)

    def clear_case_events(
        self,
        case_id: str,
    ) -> None:
        """
        Remove all audit events for a recovery case.

        Events are removed from both memory and persistent
        storage when a repository is configured.
        """

        self._events = [
            event
            for event in self._events
            if event.case_id != case_id
        ]

        if self.repository is not None:
            self.repository.delete_case_events(
                case_id
            )
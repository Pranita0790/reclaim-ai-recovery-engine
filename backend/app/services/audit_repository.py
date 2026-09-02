from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.models.audit import (
    AuditEvent,
    AuditEventType,
)


class AuditRepository:
    """SQLite repository for persistent audit events."""

    def __init__(
        self,
        database_path: str | Path = "data/reclaim.db",
    ) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    def _get_connection(
        self,
    ) -> sqlite3.Connection:
        """Create a connection to the SQLite database."""

        return sqlite3.connect(
            self.database_path,
        )

    def _initialize_database(
        self,
    ) -> None:
        """Create the audit_events table if needed."""

        with self._get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_audit_events_case_id
                ON audit_events(case_id)
                """
            )

    def save_event(
        self,
        event: AuditEvent,
    ) -> AuditEvent:
        """Persist an audit event."""

        with self._get_connection() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    event_id,
                    case_id,
                    event_type,
                    message,
                    data,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.case_id,
                    event.event_type.value,
                    event.message,
                    json.dumps(event.data),
                    event.created_at.isoformat(),
                ),
            )

        return event

    def get_case_events(
        self,
        case_id: str,
    ) -> list[AuditEvent]:
        """Return all events belonging to one recovery case."""

        with self._get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_id,
                    case_id,
                    event_type,
                    message,
                    data,
                    created_at
                FROM audit_events
                WHERE case_id = ?
                ORDER BY created_at ASC
                """,
                (case_id,),
            ).fetchall()

        return [
            self._row_to_event(row)
            for row in rows
        ]

    def get_all_events(
        self,
    ) -> list[AuditEvent]:
        """Return every stored audit event."""

        with self._get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_id,
                    case_id,
                    event_type,
                    message,
                    data,
                    created_at
                FROM audit_events
                ORDER BY created_at ASC
                """
            ).fetchall()

        return [
            self._row_to_event(row)
            for row in rows
        ]

    def delete_case_events(
        self,
        case_id: str,
    ) -> None:
        """Delete all audit events for one recovery case."""

        with self._get_connection() as connection:
            connection.execute(
                """
                DELETE FROM audit_events
                WHERE case_id = ?
                """,
                (case_id,),
            )

    @staticmethod
    def _row_to_event(
        row: tuple,
    ) -> AuditEvent:
        """Convert a database row into an AuditEvent."""

        return AuditEvent(
            event_id=row[0],
            case_id=row[1],
            event_type=AuditEventType(row[2]),
            message=row[3],
            data=json.loads(row[4]),
            created_at=datetime.fromisoformat(
                row[5]
            ),
        )
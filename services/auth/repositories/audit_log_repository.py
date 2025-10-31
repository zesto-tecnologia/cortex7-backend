"""Audit log repository for data access layer."""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from services.auth.models.audit_log import AuditLog
from typing import Any


class AuditLogRepository:
    """Repository for audit log data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        user_id: UUID | None,
        action: str,
        resource: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> AuditLog:
        """Create a new audit log entry.

        Args:
            user_id: User UUID (can be None for anonymous actions)
            action: Action performed (e.g., 'login', 'logout', 'register')
            resource: Resource affected (optional)
            ip_address: IP address of the client
            user_agent: User agent string
            metadata: Additional metadata as JSON

        Returns:
            Created audit log instance
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata or {}
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: UUID) -> AuditLog | None:
        """Get audit log by ID.

        Args:
            log_id: Audit log UUID

        Returns:
            AuditLog instance or None if not found
        """
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_user_logs(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[AuditLog]:
        """Get audit logs for a specific user.

        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            action: Optional action filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of audit logs
        """
        query = select(AuditLog).where(AuditLog.user_id == user_id)

        if action is not None:
            query = query.where(AuditLog.action == action)

        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_logs(
        self,
        limit: int = 100,
        action: str | None = None,
        user_id: UUID | None = None
    ) -> list[AuditLog]:
        """Get recent audit logs across all users.

        Args:
            limit: Maximum number of records to return
            action: Optional action filter
            user_id: Optional user ID filter

        Returns:
            List of recent audit logs
        """
        query = select(AuditLog)

        if action is not None:
            query = query.where(AuditLog.action == action)

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_action(
        self,
        action: str,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[AuditLog]:
        """Get audit logs filtered by action type.

        Args:
            action: Action to filter by (e.g., 'login', 'failed_login')
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of audit logs
        """
        query = select(AuditLog).where(AuditLog.action == action)

        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_ip(
        self,
        ip_address: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get audit logs from a specific IP address.

        Useful for security analysis and detecting suspicious activity.

        Args:
            ip_address: IP address to search for
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of audit logs
        """
        query = select(AuditLog).where(AuditLog.ip_address == ip_address)
        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_action(
        self,
        action: str,
        user_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> int:
        """Count audit logs by action type.

        Args:
            action: Action to count
            user_id: Optional user ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Count of matching logs
        """
        query = select(func.count(AuditLog.id)).where(AuditLog.action == action)

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)

        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_failed_login_attempts(
        self,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        since: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get failed login attempts.

        Useful for security monitoring and brute force detection.

        Args:
            user_id: Optional user ID filter
            ip_address: Optional IP address filter
            since: Optional start datetime
            limit: Maximum number of records

        Returns:
            List of failed login attempt logs
        """
        query = select(AuditLog).where(AuditLog.action == 'failed_login')

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)

        if ip_address is not None:
            query = query.where(AuditLog.ip_address == ip_address)

        if since is not None:
            query = query.where(AuditLog.timestamp >= since)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_recent_failed_logins(
        self,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        minutes: int = 15
    ) -> int:
        """Count failed login attempts in recent time period.

        Args:
            user_id: Optional user ID filter
            ip_address: Optional IP address filter
            minutes: Time window in minutes (default: 15)

        Returns:
            Count of failed login attempts
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(func.count(AuditLog.id)).where(
            AuditLog.action == 'failed_login',
            AuditLog.timestamp >= since
        )

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)

        if ip_address is not None:
            query = query.where(AuditLog.ip_address == ip_address)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def cleanup_old_logs(self, older_than_days: int = 90) -> int:
        """Delete audit logs older than specified days.

        This should be run periodically as a maintenance task.

        Args:
            older_than_days: Delete logs older than this many days (default: 90)

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        result = await self.session.execute(
            delete(AuditLog).where(AuditLog.timestamp < cutoff_date)
        )
        await self.session.flush()

        return result.rowcount

    async def get_action_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, int]:
        """Get statistics on audit log actions.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping action types to counts
        """
        query = select(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        )

        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.group_by(AuditLog.action)

        result = await self.session.execute(query)
        return {row.action: row.count for row in result.all()}

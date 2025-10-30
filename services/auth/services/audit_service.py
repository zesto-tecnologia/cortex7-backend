"""Audit logging service for tracking admin and security events."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models.audit_log import AuditLog
from services.auth.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for creating audit log entries."""

    def __init__(self, session: AsyncSession):
        """Initialize audit service.

        Args:
            session: Database session
        """
        self.session = session

    async def log_admin_action(
        self,
        event_type: str,
        user_id: UUID,
        result: str,
        request: Optional[Request] = None,
        event_details: Optional[dict] = None
    ) -> AuditLog:
        """Log an admin action to the audit log.

        Args:
            event_type: Type of event (e.g., "invite_created", "role_updated")
            user_id: UUID of the user performing the action
            result: Result of the action ("success", "failure", "denied")
            request: FastAPI request object for extracting metadata
            event_details: Additional event-specific details

        Returns:
            AuditLog: Created audit log entry
        """
        # Extract request metadata
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Create audit log entry
        audit_log = AuditLog(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            result=result,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            service_name="auth-service",
            event_details=event_details or {}
        )

        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)

        logger.info(
            f"audit_logged - event_type={event_type}, user_id={user_id}, result={result}"
        )

        return audit_log

    async def log_invite_created(
        self,
        admin_id: UUID,
        invite_code: str,
        expires_in_days: int,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log invite code creation.

        Args:
            admin_id: UUID of the admin creating the invite
            invite_code: Generated invite code (first 8 chars only for security)
            expires_in_days: Expiration period in days
            request: FastAPI request object

        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_admin_action(
            event_type="invite_created",
            user_id=admin_id,
            result="success",
            request=request,
            event_details={
                "invite_code_prefix": invite_code[:8],
                "expires_in_days": expires_in_days
            }
        )

    async def log_invite_revoked(
        self,
        admin_id: UUID,
        invite_code: str,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log invite code revocation.

        Args:
            admin_id: UUID of the admin revoking the invite
            invite_code: Revoked invite code (first 8 chars only)
            request: FastAPI request object

        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_admin_action(
            event_type="invite_revoked",
            user_id=admin_id,
            result="success",
            request=request,
            event_details={
                "invite_code_prefix": invite_code[:8]
            }
        )

    async def log_role_updated(
        self,
        admin_id: UUID,
        target_user_id: UUID,
        old_role: str,
        new_role: str,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log user role update.

        Args:
            admin_id: UUID of the admin updating the role
            target_user_id: UUID of the user whose role was updated
            old_role: Previous role
            new_role: New role
            request: FastAPI request object

        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_admin_action(
            event_type="role_updated",
            user_id=admin_id,
            result="success",
            request=request,
            event_details={
                "target_user_id": str(target_user_id),
                "old_role": old_role,
                "new_role": new_role
            }
        )

    async def log_permission_denied(
        self,
        user_id: UUID,
        attempted_action: str,
        required_role: str,
        current_role: str,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log permission denied event.

        Args:
            user_id: UUID of the user whose access was denied
            attempted_action: Action that was attempted
            required_role: Role required for the action
            current_role: Current role of the user
            request: FastAPI request object

        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_admin_action(
            event_type="permission_denied",
            user_id=user_id,
            result="denied",
            request=request,
            event_details={
                "attempted_action": attempted_action,
                "required_role": required_role,
                "current_role": current_role
            }
        )

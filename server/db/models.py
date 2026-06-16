"""数据库表模型定义。

可以把这一层理解成 Java 里的 JPA Entity。
这里的表分成 4 组：
1. 身份与权限：users / roles / permissions / sessions
2. 会话与审计：conversation_* / tool_audit_logs
3. 知识库：knowledge_documents / knowledge_chunks / ingestion_jobs
4. 报告：user_device_reports / report_requests
"""

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.base import Base


def utc_now() -> datetime:
    """统一的 UTC 时间工厂。"""
    return datetime.now(UTC)


class RolePermission(Base):
    """角色-权限多对多关联表。"""
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)


class UserRole(Base):
    """用户-角色多对多关联表。"""
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)


class User(Base):
    """用户主表。

    这是系统里最核心的身份表，保存：
    - username：登录名
    - account_code：业务账号/用户编号
    - location：用户默认地理位置
    - password_hash：密码哈希，不存明文
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    account_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    location: Mapped[str] = mapped_column(String(64), default="上海")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


class Role(Base):
    """角色表，例如 user / admin。"""
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")

    permissions: Mapped[list["Permission"]] = relationship(secondary="role_permissions", back_populates="roles")
    users: Mapped[list[User]] = relationship(secondary="user_roles", back_populates="roles")


class Permission(Base):
    """权限点表，例如 kb:read / report:read:self。"""
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")

    roles: Mapped[list[Role]] = relationship(secondary="role_permissions", back_populates="permissions")


class Session(Base):
    """刷新令牌会话表。

    Access Token 无状态，Refresh Token 需要可撤销，因此会落一张会话表。
    """
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped[User] = relationship(back_populates="sessions")


class ConversationThread(Base):
    """对话线程表。

    一次连续聊天对应一个 thread，类似会话主表。
    """
    __tablename__ = "conversation_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="新会话")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """对话消息明细表。

    用户和助手的每一条消息都会入库，便于回放、审计和后续多轮扩展。
    """
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_threads.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citations: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    thread: Mapped[ConversationThread] = relationship(back_populates="messages")


class ToolAuditLog(Base):
    """审计日志表。

    记录关键动作，比如 FAQ 检索、报告查询等。
    """
    __tablename__ = "tool_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_threads.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="success")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeDocument(Base):
    """知识文档主表。

    每个 txt/pdf 原始文件入库后对应一条 document 记录。
    """
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_path: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(64), default="general")
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    document_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """知识分片表。

    document 会被切成多个 chunk，每个 chunk 都会保存：
    - 原文
    - 清洗后的文本
    - 元数据
    - embedding 向量
    """
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("chunk_hash", name="uq_knowledge_chunks_chunk_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    sanitized_content: Mapped[str] = mapped_column(Text)
    chunk_hash: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(64), default="general")
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


class IngestionJob(Base):
    """知识导入任务表，用于记录一次离线导入的结果。"""
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportRequest(Base):
    """报告查询审计表。

    记录“谁在什么时间查了谁的哪一个月报告”。
    """
    __tablename__ = "report_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    month: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(32), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UserDeviceReport(Base):
    """用户月度设备报告事实表。

    真正的业务报告数据存这里，`user_id + month` 唯一。
    """
    __tablename__ = "user_device_reports"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_user_device_reports_user_month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    month: Mapped[str] = mapped_column(String(7), index=True)
    feature: Mapped[str] = mapped_column(Text, default="")
    efficiency: Mapped[str] = mapped_column(Text, default="")
    consumables: Mapped[str] = mapped_column(Text, default="")
    comparison: Mapped[str] = mapped_column(Text, default="")
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from app.models import UserRole, TaskStatus, TaskPriority, ProjectMemberRole


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectMemberOut(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectMemberRole

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    user_id: UUID
    role: ProjectMemberRole = ProjectMemberRole.member


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    created_at: datetime
    members: List[ProjectMemberOut] = []

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    project_id: UUID
    assignee_id: Optional[UUID]
    created_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OverdueTask(BaseModel):
    id: UUID
    title: str
    project_id: UUID
    assignee_id: Optional[UUID]
    due_date: date
    status: TaskStatus

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int


class DashboardStats(BaseModel):
    projects_count: int
    task_summary: TaskSummary
    overdue_tasks: List[OverdueTask]
    assigned_tasks: List[TaskOut]


class Token(BaseModel):
    access_token: str
    token_type: str
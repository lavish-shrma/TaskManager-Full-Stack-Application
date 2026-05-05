from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.db.session import get_session
from app.models import User, Project, ProjectMember, Task, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.dependencies.auth import get_current_user, check_project_admin, get_project_member_or_403

router = APIRouter(prefix="/projects", tags=["tasks"])


@router.post("/{project_id}/tasks", response_model=TaskOut)
async def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    _admin: ProjectMember = Depends(check_project_admin),
    session: AsyncSession = Depends(get_session)
):
    """Create a new task in the project."""
    # Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # If assignee_id is provided, verify user exists and is a member
    if task_data.assignee_id:
        stmt = select(User).where(User.id == task_data.assignee_id)
        result = await session.execute(stmt)
        assignee = result.scalar_one_or_none()
        
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"loc": ["assignee_id"], "msg": "Assignee not found"}]
            )
        
        stmt = select(ProjectMember).where(
            (ProjectMember.project_id == project_id) &
            (ProjectMember.user_id == task_data.assignee_id)
        )
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"loc": ["assignee_id"], "msg": "Assignee is not a project member"}]
            )
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        project_id=project_id,
        assignee_id=task_data.assignee_id,
        created_by=current_user.id
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.get("/{project_id}/tasks", response_model=List[TaskOut])
async def list_tasks(
    project_id: UUID,
    status: Optional[str] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    _member: ProjectMember = Depends(get_project_member_or_403),
    session: AsyncSession = Depends(get_session)
):
    """Get tasks in the project."""
    stmt = select(Task).where(Task.project_id == project_id)
    
    if status:
        try:
            task_status = TaskStatus(status)
            stmt = stmt.where(Task.status == task_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"loc": ["status"], "msg": "Invalid status value"}]
            )
    
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    
    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskOut)
async def get_task(
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    _member: ProjectMember = Depends(get_project_member_or_403),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific task."""
    stmt = select(Task).where(
        (Task.id == task_id) &
        (Task.project_id == project_id)
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    project_id: UUID,
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    _member: ProjectMember = Depends(get_project_member_or_403),
    session: AsyncSession = Depends(get_session)
):
    """Update a task."""
    stmt = select(Task).where(
        (Task.id == task_id) &
        (Task.project_id == project_id)
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get project member to check role
    stmt = select(ProjectMember).where(
        (ProjectMember.project_id == project_id) &
        (ProjectMember.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    
    is_admin = member and member.role == "admin"
    is_assignee = task.assignee_id == current_user.id
    
    # Check permissions
    if not is_admin:
        # Members can only update status field
        if task_data.title is not None or task_data.description is not None or \
           task_data.priority is not None or task_data.due_date is not None or \
           task_data.assignee_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only update task status"
            )
        # Members can only update status on tasks assigned to them
        if not is_assignee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only update tasks assigned to them"
            )
    
    # Update allowed fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.assignee_id is not None:
        # Verify assignee is a project member
        stmt = select(ProjectMember).where(
            (ProjectMember.project_id == project_id) &
            (ProjectMember.user_id == task_data.assignee_id)
        )
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"loc": ["assignee_id"], "msg": "Assignee is not a project member"}]
            )
        task.assignee_id = task_data.assignee_id
    
    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    _member: ProjectMember = Depends(get_project_member_or_403),
    session: AsyncSession = Depends(get_session)
):
    """Delete a task."""
    stmt = select(Task).where(
        (Task.id == task_id) &
        (Task.project_id == project_id)
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get project member to check role
    stmt = select(ProjectMember).where(
        (ProjectMember.project_id == project_id) &
        (ProjectMember.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    
    is_admin = member and member.role == "admin"
    is_creator = task.created_by == current_user.id
    
    if not (is_admin or is_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or task creators can delete tasks"
        )
    
    await session.delete(task)
    await session.commit()

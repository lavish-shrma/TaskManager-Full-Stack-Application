from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date
from app.db.session import get_session
from app.models import User, Project, ProjectMember, Task, TaskStatus
from app.schemas import DashboardStats, TaskSummary, TaskOut, OverdueTask
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get dashboard statistics."""
    # Get all project IDs user is a member of
    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == current_user.id)
    result = await session.execute(stmt)
    project_ids = result.scalars().all()
    
    # Count of projects
    projects_count = len(project_ids)
    
    # Task counts by status
    stmt = select(func.count(Task.id)).where(Task.project_id.in_(project_ids))
    result = await session.execute(stmt)
    total_tasks = result.scalar() or 0
    
    stmt = select(func.count(Task.id)).where(
        and_(Task.project_id.in_(project_ids), Task.status == TaskStatus.todo)
    )
    result = await session.execute(stmt)
    todo_count = result.scalar() or 0
    
    stmt = select(func.count(Task.id)).where(
        and_(Task.project_id.in_(project_ids), Task.status == TaskStatus.in_progress)
    )
    result = await session.execute(stmt)
    in_progress_count = result.scalar() or 0
    
    stmt = select(func.count(Task.id)).where(
        and_(Task.project_id.in_(project_ids), Task.status == TaskStatus.done)
    )
    result = await session.execute(stmt)
    done_count = result.scalar() or 0
    
    task_summary = TaskSummary(
        total=total_tasks,
        todo=todo_count,
        in_progress=in_progress_count,
        done=done_count
    )
    
    # Get overdue tasks
    stmt = select(Task).where(
        and_(
            Task.project_id.in_(project_ids),
            Task.due_date < date.today(),
            Task.status != TaskStatus.done
        )
    )
    result = await session.execute(stmt)
    overdue_tasks = result.scalars().all()
    
    # Get tasks assigned to current user
    stmt = select(Task).where(
        and_(
            Task.project_id.in_(project_ids),
            Task.assignee_id == current_user.id
        )
    )
    result = await session.execute(stmt)
    assigned_tasks = result.scalars().all()
    
    return DashboardStats(
        projects_count=projects_count,
        task_summary=task_summary,
        overdue_tasks=overdue_tasks,
        assigned_tasks=assigned_tasks
    )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from app.db.session import get_session
from app.models import User, Project, ProjectMember, ProjectMemberRole
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberAdd, ProjectMemberOut
from app.dependencies.auth import get_current_user, check_project_admin, check_project_owner, get_project_member_or_403

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new project."""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    session.add(project)
    await session.flush()

    # Add owner as admin member
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=ProjectMemberRole.admin
    )
    session.add(member)
    await session.commit()
    stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project.id)
    result = await session.execute(stmt)
    project = result.scalar_one()

    return project


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all projects the user is a member of."""
    stmt = select(Project).join(ProjectMember).where(
        ProjectMember.user_id == current_user.id
    ).options(selectinload(Project.members))
    result = await session.execute(stmt)
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: UUID,
    _member: ProjectMember = Depends(get_project_member_or_403),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific project."""
    stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    _admin: ProjectMember = Depends(check_project_admin),
    session: AsyncSession = Depends(get_session)
):
    """Update project metadata."""
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    await session.commit()
    stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one()
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    _owner: Project = Depends(check_project_owner),
    session: AsyncSession = Depends(get_session)
):
    """Delete a project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if project:
        await session.delete(project)
        await session.commit()


@router.post("/{project_id}/members", response_model=ProjectMemberOut)
async def add_project_member(
    project_id: UUID,
    member_data: ProjectMemberAdd,
    _admin: ProjectMember = Depends(check_project_admin),
    session: AsyncSession = Depends(get_session)
):
    """Add a member to the project."""
    # Check if user exists
    stmt = select(User).where(User.id == member_data.user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"loc": ["user_id"], "msg": "User not found"}]
        )
    
    # Check if already a member
    stmt = select(ProjectMember).where(
        (ProjectMember.project_id == project_id) &
        (ProjectMember.user_id == member_data.user_id)
    )
    result = await session.execute(stmt)
    existing_member = result.scalar_one_or_none()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"loc": ["user_id"], "msg": "User is already a member"}]
        )
    
    new_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    session.add(new_member)
    await session.commit()
    await session.refresh(new_member)
    return new_member


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    _admin: ProjectMember = Depends(check_project_admin),
    session: AsyncSession = Depends(get_session)
):
    """Remove a member from the project."""
    stmt = select(ProjectMember).where(
        (ProjectMember.project_id == project_id) &
        (ProjectMember.user_id == user_id)
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Prevent removing the owner
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    
    if project and project.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the project owner"
        )
    
    await session.delete(member)
    await session.commit()

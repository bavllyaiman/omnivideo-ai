from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from uuid import uuid4
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Project, Video

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
async def list_projects(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * per_page
    total = (await db.execute(select(func.count(Project.id)).where(Project.user_id == user.id))).scalar()
    result = await db.execute(select(Project).where(Project.user_id == user.id).order_by(desc(Project.created_at)).offset(offset).limit(per_page))
    projects = result.scalars().all()
    items = []
    for p in projects:
        vc = (await db.execute(select(func.count(Video.id)).where(Video.project_id == p.id))).scalar()
        items.append({"id": p.id, "name": p.name, "description": p.description, "status": p.status, "video_count": vc, "created_at": str(p.created_at), "updated_at": str(p.updated_at)})
    return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}


@router.post("")
async def create_project(name: str, description: str = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = Project(user_id=user.id, name=name, description=description)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return {"id": project.id, "name": project.name, "description": project.description, "status": project.status, "created_at": str(project.created_at)}


@router.get("/{project_id}")
async def get_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    vc = (await db.execute(select(func.count(Video.id)).where(Video.project_id == project.id))).scalar()
    return {"id": project.id, "name": project.name, "description": project.description, "status": project.status, "video_count": vc, "created_at": str(project.created_at)}


@router.put("/{project_id}")
async def update_project(project_id: str, name: str = None, description: str = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if name: project.name = name
    if description: project.description = description
    await db.flush()
    return {"id": project.id, "name": project.name, "description": project.description}


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    return {"status": "deleted"}

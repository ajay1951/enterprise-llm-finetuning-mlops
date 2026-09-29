from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List

from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    def create_project(self, project_in: ProjectCreate) -> Project:
        from slugify import slugify

        slug = slugify(project_in.name)
        existing = (
            self.db.query(Project)
            .filter(
                Project.slug == slug, Project.organization_id == self.organization_id
            )
            .first()
        )
        if existing:
            import uuid

            slug = f"{slug}-{str(uuid.uuid4())[:6]}"

        project = Project(
            name=project_in.name,
            description=project_in.description,
            organization_id=self.organization_id,
            slug=slug,
        )
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return project
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Project with name '{project_in.name}' already exists in this organization.",
            )

    def get_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.organization_id == self.organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_project(self, project_id: str) -> Project:
        project = (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.organization_id == self.organization_id,
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        self.db.delete(project)
        self.db.commit()

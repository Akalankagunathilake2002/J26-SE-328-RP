from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.learning import (
    UpstreamStudentProfileRequest,
    UpstreamProfileResponse
)
from app.services.progress_service import progress_service

router = APIRouter(prefix="/upstream", tags=["Platform Integration: Upstream Contracts"])


@router.post("/student-profile", response_model=UpstreamProfileResponse)
async def receive_student_profile(
    request: UpstreamStudentProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Standardized Upstream Interface Contract with Skill-Gap Analysis Team (Component C03).
    Receives computed readiness score, identified weak skills, and priority learning topics,
    persisting student state and returning tailored starting modules across the curriculum.
    """
    try:
        # Map weak skills to curriculum modules
        curriculum_module_map = {
            "Database Indexing": "Relational Database Indexing: B-Tree, GIN, and BRIN Optimization",
            "Message Queues": "Distributed Message Queues: Apache Kafka Partitions & Consumer Groups",
            "Distributed Caching": "High-Performance Caching Patterns with Redis & Stampede Mitigation",
            "Microservices Resilience": "Microservices Resilience: Circuit Breakers & Resilience4j",
            "Authentication": "JSON Web Token (JWT) Stateless Authentication & OWASP Defenses",
            "React Patterns": "Modern Frontend Rendering Patterns: SSR, SSG, ISR, and Server Components",
            "State Management": "Modern Frontend State Management: Zustand vs TanStack Query",
            "Docker Optimization": "Docker Multi-Stage Builds & Container Attack Surface Reduction",
            "Kubernetes Orchestration": "Kubernetes Architecture: Pod Orchestration, Services & Autoscaling",
            "Table Partitioning": "PostgreSQL Table Partitioning & Large-Scale Archival",
            "Transaction Isolation": "Transaction Isolation Levels, Concurrency Anomalies & MVCC Mechanics"
        }

        recommended_modules = []
        for skill in request.identified_weak_skills:
            matched_mod = curriculum_module_map.get(skill, f"Foundations of {skill} in {request.target_role}")
            recommended_modules.append(matched_mod)

        for topic in request.priority_learning_topics:
            if topic not in recommended_modules:
                recommended_modules.append(topic)

        if not recommended_modules:
            recommended_modules = [
                f"Core {request.target_role} Architecture Foundations",
                "Advanced System Design & Scalability Patterns"
            ]

        # Record profile baseline progress
        await progress_service.get_or_create_progress(
            session=db,
            student_id=request.student_id,
            target_role=request.target_role
        )

        return UpstreamProfileResponse(
            status="success",
            student_id=request.student_id,
            target_role=request.target_role,
            recommended_learning_modules=recommended_modules,
            message=(
                f"Student profile synchronized from Skill-Gap Analysis. "
                f"Readiness score: {request.readiness_score:.1f}%. "
                f"Generated {len(recommended_modules)} personalized starting modules."
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upstream profile sync error: {str(e)}")

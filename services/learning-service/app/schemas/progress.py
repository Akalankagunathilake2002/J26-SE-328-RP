from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class TopicProgressItem(BaseModel):
    topic: str
    target_role: str
    queries_count: int
    status: str
    last_studied_at: datetime


class StudentProgressResponse(BaseModel):
    student_id: str
    target_role: str
    total_topics_explored: int
    completed_topics_count: int
    topics: List[TopicProgressItem]

from pydantic import BaseModel
from typing import Optional


class VideoBase(BaseModel):
    filename: str
    web_path: str


class VideoResponse(VideoBase):
    id: int
    is_annotated: bool
    tag: Optional[str] = None


class TagRequest(BaseModel):
    tag: str


class MessageResponse(BaseModel):
    message: str


class StatsResponse(BaseModel):
    total_videos: int
    annotated_videos: int
    unannotated_videos: int

import os
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

from . import database, models

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

VIDEO_FOLDER_PATH_STR = os.getenv("VIDEO_FOLDER_PATH")
if not VIDEO_FOLDER_PATH_STR:
    raise ValueError(
        "VIDEO_FOLDER_PATH environment variable not set. Please create a .env file."
    )
raw_video_folder_path = Path(VIDEO_FOLDER_PATH_STR)
if not raw_video_folder_path.is_absolute():
    VIDEO_FOLDER = (PROJECT_ROOT / raw_video_folder_path).resolve()
else:
    VIDEO_FOLDER = raw_video_folder_path.resolve()
if not VIDEO_FOLDER.is_dir():
    raise ValueError(
        f"VIDEO_FOLDER_PATH '{VIDEO_FOLDER_PATH_STR}' resolved to '{VIDEO_FOLDER}', which is not a valid directory."
    )

PREDEFINED_TAGS_STR = os.getenv("PREDEFINED_TAGS", '["Good", "Bad", "Neutral"]')
try:
    PREDEFINED_TAGS = json.loads(PREDEFINED_TAGS_STR)
    if not isinstance(PREDEFINED_TAGS, list) or not all(
        isinstance(tag, str) for tag in PREDEFINED_TAGS
    ):
        raise ValueError("PREDEFINED_TAGS must be a JSON string array in .env file.")
except json.JSONDecodeError:
    raise ValueError("PREDEFINED_TAGS in .env file is not a valid JSON string.")

app = FastAPI()

app.mount(
    "/static", StaticFiles(directory=PROJECT_ROOT / "app" / "static"), name="static"
)
app.mount("/static_videos", StaticFiles(directory=VIDEO_FOLDER), name="static_videos")

templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@app.on_event("startup")
def on_startup():
    database.create_db_and_tables()
    index_videos()


def index_videos():
    db: Session = next(database.get_db())
    try:
        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        print(f"Starting video indexing in: {VIDEO_FOLDER}")
        count_added = 0
        for video_file in VIDEO_FOLDER.rglob("*"):
            if video_file.is_file() and video_file.suffix.lower() in video_extensions:
                abs_filepath_str = str(video_file.resolve())
                existing_video = (
                    db.query(database.Video)
                    .filter(database.Video.filepath == abs_filepath_str)
                    .first()
                )
                if not existing_video:
                    new_video = database.Video(
                        filepath=abs_filepath_str, filename=video_file.name
                    )
                    db.add(new_video)
                    count_added += 1
        if count_added > 0:
            db.commit()
        print(f"Video indexing complete. Added {count_added} new videos.")
    except Exception as e:
        print(f"Error during video indexing: {e}")
        db.rollback()
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "tags": PREDEFINED_TAGS}
    )


@app.get("/next-video", response_model=Optional[models.VideoResponse])
def get_next_video(db: Session = Depends(database.get_db)):
    video = (
        db.query(database.Video)
        .filter(database.Video.is_annotated == False) # noqa: E712
        .order_by(func.random())
        .first()
    )
    if not video:
        return None

    try:
        relative_path = Path(video.filepath).relative_to(VIDEO_FOLDER)
        web_path = f"/static_videos/{relative_path.as_posix()}"
    except ValueError:
        print(
            f"Path mismatch error for video ID {video.id}: '{video.filepath}' is not relative to '{VIDEO_FOLDER}'. Skipping video."
        )
        video.is_annotated = True
        db.commit()
        return get_next_video(db)

    return models.VideoResponse(
        id=video.id,
        filename=video.filename,
        web_path=web_path,
        is_annotated=video.is_annotated,
        tag=video.tag,
    )


@app.post("/tag-video/{video_id}", response_model=models.VideoResponse)
def tag_video_endpoint(
    video_id: int,
    tag_request: models.TagRequest,
    db: Session = Depends(database.get_db),
):
    if tag_request.tag not in PREDEFINED_TAGS:
        raise HTTPException(
            status_code=400, detail=f"Invalid tag. Must be one of {PREDEFINED_TAGS}"
        )

    video = db.query(database.Video).filter(database.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.tag = tag_request.tag
    video.is_annotated = True
    db.commit()
    db.refresh(video)

    relative_path = Path(video.filepath).relative_to(VIDEO_FOLDER)
    web_path = f"/static_videos/{relative_path.as_posix()}"

    return models.VideoResponse(
        id=video.id,
        filename=video.filename,
        web_path=web_path,
        is_annotated=video.is_annotated,
        tag=video.tag,
    )


@app.get("/stats", response_model=models.StatsResponse)
def get_stats(db: Session = Depends(database.get_db)):
    total_videos = db.query(database.Video).count()
    annotated_videos = (
        db.query(database.Video).filter(database.Video.is_annotated).count()
    )
    unannotated_videos = total_videos - annotated_videos
    return models.StatsResponse(
        total_videos=total_videos,
        annotated_videos=annotated_videos,
        unannotated_videos=unannotated_videos,
    )

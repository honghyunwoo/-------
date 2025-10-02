import glob
import os
import pathlib
from typing import Union

from fastapi import Depends, Path, Request, UploadFile, Response, StreamingResponse
from fastapi.params import File
from sqlalchemy.orm import Session

from app.controllers.v1.base import new_router
from app.database.connection import get_db
from app.models.exception import HttpException, LLMError
from app.models.schema import AudioRequest
from app.models.schema import BgmRetrieveResponse
from app.models.schema import BgmUploadResponse
from app.models.schema import SubtitleRequest
from app.models.schema import TaskDeletionResponse
from app.models.schema import TaskQueryRequest
from app.models.schema import TaskQueryResponse
from app.models.schema import TaskResponse
from app.models.schema import TaskVideoRequest
from app.models.user import User
from app.services import auth, state as sm, usage
from app.utils import utils
from app.config.config import config
from app.worker import generate_video_task

# 인증 의존성
# router = new_router(dependencies=[Depends(base.verify_token)])
router = new_router()


@router.post("/videos", response_model=TaskResponse, summary="Generate a short video")
def create_video(
    request: Request, 
    body: TaskVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user),
):
    return create_task(request, body, db, current_user, stop_at="video")


@router.post("/subtitle", response_model=TaskResponse, summary="Generate subtitle only")
def create_subtitle(
    request: Request, 
    body: SubtitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user),
):
    return create_task(request, body, db, current_user, stop_at="subtitle")


@router.post("/audio", response_model=TaskResponse, summary="Generate audio only")
def create_audio(
    request: Request, 
    body: AudioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user),
):
    return create_task(request, body, db, current_user, stop_at="audio")


def create_task(
    request: Request,
    body: Union[TaskVideoRequest, SubtitleRequest, AudioRequest],
    db: Session,
    current_user: User,
    stop_at: str,
):
    usage.check_credits(db, current_user)

    task_id = utils.get_uuid()
    try:
        task = {
            "task_id": task_id,
            "params": body.model_dump(),
        }
        sm.state.update_task(task_id, state=sm.const.TASK_STATE_PENDING)

        # Send task to Celery worker
        generate_video_task.delay(
            task_id=task_id,
            params_dict=body.model_dump(),
            user_id=current_user.id,
            stop_at=stop_at,
        )
        usage.use_credits(db, current_user)

        logger.success(f"Task created: {task_id}")
        return utils.get_response(200, task)
    except ValueError as e:
        raise HttpException(
            task_id=task_id, status_code=400, message=f"{str(e)}"
        )

from fastapi import Query


@router.get("/tasks", response_model=TaskQueryResponse, summary="Get all tasks")
def get_all_tasks(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)
):
    tasks, total = sm.state.get_all_tasks(page, page_size)

    response = {
        "tasks": tasks,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return utils.get_response(200, response)

@router.get(
    "/tasks/{task_id}", response_model=TaskQueryResponse, summary="Query task status"
)
def get_task(
    request: Request,
    task_id: str = Path(..., description="Task ID"),
    query: TaskQueryRequest = Depends(),
):
    endpoint = config.app.get("endpoint", "")
    if not endpoint:
        endpoint = str(request.base_url)
    endpoint = endpoint.rstrip("/")

    task = sm.state.get_task(task_id)
    if task:
        task_dir = utils.task_dir()

        def file_to_uri(file):
            if not file.startswith(endpoint):
                _uri_path = v.replace(task_dir, "tasks").replace("\\", "/")
                _uri_path = f"{endpoint}/{_uri_path}"
            else:
                _uri_path = file
            return _uri_path

        if "videos" in task:
            videos = task["videos"]
            urls = []
            for v in videos:
                urls.append(file_to_uri(v))
            task["videos"] = urls
        if "combined_videos" in task:
            combined_videos = task["combined_videos"]
            urls = []
            for v in combined_videos:
                urls.append(file_to_uri(v))
            task["combined_videos"] = urls
        return utils.get_response(200, task)

    raise HttpException(
        task_id=task_id, status_code=404, message=f"Task '{task_id}' not found."
    )


@router.delete(
    "/tasks/{task_id}",
    response_model=TaskDeletionResponse,
    summary="Delete a generated short video task",
)
def delete_video(request: Request, task_id: str = Path(..., description="Task ID")):
    task = sm.state.get_task(task_id)
    if task:
        tasks_dir = utils.task_dir()
        current_task_dir = os.path.join(tasks_dir, task_id)
        if os.path.exists(current_task_dir):
            shutil.rmtree(current_task_dir)

        sm.state.delete_task(task_id)
        logger.success(f"video deleted: {utils.to_json(task)}")
        return utils.get_response(200)
    raise HttpException(
        task_id=task_id, status_code=404, message=f"Task '{task_id}' not found."
    )


@router.get(
    "/musics", response_model=BgmRetrieveResponse, summary="Retrieve local BGM files"
)
def get_bgm_list(request: Request):
    suffix = "*.mp3"
    song_dir = utils.song_dir()
    files = glob.glob(os.path.join(song_dir, suffix))
    bgm_list = []
    for file in files:
        bgm_list.append(
            {
                "name": os.path.basename(file),
                "size": os.path.getsize(file),
                "file": file,
            }
        )
    response = {"files": bgm_list}
    return utils.get_response(200, response)


@router.post(
    "/musics",
    response_model=BgmUploadResponse,
    summary="Upload the BGM file to the songs directory",
)
def upload_bgm_file(request: Request, file: UploadFile = File(...)):
    # check file ext
    if file.filename.endswith("mp3"):
        song_dir = utils.song_dir()
        save_path = os.path.join(song_dir, file.filename)
        # save file
        with open(save_path, "wb+") as buffer:
            # If the file already exists, it will be overwritten
            file.file.seek(0)
            buffer.write(file.file.read())
        response = {"file": save_path}
        return utils.get_response(200, response)

    raise HttpException(
        "", status_code=400, message=f"Only *.mp3 files can be uploaded."
    )


@router.get("/stream/{file_path:path}")
async def stream_video(request: Request, file_path: str):
    tasks_dir = utils.task_dir()
    safe_path = utils.safe_file_path(base_dir=tasks_dir, file_path=file_path)
    if not safe_path:
        raise HttpException(
            status_code=400,
            message="Invalid file path.",
        )
    video_path = safe_path
    if not os.path.exists(video_path):
        raise HttpException(
            status_code=404, message="Video file not found."
        )

    range_header = request.headers.get("Range")
    video_size = os.path.getsize(video_path)
    start, end = 0, video_size - 1

    length = video_size
    if range_header:
        range_ = range_header.split("bytes=")[1]
        start, end = [int(part) if part else None for part in range_.split("-")]
        if start is None:
            start = video_size - end
            end = video_size - 1
        if end is None:
            end = video_size - 1
        length = end - start + 1

    def file_iterator(file_path, offset=0, bytes_to_read=None):
        with open(file_path, "rb") as f:
            f.seek(offset, os.SEEK_SET)
            remaining = bytes_to_read or video_size
            while remaining > 0:
                bytes_to_read = min(4096, remaining)
                data = f.read(bytes_to_read)
                if not data:
                    break
                remaining -= len(data)
                yield data

    response = StreamingResponse(
        file_iterator(video_path, start, length), media_type="video/mp4"
    )
    response.headers["Content-Range"] = f"bytes {start}-{end}/{video_size}"
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Content-Length"] = str(length)
    response.status_code = 206  # Partial Content

    return response


@router.get("/download/{file_path:path}")
async def download_video(_: Request, file_path: str):
    """
    download video
    :param _: Request request
    :param file_path: video file path, eg: /cd1727ed-3473-42a2-a7da-4faafafec72b/final-1.mp4
    :return: video file
    """
    tasks_dir = utils.task_dir()
    safe_path = utils.safe_file_path(base_dir=tasks_dir, file_path=file_path)
    if not safe_path:
        raise HttpException(
            status_code=400,
            message="Invalid file path.",
        )
    video_path = safe_path
    if not os.path.exists(video_path):
        raise HttpException(
            status_code=404, message="Video file not found."
        )

    path_obj = pathlib.Path(video_path)
    filename = path_obj.name
    extension = path_obj.suffix
    headers = {"Content-Disposition": f"attachment; filename={filename}{extension}"}
    return FileResponse(
        path=video_path,
        headers=headers,
        filename=f"{filename}{extension}",
        media_type=f"video/{extension[1:]}",
    )

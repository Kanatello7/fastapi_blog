from uuid import UUID

from fastapi import APIRouter, status

from src.auth.dependencies import RequireAdminDep
from src.posts.dependencies import TagServiceDep
from src.posts.exceptions import TagNotFoundException
from src.posts.schemas import TagCreate, TagResponse, TagUpdate

router = APIRouter()


@router.get("/{tag_id}", response_model=TagResponse, status_code=status.HTTP_200_OK)
async def get_tag(tag_id: UUID, service: TagServiceDep, admin: RequireAdminDep):
    tag = await service.get_tag(id=tag_id)
    if not tag:
        raise TagNotFoundException
    return tag


@router.get("/", response_model=list[TagResponse], status_code=status.HTTP_200_OK)
async def get_tags(service: TagServiceDep, admin: RequireAdminDep):
    return await service.get_tags()


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    new_tag: TagCreate, service: TagServiceDep, admin: RequireAdminDep
):
    return await service.create_tag(new_tag)


@router.put("/{tag_id}", status_code=status.HTTP_200_OK)
async def update_tag(
    tag_id: UUID, new_data: TagUpdate, service: TagServiceDep, admin: RequireAdminDep
):
    tag = await service.update_tag(tag_id=tag_id, data=new_data)
    if not tag:
        raise TagNotFoundException
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_200_OK)
async def delete_tag(tag_id: UUID, service: TagServiceDep, admin: RequireAdminDep):
    tag = await service.delete_tag(tag_id=tag_id)
    if not tag:
        raise TagNotFoundException
    return {"message": "successfully deleted"}

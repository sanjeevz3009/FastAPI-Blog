from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(
        min_length=1, max_length=50, description="The username of the user"
    )
    email: EmailStr = Field(
        min_length=1, max_length=120, description="The email of the user"
    )


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class PostBase(BaseModel):
    title: str = Field(
        min_length=1, max_length=100, description="The title of the post"
    )
    content: str = Field(min_length=1, description="The content of the post")


class PostCreate(PostBase):
    user_id: int # Temporary


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse

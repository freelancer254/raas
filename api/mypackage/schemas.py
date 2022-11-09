from typing import List, Union

from pydantic import BaseModel, EmailStr


class DrawBase(BaseModel):
    requestId : str
    timestamp: str
    numWords: int
    randomWords: str


class DrawCreate(DrawBase):
    pass


class Draw(DrawBase):
    username: str

    class Config:
        orm_mode = True

class DrawResponse(DrawBase):
    username: str

    class Config:
        orm_mode = True

class LatestDrawsResponse():
    latest_draws: List = []

class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    email: EmailStr
    password: str


class User(UserBase):
    key: str
    is_active: bool
    draws: List = []

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    draws: List = [None]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None

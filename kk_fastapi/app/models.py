from pydantic import BaseModel

class BeaconResponse(BaseModel):
    miner_id: str


class CoinResponse(BaseModel):
    miner_id: str
    coin_result: str


class StatusResponse(BaseModel):
    uuid: str
    h: int
    j: int


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    hashed_password: str

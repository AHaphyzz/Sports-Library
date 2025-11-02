from pydantic import BaseModel


class UserInput(BaseModel):
    country: str
    year: int


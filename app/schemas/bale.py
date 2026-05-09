from typing import Any

from pydantic import BaseModel, Field


class BaleChat(BaseModel):
    id: int | str
    type: str | None = None


class BaleUser(BaseModel):
    id: int | str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class BaleMessage(BaseModel):
    message_id: int | str | None = None
    from_user: BaleUser | None = Field(default=None, alias="from")
    chat: BaleChat
    date: int | None = None
    text: str | None = None
    contact: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class BaleUpdate(BaseModel):
    update_id: int | str | None = None
    message: BaleMessage | None = None
    callback_query: dict[str, Any] | None = None


class ReplyKeyboardMarkup(BaseModel):
    keyboard: list[list[str | dict[str, Any]]]
    resize_keyboard: bool = True
    one_time_keyboard: bool = False


class InlineKeyboardMarkup(BaseModel):
    inline_keyboard: list[list[dict[str, Any]]]

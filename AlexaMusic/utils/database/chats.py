# Copyright (C) 2025 by Alexa_Help @ Github, < https://github.com/TheTeamAlexa >
# Subscribe On YT < Jankari Ki Duniya >. All rights reserved. © Alexa © Yukki.

"""
TheTeamAlexa is a project of Telegram bots with variety of purposes.
Copyright (c) 2021 ~ Present Team Alexa <https://github.com/TheTeamAlexa>

This program is free software: you can redistribute it and can modify
as you want or you can collabe if you have new ideas.
"""


from typing import Dict, List, Union

from AlexaMusic.core.mongo import mongodb

chatsdb = db.chats


async def get_served_chats() -> list:
    chats = chatsdb.find({"chat_id": {"$lt": 0}})
    return list(await chats.to_list(length=1000000000)) if chats else []


async def is_served_chat(chat_id: int) -> bool:
    chat = await chatsdb.find_one({"chat_id": chat_id})
    return bool(chat)


async def add_served_chat(chat_id: int):
    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    return await chatsdb.insert_one({"chat_id": chat_id})


async def remove_served_chat(chat_id: int):
    is_served = await is_served_chat(chat_id)
    if not is_served:
        return
    return await chatsdb.delete_one({"chat_id": chat_id})

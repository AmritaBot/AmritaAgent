import json
from collections.abc import Generator, Sequence
from datetime import datetime
from typing import Any
from uuid import uuid4

import tomli
from amrita_core import (
    MemoryModel,
    ModelPreset,
    PresetManager,
)
from typing_extensions import Self

from amrita_agent.constants import MEMORY_SESSIONS_DIR, PRESETS_DIR


class Memory(MemoryModel):
    name: str
    session_id: str
    last_update: datetime

    def save(self):
        with open(
            MEMORY_SESSIONS_DIR / f"{self.session_id}.json", "w", encoding="u8"
        ) as f:
            json.dump(self.model_dump(), f)

    def destroy(self):
        (MEMORY_SESSIONS_DIR / f"{self.session_id}.json").unlink(True)

    @classmethod
    def load(cls, session_id: str):
        if not (MEMORY_SESSIONS_DIR / f"{session_id}.json").exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        with open(MEMORY_SESSIONS_DIR / f"{session_id}.json", encoding="u8") as f:
            return cls.model_validate(json.load(f))

    @classmethod
    def loading(cls) -> Generator[Self, Any, None]:
        for file in MEMORY_SESSIONS_DIR.glob("*.json"):
            with open(file, encoding="u8") as f:
                yield cls.model_validate(json.load(f))


class DataManager:
    _instance = None
    _name2sessionid: dict[str, str]
    _sessionid2name: dict[str, str]
    _sessionid2memory: dict[str, Memory]
    _name2presets: dict[str, ModelPreset]

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._name2sessionid = {}
            cls._sessionid2memory = {}
            cls._sessionid2name = {}
            cls._name2presets = {}
        return cls._instance

    def loads(self):
        for data in Memory.loading():
            data.save()
            session_id = data.session_id
            self._name2sessionid[data.name] = session_id
            self._sessionid2name[session_id] = data.name
            self._sessionid2memory[session_id] = data
        for file in PRESETS_DIR.glob("*.toml"):
            data = ModelPreset.model_validate(tomli.loads(file.read_text("utf-8")))
            PresetManager().add_preset(data)
            self._name2presets[data.name] = data

    def get_memory_by_name(self, name: str) -> Memory:
        return self._sessionid2memory[self._name2sessionid[name]]

    def get_memory_by_name_contains(self, name: str) -> Sequence[Memory]:
        return [
            self._sessionid2memory[v]
            for k, v in self._name2sessionid.items()
            if name.strip().lower() in k.lower().strip()
        ]

    def get_memory_by_session_id(self, sid: str) -> Memory:
        return self._sessionid2memory[sid]

    def get_session_id(self, name: str) -> str:
        return self._name2sessionid[name]

    def get_name(self, sid: str) -> str:
        return self._sessionid2name[sid]

    def new_session(self, name: str | None = None):
        name = name or f"新的对话{len(self._sessionid2memory) + 1!s}"
        session_id = uuid4().hex
        self._sessionid2name[session_id] = name
        self._name2sessionid[name] = session_id

    def init_session(self, name: str, session_id: str):
        self._sessionid2memory[session_id] = Memory(
            name=name, session_id=session_id, last_update=datetime.utcnow()
        )

    def rename(self, old: str, new: str):
        session_id = self.get_session_id(old)
        self._sessionid2name.pop(session_id)
        memory = self._sessionid2memory.pop(session_id)
        self._name2sessionid.pop(old)
        self.init_session(new, session_id)
        self._sessionid2memory[session_id] = memory

    def destroy(self, name_or_session_id: str):
        if session_id := self._name2sessionid.get(name_or_session_id):
            self._name2sessionid.pop(name_or_session_id)
        elif name_or_session_id in self._sessionid2name:
            session_id = name_or_session_id
            name = self._sessionid2name.pop(name_or_session_id)
            self._name2sessionid.pop(name)
        else:
            raise KeyError(f"No session found from `{name_or_session_id}`")
        memory = self._sessionid2memory[session_id]
        memory.destroy()

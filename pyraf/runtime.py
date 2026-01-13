from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Dict, List

from .errors import RuntimeError_

@dataclass
class Env:
    parent: Optional["Env"] = None

    def __post_init__(self):
        self.values: Dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeError_(f"Undefined variable '{name}'")

    def set(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        raise RuntimeError_(f"Undefined variable '{name}'")

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value

@dataclass
class Function:
    name: str
    params: List[str]
    body: Any  # A.Block, but keep runtime decoupled
    closure: Env

    def call(self, interp: Any, args: List[Any]) -> Any:
        if len(args) != len(self.params):
            raise RuntimeError_(f"{self.name}() expected {len(self.params)} args, got {len(args)}")
        local = Env(self.closure)
        for p, a in zip(self.params, args):
            local.define(p, a)
        try:
            interp.exec_block(self.body, local)
        except ReturnSignal as r:
            return r.value
        return None

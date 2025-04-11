import json
from dataclasses import dataclass


@dataclass
class Assistant:
    name: str
    description: str

    @property
    def prompt_format(self) -> str:
        return json.dumps({"name": self.name, "description": self.description}, indent=4)
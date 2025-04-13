from dataclasses import dataclass
from typing import List

@dataclass
class LLMJudgeCriteria:
    primary_goals: List[str]
    secondary_goals: List[str]
    tertiary_goals: List[str]
    dealbreakers: List[str]

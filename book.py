from dataclasses import dataclass, field
from typing import List

from chapter import Chapter

@dataclass
class Book:
  title: str
  art_url: str = field(default=None)
  chapters: List[Chapter] = field(default_factory=list)

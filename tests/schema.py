from pydantic import BaseModel
from typing import List, Optional

class TestCase(BaseModel):
    id: str
    prompt: str
    grader: Optional[str] = "correctness"
    expected_keywords: Optional[List[str]] = None
    expected_tool: Optional[str] = None
    must_refuse: Optional[bool] = False

class TestSuite(BaseModel):
    suite: str
    description: Optional[str] = None
    tests: List[TestCase]
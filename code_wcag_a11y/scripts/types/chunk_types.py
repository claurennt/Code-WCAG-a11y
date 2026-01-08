from typing import TypedDict
from typing_extensions import Literal


WcagVersion = Literal["2.1", "2.2"]


class BaseData(TypedDict):
    chunk_id: str
    wcag_version: WcagVersion
    id: str
    level: str
    num: str
    handle: str
    type: str
    description: str


class ParentData(TypedDict):
    parent_id: str
    parent_type: str
    parent_num: str
    parent_title: str


class GuidelineChunk(BaseData, ParentData, total=True):
    success_criteria_count: int
    success_criteria_ids: list[str]
    full_context: str


class SuccessCriterionChunk(BaseData, ParentData, total=True):
    description: str
    principle_id: str
    principle_num: str
    principle_title: str
    compliance_level: str
    versions_applicable: list[str]
    testing_requirements: list[str]
    related_requirements: list[str]
    full_context: str


class PrincipleChunk(BaseData, total=True):
    description: str
    guidelines_count: int
    guideline_ids: list[str]
    full_context: str


class TermChunk(BaseData, total=True):
    chunk_id: str
    type: str
    wcag_version: WcagVersion
    id: str
    term: str
    definition: str
    level: str
    full_context: str

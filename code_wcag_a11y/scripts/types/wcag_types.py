from __future__ import annotations

from pydantic import BaseModel, Field


class Item(BaseModel):
    handle: str | None = None
    text: str


class Detail(BaseModel):
    type: str
    items: list[Item] | None = None
    handle: str | None = None
    text: str | None = None


class AndItem(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str


class UsingItem1(BaseModel):
    id: str
    technology: str
    title: str


class UsingItem(BaseModel):
    id: str
    technology: str
    title: str
    using: list[UsingItem1] | None = None


class Technique(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str | None = None
    suffix: str | None = None
    and_: list[AndItem] | None = Field(None, alias="and")
    using: list[UsingItem] | None = None


class Technique1(BaseModel):
    id: str
    technology: str
    title: str


class Group(BaseModel):
    id: str
    title: str
    techniques: list[Technique1]


class UsingItem3(BaseModel):
    id: str
    technology: str
    title: str


class AndItem1(BaseModel):
    id: str
    technology: str
    title: str


class UsingItem2(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str | None = None
    using: list[UsingItem3] | None = None
    and_: list[AndItem1] | None = Field(None, alias="and")


class AndItem2(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str


class SufficientItem(BaseModel):
    title: str | None = None
    techniques: list[Technique] | None = None
    groups: list[Group] | None = None
    id: str | None = None
    technology: str | None = None
    suffix: str | None = None
    using: list[UsingItem2] | None = None
    and_: list[AndItem2] | None = Field(None, alias="and")
    prefix: str | None = None
    note: str | None = None


class AndItem3(BaseModel):
    title: str
    id: str | None = None
    technology: str | None = None


class AdvisoryItem(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str | None = None
    and_: list[AndItem3] | None = Field(None, alias="and")
    prefix: str | None = None


class FailureItem(BaseModel):
    id: str | None = None
    technology: str | None = None
    title: str


class Techniques(BaseModel):
    sufficient: list[SufficientItem] | None = None
    advisory: list[AdvisoryItem] | None = None
    failure: list[FailureItem] | None = None
    sufficientNote: str | None = None


class Successcriterion(BaseModel):
    id: str
    num: str
    alt_id: list[str]
    content: str
    handle: str
    title: str
    versions: list[str]
    level: str
    details: list[Detail]
    techniques: Techniques


class Guideline(BaseModel):
    id: str
    num: str
    alt_id: list[str]
    content: str
    handle: str
    title: str
    versions: list[str]
    successcriteria: list[Successcriterion]


class Principle(BaseModel):
    id: str
    num: str
    content: str
    handle: str
    title: str
    versions: list[str]
    guidelines: list[Guideline]


class Term(BaseModel):
    id: str
    definition: str
    name: str


class WCAGData(BaseModel):
    principles: list[Principle]
    terms: list[Term]

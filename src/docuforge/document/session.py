"""Editing session with snapshot-based undo and redo.

Commands are intentionally independent of the UI toolkit so ribbon actions,
menus, keyboard shortcuts and tests can share the same editing operations.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Protocol

from docuforge.document.model import Document, DynamicField, Paragraph, TextRun


class EditCommand(Protocol):
    def apply(self, document: Document) -> None: ...


@dataclass(slots=True)
class InsertParagraph:
    section_index: int
    paragraph_index: int
    paragraph: Paragraph

    def apply(self, document: Document) -> None:
        section = document.sections[self.section_index]
        if not 0 <= self.paragraph_index <= len(section.blocks):
            raise IndexError("Paragraph insertion position is outside the section.")
        section.blocks.insert(self.paragraph_index, deepcopy(self.paragraph))


@dataclass(slots=True)
class InsertText:
    section_index: int
    paragraph_index: int
    text: str

    def apply(self, document: Document) -> None:
        section = document.sections[self.section_index]
        paragraph = section.blocks[self.paragraph_index]
        if not isinstance(paragraph, Paragraph):
            raise TypeError("Text can only be inserted into a paragraph.")
        if not self.text:
            return
        if paragraph.runs and isinstance(paragraph.runs[-1], TextRun):
            paragraph.runs[-1].text += self.text
        else:
            paragraph.runs.append(TextRun(self.text))


@dataclass(slots=True)
class InsertInlineField:
    """Insert a typed field at a character offset inside a paragraph."""

    section_index: int
    paragraph_index: int
    run_index: int
    offset: int
    field: DynamicField

    def apply(self, document: Document) -> None:
        paragraph = document.sections[self.section_index].blocks[self.paragraph_index]
        if not isinstance(paragraph, Paragraph):
            raise TypeError("Fields can only be inserted into a paragraph.")
        if not 0 <= self.run_index <= len(paragraph.runs):
            raise IndexError("Inline insertion position is outside the paragraph.")
        if self.run_index == len(paragraph.runs):
            if self.offset != 0:
                raise IndexError("Offset must be zero after the last run.")
            paragraph.runs.append(deepcopy(self.field))
            return
        target = paragraph.runs[self.run_index]
        if not isinstance(target, TextRun):
            if self.offset != 0:
                raise IndexError("A field node only accepts offset zero.")
            paragraph.runs.insert(self.run_index, deepcopy(self.field))
            return
        if not 0 <= self.offset <= len(target.text):
            raise IndexError("Character offset is outside the text run.")
        before, after = deepcopy(target), deepcopy(target)
        before.text, after.text = target.text[:self.offset], target.text[self.offset:]
        replacement = ([before] if before.text else []) + [deepcopy(self.field)]
        if after.text:
            replacement.append(after)
        paragraph.runs[self.run_index:self.run_index + 1] = replacement


@dataclass(slots=True)
class RemoveInlineNode:
    """Remove an inline node from a paragraph."""

    section_index: int
    paragraph_index: int
    run_index: int

    def apply(self, document: Document) -> None:
        paragraph = document.sections[self.section_index].blocks[self.paragraph_index]
        if not isinstance(paragraph, Paragraph):
            raise TypeError("Inline nodes can only be removed from a paragraph.")
        if not 0 <= self.run_index < len(paragraph.runs):
            raise IndexError("Inline node position is outside the paragraph.")
        paragraph.runs.pop(self.run_index)


class EditorSession:
    """Owns an editable document and its undo/redo history."""

    def __init__(self, document: Document | None = None, history_limit: int = 200) -> None:
        self.document = deepcopy(document) if document is not None else Document()
        self.history_limit = max(1, history_limit)
        self._undo: list[Document] = []
        self._redo: list[Document] = []
        self.dirty = False

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def execute(self, command: EditCommand) -> None:
        before = deepcopy(self.document)
        command.apply(self.document)
        if self.document == before:
            return
        self._undo.append(before)
        if len(self._undo) > self.history_limit:
            self._undo.pop(0)
        self._redo.clear()
        self.dirty = True

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(deepcopy(self.document))
        self.document = self._undo.pop()
        self.dirty = True
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(deepcopy(self.document))
        self.document = self._redo.pop()
        self.dirty = True
        return True

    def mark_saved(self) -> None:
        self.dirty = False

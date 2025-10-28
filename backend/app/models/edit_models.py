from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Literal, Optional


EditType = Literal["voiceover", "text_overlay", "trim", "filter"]
EditStatus = Literal["pending", "applied", "reverted", "overwritten", "superseded"]


@dataclass
class Edit:
    id: str
    type: EditType
    params: dict[str, Any]
    timestamp: str
    status: EditStatus
    result_video_url: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Edit":
        return cls(**data)


@dataclass
class EditQueue:
    session_id: str
    original_video_url: str
    edits: list[Edit]
    current_video_url: str
    video_id: Optional[str] = None
    
    def add_edit(self, edit: Edit) -> None:
        self.edits.append(edit)
    
    def remove_edit(self, edit_id: str) -> bool:
        initial_length = len(self.edits)
        self.edits = [e for e in self.edits if e.id != edit_id]
        return len(self.edits) < initial_length
    
    def update_edit(self, edit_id: str, new_params: dict[str, Any]) -> bool:
        for edit in self.edits:
            if edit.id == edit_id:
                edit.params.update(new_params)
                edit.timestamp = datetime.now().isoformat()
                return True
        return False
    
    def get_edit(self, edit_id: str) -> Optional[Edit]:
        for edit in self.edits:
            if edit.id == edit_id:
                return edit
        return None
    
    def get_applied_edits(self) -> list[Edit]:
        return [e for e in self.edits if e.status == "applied"]
    
    def find_edit_by_type(self, edit_type: EditType) -> Optional[Edit]:
        for edit in reversed(self.edits):
            if edit.type == edit_type and edit.status == "applied":
                return edit
        return None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "original_video_url": self.original_video_url,
            "edits": [e.to_dict() for e in self.edits],
            "current_video_url": self.current_video_url,
            "video_id": self.video_id
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EditQueue":
        edits = [Edit.from_dict(e) for e in data.get("edits", [])]
        return cls(
            session_id=data["session_id"],
            original_video_url=data["original_video_url"],
            edits=edits,
            current_video_url=data["current_video_url"],
            video_id=data.get("video_id")
        )

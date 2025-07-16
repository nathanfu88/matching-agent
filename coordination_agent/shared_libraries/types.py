from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class UserGroup(BaseModel):
    """Represents a group of matched users."""
    user_ids: list[str] = Field(
        ...,
        description="List of user IDs in this group",
        min_length=1
    )
    group_rationale: Optional[str] = Field(
        None,
        description="Explanation of why these users were grouped together"
    )
    complementary_traits: Optional[list[str]] = Field(
        None,
        description="List of complementary traits that make this group effective"
    )
    
    model_config = {
        "extra": "forbid"  # Prevent extra fields
    }


class MatcherResponse(BaseModel):
    """Response model for the matcher subagent."""
    matched_groups: dict[str, UserGroup] = Field(
        ...,
        description="Dictionary of user groups created by the matcher, keyed by group ID",
        min_length=1
    )
    matching_strategy: Optional[str] = Field(
        None,
        description="Overall strategy used for creating these matches"
    )
    
    
    @classmethod
    def from_list(cls, groups: list[UserGroup], **data) -> 'MatcherResponse':
        """Create a MatcherResponse from a list of UserGroups."""
        return cls(
            matched_groups={str(uuid4()): group for group in groups},
            **data
        )

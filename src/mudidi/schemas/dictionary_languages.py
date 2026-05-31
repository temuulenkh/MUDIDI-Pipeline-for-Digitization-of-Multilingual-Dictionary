"""Per-dictionary language roles for Stage 2 and MDF export."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Recommended layout labels (not enforced — any string is accepted).
RECOMMENDED_LAYOUTS = (
    "inline_bilingual",
    "column_bilingual",
    "inline_trilingual",
    "column_trilingual",
)


class SourceLanguageConfig(BaseModel):
    """Vernacular / headword language."""

    model_config = ConfigDict(extra="ignore")

    language: str = Field(description="Human-readable source language name.")
    column_id: Optional[str] = Field(
        default=None,
        description="Stage-1 column_id for headwords when layout is column_trilingual.",
    )


class TargetLanguageConfig(BaseModel):
    """One gloss/translation language."""

    model_config = ConfigDict(extra="ignore")

    language: str = Field(description="Human-readable target language name.")
    column_id: Optional[str] = Field(
        default=None,
        description="Stage-1 column_id for this gloss when layout is column_trilingual.",
    )


class DictionaryLanguagesConfig(BaseModel):
    """Loaded from dictionary_languages.yaml in each sample folder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    layout: str = Field(
        description=(
            "Free-form layout label for Pass 1 (recommended values: "
            + ", ".join(RECOMMENDED_LAYOUTS)
            + ")."
        ),
    )
    layout_description: Optional[str] = Field(
        default=None,
        validation_alias="layout-description",
        serialization_alias="layout-description",
        description=(
            "Optional prose explaining what this layout means for this dictionary; "
            "included in the Stage 2 Pass 1 hint when set."
        ),
    )
    source: SourceLanguageConfig
    targets: List[TargetLanguageConfig] = Field(min_length=1)
    writing_system: str = Field(
        default="",
        description="From dictionary_metadata.csv when matched.",
    )
    metadata_archive: str = Field(
        default="",
        description="First CSV column (archive id) when matched.",
    )

    def target_codes(self) -> List[str]:
        """Stable internal keys for MDF export (derived from ``language`` names)."""
        from mudidi.utils.dictionary_languages import language_key

        return [language_key(t.language) for t in self.targets]

    def pass1_config_hint(self) -> str:
        """Short inline hint for Stage 2 Pass 1 prompts."""
        target_names = ", ".join(t.language for t in self.targets)
        hint = (
            f"\n3. Language roles: layout={self.layout}, "
            f"source={self.source.language}, targets=[{target_names}]."
        )
        desc = (self.layout_description or "").strip()
        if desc:
            hint += f"\n   Layout note: {desc}\n"
        else:
            hint += "\n"
        return hint

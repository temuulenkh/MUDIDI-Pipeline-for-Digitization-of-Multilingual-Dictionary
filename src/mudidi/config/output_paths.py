"""Output directory layout for benchmark vs inference runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mudidi.config.run_config import RunConfig
from mudidi.utils.stage1_input import stage1_experiment_dir, stage1_gold_dir


@dataclass(frozen=True)
class OutputLayout:
    """Resolved stage-1/stage-2 directories for one run."""

    output_dir: Path
    stage1_root: Path
    stage2_root: Path
    field_cheatsheet_path: Path
    inference: bool

    def stage1_page_dir(self, stem: str) -> Path:
        if self.inference:
            return self.stage1_root / stem
        return self.stage1_root / stem

    def stage2_page_dir(self, stem: str) -> Path:
        return self.stage2_root / stem


def resolve_output_layout(config: RunConfig) -> OutputLayout:
    """Return stage output roots for the given run configuration."""
    if config.benchmark:
        stage1_root = stage1_experiment_dir(
            config.output_dir,
            config.experiment_name,
            subdir=config.stage1_output_subdir,
        )
        stage2_root = config.output_dir / "stage-2" / (config.stage2_experiment_name or "default")
        cheatsheet = stage2_root / "field_cheatsheet.json"
    else:
        stage1_root = config.output_dir / "stage-1"
        stage2_root = config.output_dir / "stage-2"
        cheatsheet = config.output_dir / "field_cheatsheet.json"
    return OutputLayout(
        output_dir=config.output_dir,
        stage1_root=stage1_root,
        stage2_root=stage2_root,
        field_cheatsheet_path=cheatsheet,
        inference=not config.benchmark,
    )


def stage1_predictions_page_dir(
    output_dir: Path,
    stem: str,
    *,
    benchmark: bool,
    experiment_name: str = "default",
    stage1_output_subdir: str = "stage-1",
) -> Path:
    """Directory holding Stage-1 prediction artifacts for one page."""
    if benchmark:
        return stage1_experiment_dir(
            output_dir, experiment_name, subdir=stage1_output_subdir
        ) / stem
    return output_dir / "stage-1" / stem


def stage1_gold_page_dir(output_dir: Path, stem: str) -> Path:
    """Directory holding Stage-1 gold artifacts for one page."""
    return stage1_gold_dir(output_dir) / stem

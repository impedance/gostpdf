from pathlib import Path

import pytest

from md2pdf.config import ProjectConfig, load_config


def _write_default_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
content_root: content
images_root: public/images
style: style
template: templates/gost.tex
""".strip()
    )


def _prepare_project_layout(base_dir: Path) -> None:
    (base_dir / "content").mkdir(parents=True)
    (base_dir / "public" / "images").mkdir(parents=True)
    (base_dir / "styles").mkdir(parents=True)
    (base_dir / "styles" / "style.yaml").write_text("stub style")
    (base_dir / "templates").mkdir(parents=True)
    (base_dir / "templates" / "gost.tex").write_text("% template")


def test_load_config_resolves_paths(tmp_path: Path) -> None:
    _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_default_config(config_path)

    project_config = load_config(config_path)

    assert isinstance(project_config, ProjectConfig)
    assert project_config.content_root == tmp_path / "content"
    assert project_config.images_root == tmp_path / "public" / "images"
    assert project_config.style == tmp_path / "styles" / "style.yaml"
    assert project_config.template == tmp_path / "templates" / "gost.tex"
    assert project_config.filters == ()
    assert project_config.output is None


def test_missing_content_root_raises(tmp_path: Path) -> None:
    _prepare_project_layout(tmp_path)
    (tmp_path / "content").rmdir()
    config_path = tmp_path / "config" / "project.yml"
    _write_default_config(config_path)

    with pytest.raises(ValueError, match="Missing directory"):
        load_config(config_path)


def test_missing_style_file_raises(tmp_path: Path) -> None:
    _prepare_project_layout(tmp_path)
    (tmp_path / "styles" / "style.yaml").unlink()
    config_path = tmp_path / "config" / "project.yml"
    _write_default_config(config_path)

    with pytest.raises(ValueError, match="Missing file"):
        load_config(config_path)


def test_missing_template_file_raises(tmp_path: Path) -> None:
    _prepare_project_layout(tmp_path)
    (tmp_path / "templates" / "gost.tex").unlink()
    config_path = tmp_path / "config" / "project.yml"
    _write_default_config(config_path)

    with pytest.raises(ValueError, match="Missing file"):
        load_config(config_path)

from pathlib import Path

import pytest

from gaming_script_generator.thumbnail_renderer import render_thumbnail


def test_render_thumbnail_writes_1280_by_720_svg_and_escapes_text(tmp_path: Path) -> None:
    path = render_thumbnail(
        {
            "title": "A&B: jogos",
            "overlay_text": "TOP 3 <JOGOS>",
            "composition": "Controle no centro",
        },
        1,
        tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    assert path.suffix == ".svg"
    assert 'width="1280" height="720"' in content
    assert "TOP 3 &lt;JOGOS&gt;" in content
    assert "A&amp;B: jogos" in content


def test_render_thumbnail_rejects_zero_index(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="começar em 1"):
        render_thumbnail({"title": "Teste"}, 0, tmp_path)

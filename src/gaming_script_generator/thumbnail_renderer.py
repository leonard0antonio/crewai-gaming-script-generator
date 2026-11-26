"""Renderização local de conceitos de thumbnail como arquivos SVG."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


_PALETTE = (
    ("#10152f", "#39216b", "#ffcb45"),
    ("#102c35", "#176d72", "#ff5d73"),
    ("#311625", "#9d3e50", "#65e6c1"),
)


def _text(value: Any, default: str) -> str:
    value = str(value or "").strip()
    return value if value else default


def _wrap(value: str, max_chars: int = 20, max_lines: int = 3) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max_chars - 1].rstrip() + "…"
    return lines


def render_thumbnail(option: dict[str, Any], index: int, output_path: Path) -> Path:
    """Cria uma thumbnail 1280x720 com título e arte vetorial abstrata."""
    if index < 1:
        raise ValueError("O índice da opção deve começar em 1.")

    background_a, background_b, accent = _PALETTE[(index - 1) % len(_PALETTE)]
    headline = _text(option.get("overlay_text"), _text(option.get("title"), "GAMES EM DESTAQUE"))
    title = _text(option.get("title"), f"Opção {index}")
    safe_title = html.escape(title)
    lines = _wrap(headline.upper())
    text_elements = "\n".join(
        f'<text x="88" y="{330 + row * 100}" class="headline">{html.escape(line)}</text>'
        for row, line in enumerate(lines)
    )
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", title).strip("-").lower() or f"opcao-{index}"
    output_path.mkdir(parents=True, exist_ok=True)
    destination = output_path / f"thumbnail-{index}-{filename}.svg"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc">
  <title id="title">{safe_title}</title>
  <desc id="desc">Thumbnail de vídeo gamer: {html.escape(_text(option.get("composition"), headline))}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{background_a}"/>
      <stop offset="1" stop-color="{background_b}"/>
    </linearGradient>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{accent}"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="7"/>
      <feOffset dy="7"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.7"/></feComponentTransfer>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .headline {{ font: 900 78px Impact, 'Arial Black', sans-serif; fill: #fff; stroke: #111321; stroke-width: 7px; paint-order: stroke fill; filter: url(#shadow); }}
      .label {{ font: 800 24px Arial, sans-serif; letter-spacing: 3px; fill: #151523; }}
    </style>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)"/>
  <path d="M820 0h460v720H650z" fill="{accent}" opacity=".18"/>
  <circle cx="1000" cy="330" r="240" fill="url(#glow)" opacity=".16"/>
  <circle cx="1120" cy="170" r="130" fill="{accent}" opacity=".32"/>
  <path d="M0 620L690 0h150L150 720H0z" fill="#fff" opacity=".06"/>
  <g transform="translate(845 260) rotate(-12)">
    <path d="M84 114c-38-11-67 13-79 59l-31 114c-8 31 25 48 48 26l82-71h102l82 71c23 22 56 5 48-26l-31-114c-12-46-41-70-79-59-41 12-84 12-142 0z" fill="#121522" stroke="#fff" stroke-width="9"/>
    <path d="M53 176v82m-41-41h82" stroke="{accent}" stroke-width="17" stroke-linecap="round"/>
    <circle cx="248" cy="182" r="17" fill="#ff5364"/>
    <circle cx="289" cy="224" r="17" fill="#5be0c2"/>
    <circle cx="207" cy="224" r="17" fill="#ffd34e"/>
    <circle cx="248" cy="265" r="17" fill="#65a8ff"/>
    <path d="M119 300h112" stroke="#fff" stroke-width="5" opacity=".7"/>
  </g>
  <rect x="76" y="106" width="410" height="48" rx="8" fill="{accent}"/>
  <text x="96" y="138" class="label">UNIVERSO GAMER  •  OPÇÃO {index}</text>
  {text_elements}
  <text x="88" y="636" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#fff" opacity=".88">{safe_title}</text>
</svg>
"""
    destination.write_text(svg, encoding="utf-8")
    return destination

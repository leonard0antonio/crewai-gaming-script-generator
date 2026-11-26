"""Interface de linha de comando e gravação dos resultados."""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from gaming_script_generator.crew import run_generation
from gaming_script_generator.thumbnail_renderer import render_thumbnail


def generate(query: str, output_dir: Path) -> Path:
    result = run_generation(query)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = [
        render_thumbnail(option, index, output_dir / "thumbnails")
        for index, option in enumerate(result.thumbnail_options, start=1)
    ]
    selected = next(
        option for option in result.thumbnail_options if option["id"] == result.selected_option_id
    )
    selected_index = result.thumbnail_options.index(selected)

    report = [
        f"# Roteiro: {query}",
        "",
        result.script,
        "",
        "## Opções de thumbnail",
    ]
    for index, (option, image_path) in enumerate(
        zip(result.thumbnail_options, image_paths), start=1
    ):
        report.extend(
            [
                "",
                f"### Opção {index}: {option['title']}",
                f"- Texto: {option['overlay_text']}",
                f"- Composição: {option['composition']}",
                f"- Prompt visual: {option['image_prompt']}",
                f"- Arquivo SVG: `{image_path.name}`",
            ]
        )
    report.extend(
        [
            "",
            "## Thumbnail escolhida",
            f"**Opção {selected_index + 1}: {selected['title']}**",
            "",
            result.selection_reason,
            "",
        ]
    )
    report_path = output_dir / "roteiro-e-thumbnails.md"
    report_path.write_text("\n".join(report), encoding="utf-8")
    return report_path


def main(inputs: dict[str, str] | None = None) -> None:
    load_dotenv()
    if inputs is not None:
        query = inputs.get("query", "").strip()
        if not query:
            raise ValueError("Informe o tema em inputs['query'].")
        destination = Path(inputs.get("output_dir", "output"))
    else:
        parser = argparse.ArgumentParser(
            description="Gera um roteiro de games e três thumbnails para YouTube."
        )
        parser.add_argument("--query", required=True, help="Tema do vídeo.")
        parser.add_argument("--output-dir", default="output", help="Diretório dos arquivos gerados.")
        args = parser.parse_args()
        query = args.query.strip()
        destination = Path(args.output_dir)
        if not query:
            parser.error("--query não pode ficar vazio.")

    report_path = generate(query, destination)
    print(f"Relatório e thumbnails salvos em: {report_path.resolve()}")


if __name__ == "__main__":
    main()

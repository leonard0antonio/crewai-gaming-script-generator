# Gerador de roteiros e thumbnails para games

Aplicação Python com CrewAI que pesquisa um tema, cria um roteiro para YouTube, propõe três direções de thumbnail e revisa o roteiro e a escolha. As thumbnails são renderizadas localmente em SVG (1280 × 720), sem depender de um serviço de geração de imagens.

## Requisitos

- Python 3.10 ou superior
- Chave de API para o modelo de linguagem escolhido
- Chave Serper para pesquisa web

## Instalação

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

Edite `.env` e preencha `OPENAI_API_KEY` e `SERPER_API_KEY`. `LLM_MODEL` pode ser ajustado para outro modelo aceito pelo CrewAI.

## Uso

```powershell
gaming-script --query "Melhores jogos de 2020"
```

Ou, como módulo Python:

```python
from gaming_script_generator.cli import main

main(inputs={"query": "Melhores jogos de 2020"})
```

O diretório `output/` conterá `roteiro-e-thumbnails.md` e três SVGs em `output/thumbnails/`. A opção selecionada e sua justificativa aparecem no relatório. Também é possível informar outro destino na CLI com `--output-dir`.

## Testes

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

"""Definição dos agentes e tarefas da equipe CrewAI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import SerperDevTool
from pydantic import BaseModel


@dataclass
class GenerationResult:
    script: str
    thumbnail_options: list[dict[str, Any]]
    selected_option_id: str
    selection_reason: str


class ThumbnailOption(BaseModel):
    id: str
    title: str
    composition: str
    overlay_text: str
    image_prompt: str


class ThumbnailSet(BaseModel):
    options: list[ThumbnailOption]


class ReviewResult(BaseModel):
    reviewed_script: str
    selected_option_id: str
    selection_reason: str


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    structured = getattr(value, "pydantic", None)
    if structured is not None:
        return _as_dict(structured)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    raise TypeError("A saída estruturada do agente não está no formato esperado.")


def _thumbnail_list(value: Any) -> list[dict[str, Any]]:
    data = _as_dict(value)
    options = data.get("options")
    if not isinstance(options, list) or len(options) != 3:
        raise ValueError("O criador de thumbnails deve retornar exatamente três opções.")
    normalized = [_as_dict(option) for option in options]
    required = ("id", "title", "composition", "overlay_text", "image_prompt")
    for option in normalized:
        missing = [field for field in required if not str(option.get(field, "")).strip()]
        if missing:
            raise ValueError(f"Opção de thumbnail incompleta; campos ausentes: {', '.join(missing)}.")
    if len({option["id"] for option in normalized}) != 3:
        raise ValueError("As opções de thumbnail devem ter IDs distintos.")
    return normalized


def run_generation(query: str) -> GenerationResult:
    """Executa pesquisa, roteiro, conceitos visuais e revisão em sequência."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY no arquivo .env antes de executar.")
    if not os.getenv("SERPER_API_KEY"):
        raise RuntimeError("Defina SERPER_API_KEY no arquivo .env para habilitar a pesquisa.")

    search = SerperDevTool()
    llm = LLM(model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"))

    writer = Agent(
        role="Roteirista de vídeos de games",
        goal="Criar roteiros completos, envolventes, precisos e adequados ao YouTube.",
        backstory=(
            "Você é um roteirista experiente em videogames, storytelling e retenção de audiência. "
            "Pesquisa fatos atuais e diferencia claramente fatos confirmados de opinião."
        ),
        tools=[search],
        llm=llm,
        verbose=True,
    )
    designer = Agent(
        role="Diretor de arte e designer de thumbnails",
        goal="Criar três direções visuais distintas, legíveis e fiéis ao roteiro.",
        backstory=(
            "Você projeta thumbnails de alto contraste para YouTube. "
            "Evita logos, personagens protegidos e promessas que o roteiro não cumpre."
        ),
        llm=llm,
        verbose=True,
    )
    reviewer = Agent(
        role="Revisor editorial e diretor criativo",
        goal="Revisar o roteiro e escolher a thumbnail mais forte e fiel ao vídeo.",
        backstory=(
            "Você revisa clareza, ritmo, coerência factual e aderência entre roteiro e imagem. "
            "Escolhe uma opção por mérito editorial, não por preferência arbitrária."
        ),
        llm=llm,
        verbose=True,
    )

    script_task = Task(
        description=(
            "Pesquise o tema abaixo usando fontes atuais e confiáveis. Escreva um roteiro completo "
            "para um vídeo de YouTube em português do Brasil, com título, gancho inicial, introdução, "
            "blocos com narração e sugestões visuais, transições, conclusão e chamada para ação. "
            "Inclua fontes consultadas com URLs e não invente dados. Tema: {query}"
        ),
        expected_output=(
            "Roteiro pronto para gravação, organizado por cenas e com fontes/URLs ao final."
        ),
        agent=writer,
    )
    thumbnail_task = Task(
        description=(
            "Com base no roteiro produzido, crie exatamente três opções visuais bem diferentes. "
            "Retorne somente um objeto JSON com a chave 'options', contendo três objetos. "
            "Cada objeto deve ter: id ('opcao_1', 'opcao_2' ou 'opcao_3'), title (curto), "
            "composition (descrição visual), overlay_text (até 5 palavras, em português) e "
            "image_prompt (prompt detalhado para ilustração original, sem texto na imagem). "
            "As propostas devem destacar ideias reais do roteiro e funcionar em tela pequena."
        ),
        expected_output="JSON válido com exatamente três opções e os cinco campos solicitados.",
        agent=designer,
        context=[script_task],
        output_json=ThumbnailSet,
    )
    review_task = Task(
        description=(
            "Revise integralmente o roteiro, corrigindo linguagem, estrutura, afirmações sem apoio "
            "e fluidez sem remover as fontes. Escolha a opção de thumbnail mais clara, atraente e "
            "fiel. Retorne somente JSON válido com as chaves 'reviewed_script', "
            "'selected_option_id' (ID exato de uma das três opções) e 'selection_reason'. "
            "Roteiro e opções estão nas tarefas anteriores."
        ),
        expected_output=(
            "JSON válido com o roteiro revisado, o ID da opção selecionada e uma justificativa."
        ),
        agent=reviewer,
        context=[script_task, thumbnail_task],
        output_json=ReviewResult,
    )

    crew = Crew(
        agents=[writer, designer, reviewer],
        tasks=[script_task, thumbnail_task, review_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff(inputs={"query": query})

    options = _thumbnail_list(thumbnail_task.output)
    review = _as_dict(review_task.output)
    reviewed_script = str(review.get("reviewed_script", "")).strip()
    selected_id = str(review.get("selected_option_id", "")).strip()
    reason = str(review.get("selection_reason", "")).strip()
    valid_ids = {option["id"] for option in options}
    if not reviewed_script or selected_id not in valid_ids or not reason:
        raise ValueError("A revisão final não retornou roteiro, opção válida e justificativa.")

    return GenerationResult(
        script=reviewed_script,
        thumbnail_options=options,
        selected_option_id=selected_id,
        selection_reason=reason,
    )

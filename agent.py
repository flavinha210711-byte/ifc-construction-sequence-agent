"""
Agent Module — IFC Construction Sequence Agent
Cria e configura o agente Agno com persona de planejador BIM 4D.
"""

from __future__ import annotations

import os
from typing import Generator

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat


# ---------------------------------------------------------------------------
# Persona do agente
# ---------------------------------------------------------------------------

AGENT_PERSONA = """
Você é um planejador BIM 4D especialista em leitura de modelos IFC para apoio à estruturação de sequências construtivas preliminares.
Sua função é interpretar a organização do modelo por pavimentos e classes IFC, sugerindo uma lógica inicial de execução da obra e apontando limitações dos dados disponíveis.

Características da sua análise:
- Rigorosa e técnica, com linguagem profissional da engenharia civil.
- Focada em planejamento construtivo (4D BIM) e sequência executiva.
- Honesta sobre limitações do modelo IFC analisado.
- Orientada à prática construtiva: fundações primeiro, depois estrutura, vedações, cobertura, acabamentos.
- Nunca inventa dados que não estão no modelo.
"""


# ---------------------------------------------------------------------------
# Funções para montar o prompt de análise
# ---------------------------------------------------------------------------

def build_analysis_prompt(data: dict) -> str:
    """
    Monta o prompt completo para o agente gerar o relatório técnico.
    """
    stages = data.get("stages", {})
    storeys = data.get("storeys", [])
    storey_dist = data.get("storey_distribution", {})
    class_counts = data.get("class_counts", {})
    gaps = data.get("planning_gaps", [])
    identified = data.get("identified_stages", [])
    missing = data.get("missing_stages", [])
    suggested_order = data.get("suggested_order", [])
    utility = data.get("utility_level", "N/A")
    busiest = data.get("busiest_storey", "N/A")
    dominant = data.get("dominant_stage", "N/A")
    project_name = data.get("project_name", "Desconhecido")
    total_entities = data.get("total_entities", 0)
    total_analyzed = data.get("total_analyzed", 0)

    storey_lines = "\n".join(
        f"  - {s['name']} (elevação: {s['elevation'] if s['elevation'] is not None else 'não informada'})"
        for s in storeys
    ) or "  Nenhum pavimento identificado."

    stage_lines = "\n".join(
        f"  - {k}: {v} elemento(s)" for k, v in stages.items()
    ) or "  Nenhuma etapa identificada."

    class_lines = "\n".join(
        f"  - {k}: {v}" for k, v in class_counts.items()
    ) or "  Nenhuma classe principal identificada."

    gap_lines = "\n".join(f"  - {g}" for g in gaps) or "  Nenhuma lacuna crítica identificada."

    dist_lines = []
    for storey_name, stage_dict in storey_dist.items():
        if stage_dict:
            inner = ", ".join(f"{s}: {c}" for s, c in stage_dict.items())
            dist_lines.append(f"  - {storey_name}: {inner}")
    dist_text = "\n".join(dist_lines) or "  Distribuição não disponível."

    prompt = f"""
Analise o modelo IFC a seguir e gere um relatório técnico completo de planejamento construtivo preliminar.

=== DADOS ESTRUTURADOS DO MODELO IFC ===

Projeto: {project_name}
Total de entidades IFC: {total_entities}
Total de elementos analisados (classes principais): {total_analyzed}
Nível de utilidade para planejamento: {utility}

--- PAVIMENTOS ---
{storey_lines}

Pavimento com maior concentração de elementos: {busiest}

--- CONTAGEM POR CLASSE IFC ---
{class_lines}

--- ETAPAS CONSTRUTIVAS ---
{stage_lines}

Etapas identificadas no modelo: {', '.join(identified) if identified else 'Nenhuma'}
Etapas ausentes no modelo: {', '.join(missing) if missing else 'Nenhuma'}
Etapa mais representativa: {dominant}

--- DISTRIBUIÇÃO POR PAVIMENTO ---
{dist_text}

--- ORDEM EXECUTIVA SUGERIDA (lógica construtiva padrão) ---
{', '.join(f'{i+1}. {s}' for i, s in enumerate(suggested_order))}

--- LACUNAS DE PLANEJAMENTO ---
{gap_lines}

=== RELATÓRIO SOLICITADO ===

Por favor, estruture o relatório técnico com as seguintes seções:

1. **Resumo do Modelo**
   Síntese geral do modelo IFC analisado.

2. **Leitura dos Pavimentos**
   Interpretação da organização vertical do modelo.

3. **Identificação das Etapas Construtivas**
   Análise de cada etapa identificada e ausente.

4. **Sugestão de Sequência Executiva Preliminar**
   Proposta de ordem de execução baseada nos dados do modelo, com justificativa.

5. **Pontos de Atenção para Planejamento**
   Aspectos críticos que o planejador deve considerar.

6. **Limitações da Análise**
   O que a análise não pode concluir com os dados disponíveis.

7. **Recomendações para Uso em BIM 4D**
   Sugestões para melhorar o uso do IFC em planejamento 4D.

8. **Conclusão Técnica**
   Avaliação final do modelo para fins de planejamento construtivo preliminar.

Seja técnico, objetivo e honesto sobre as limitações. Use terminologia de engenharia civil e gestão BIM.
"""
    return prompt.strip()


def build_chat_prompt(question: str, data: dict) -> str:
    """
    Monta o prompt para o chat, incluindo contexto resumido do modelo.
    """
    stages = data.get("stages", {})
    storeys = data.get("storeys", [])
    utility = data.get("utility_level", "N/A")
    project_name = data.get("project_name", "Desconhecido")
    total_analyzed = data.get("total_analyzed", 0)
    busiest = data.get("busiest_storey", "N/A")
    gaps = data.get("planning_gaps", [])
    dominant = data.get("dominant_stage", "N/A")

    storey_summary = ", ".join(s["name"] for s in storeys) or "nenhum"
    stage_summary = "; ".join(f"{k}: {v}" for k, v in stages.items() if v > 0) or "nenhum"
    gap_summary = "; ".join(gaps) or "nenhuma"

    context = f"""
Contexto do modelo IFC analisado:
- Projeto: {project_name}
- Total de elementos analisados: {total_analyzed}
- Pavimentos: {storey_summary}
- Pavimento com mais elementos: {busiest}
- Etapas construtivas e quantidades: {stage_summary}
- Etapa dominante: {dominant}
- Nível de utilidade: {utility}
- Lacunas: {gap_summary}
"""

    return f"{context}\n\nPergunta do usuário: {question}\n\nResponda de forma técnica e objetiva."


# ---------------------------------------------------------------------------
# Factory de agente
# ---------------------------------------------------------------------------

def create_agent(provider: str, api_key: str, model_name: str) -> Agent:
    """
    Cria e retorna o agente Agno configurado com o provider e modelo escolhido.
    """
    if not api_key or api_key.strip() == "":
        raise ValueError("API Key não fornecida. Configure a chave na barra lateral.")

    if provider == "gemini":
        os.environ["GOOGLE_API_KEY"] = api_key
        model = Gemini(id=model_name)
    elif provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
        model = OpenAIChat(id=model_name)
    else:
        raise ValueError(f"Provider '{provider}' não suportado. Use 'gemini' ou 'openai'.")

    agent = Agent(
        model=model,
        description=AGENT_PERSONA,
        markdown=True,
    )
    return agent


def generate_report(agent: Agent, data: dict) -> str:
    """
    Usa o agente para gerar o relatório técnico a partir dos dados do IFC.
    Retorna o conteúdo como string.
    """
    prompt = build_analysis_prompt(data)
    response = agent.run(prompt)
    if hasattr(response, "content"):
        return response.content
    return str(response)


def chat_with_agent(agent: Agent, question: str, data: dict) -> Generator:
    """
    Envia uma pergunta ao agente com contexto do modelo e retorna um generator
    para streaming da resposta.
    """
    prompt = build_chat_prompt(question, data)
    return agent.run(prompt, stream=True)

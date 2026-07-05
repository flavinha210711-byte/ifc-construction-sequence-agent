"""
IFC Construction Sequence Agent
Aplicação Streamlit para análise de modelos BIM/IFC com foco em
planejamento construtivo e sequência executiva preliminar.

Módulo M7T5 — Agno + ifcopenshell + Gemini
"""

from __future__ import annotations

import os
import sys
import tempfile

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ifc_analyzer import analyze_ifc, CONSTRUCTION_STAGES, SUGGESTED_ORDER
from agent import create_agent, generate_report, chat_with_agent

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="IFC Construction Sequence Agent",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS customizado
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fundo geral */
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 50%, #0d1321 100%);
    color: #e8eaf0;
}

/* Header principal */
.main-header {
    background: linear-gradient(90deg, #1e3a5f 0%, #0d2137 100%);
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.main-header h1 {
    color: #e0f2fe;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}
.main-header p {
    color: #93c5fd;
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
}

/* Cards de métricas */
.metric-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
}
.metric-card:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59,130,246,0.2);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #60a5fa;
}
.metric-label {
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}

/* Utility badges */
.badge-alto { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; border-radius: 20px; padding: 2px 12px; font-size: 0.85rem; font-weight: 600; }
.badge-medio { background: #451a03; color: #fcd34d; border: 1px solid #d97706; border-radius: 20px; padding: 2px 12px; font-size: 0.85rem; font-weight: 600; }
.badge-baixo { background: #450a0a; color: #fca5a5; border: 1px solid #dc2626; border-radius: 20px; padding: 2px 12px; font-size: 0.85rem; font-weight: 600; }

/* Stage cards */
.stage-card {
    background: linear-gradient(135deg, #1e293b 0%, #162032 100%);
    border: 1px solid #334155;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
}
.stage-card:hover {
    border-left-color: #60a5fa;
    box-shadow: 0 4px 15px rgba(59,130,246,0.15);
}
.stage-name { font-weight: 600; color: #e2e8f0; font-size: 0.95rem; }
.stage-count { color: #60a5fa; font-weight: 700; font-size: 1.1rem; }
.stage-classes { color: #64748b; font-size: 0.8rem; margin-top: 0.2rem; }

/* Gap alert */
.gap-item {
    background: #1c1109;
    border: 1px solid #92400e;
    border-left: 3px solid #f59e0b;
    border-radius: 6px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    color: #fcd34d;
    font-size: 0.88rem;
}

/* Sequence step */
.seq-step {
    background: linear-gradient(135deg, #1e293b, #172033);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s ease;
}
.seq-step:hover { border-color: #3b82f6; }
.seq-number {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    color: white;
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.9rem;
    flex-shrink: 0;
}
.seq-label { color: #e2e8f0; font-weight: 500; }
.seq-count { color: #94a3b8; font-size: 0.85rem; }

/* Chat messages */
.chat-user {
    background: #1e3a5f;
    border-radius: 12px 12px 3px 12px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: #e0f2fe;
    font-size: 0.92rem;
    max-width: 85%;
    margin-left: auto;
}
.chat-agent {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px 12px 12px 3px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: #e2e8f0;
    font-size: 0.92rem;
    max-width: 92%;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1321 0%, #0f1a2e 100%);
    border-right: 1px solid #1e3a5f;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0f172a;
    border-radius: 8px;
    padding: 4px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #94a3b8;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #1d4ed8 !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1e40af, #1d4ed8);
    box-shadow: 0 4px 15px rgba(29,78,216,0.4);
    transform: translateY(-1px);
}

/* Dataframes */
.stDataFrame { border-radius: 8px; }

/* Divider */
hr { border-color: #1e3a5f; }

/* Upload area */
[data-testid="stFileUploader"] {
    border: 2px dashed #334155;
    border-radius: 12px;
    background: #0f172a;
    transition: all 0.2s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: #3b82f6;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Funções auxiliares de UI
# ---------------------------------------------------------------------------

def utility_badge(level: str) -> str:
    cls = {"Alto": "badge-alto", "Médio": "badge-medio", "Baixo": "badge-baixo"}.get(level, "badge-baixo")
    return f'<span class="{cls}">⬤ {level}</span>'


def stage_color(stage: str) -> str:
    colors = {
        "Fundação": "#f59e0b",
        "Estrutura Vertical": "#3b82f6",
        "Estrutura Horizontal": "#8b5cf6",
        "Vedação": "#10b981",
        "Aberturas": "#06b6d4",
        "Cobertura": "#ef4444",
        "Acabamentos": "#ec4899",
        "Ambientes": "#84cc16",
    }
    return colors.get(stage, "#94a3b8")


# ---------------------------------------------------------------------------
# Inicialização do session state
# ---------------------------------------------------------------------------

if "ifc_data" not in st.session_state:
    st.session_state.ifc_data = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "report" not in st.session_state:
    st.session_state.report = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = ""

# Carrega .env
load_dotenv()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size:2.5rem;">🏗️</div>
        <div style="color:#60a5fa; font-weight:700; font-size:1.1rem;">IFC Construction</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Sequence Agent</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### ⚙️ Configurações do Agente")

    provider = st.selectbox(
        "Provider LLM",
        options=["gemini", "openai"],
        index=0,
        help="Selecione o provedor de linguagem",
        key="provider_select",
    )

    if provider == "gemini":
        model_options = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        default_model = "gemini-2.5-flash"
    else:
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        default_model = "gpt-4o-mini"

    model_name = st.selectbox(
        "Modelo",
        options=model_options,
        index=0,
        key="model_select",
    )

    api_key_input = st.text_input(
        "🔑 API Key",
        type="password",
        placeholder="Insira sua API Key aqui...",
        help="A chave inserida aqui tem prioridade sobre .env e st.secrets. Nunca é exibida.",
        key="api_key_field",
    )

    # Resolução da chave: interface > .env > st.secrets
    env_var = "GOOGLE_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
    resolved_key = (
        api_key_input.strip()
        or os.getenv(env_var, "")
        or st.secrets.get(env_var, "") if hasattr(st, "secrets") else ""
    )

    key_status = "✅ Chave configurada" if resolved_key else "⚠️ Nenhuma chave detectada"
    st.caption(key_status)

    st.divider()
    st.markdown("### 📁 Upload do Modelo IFC")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo .ifc",
        type=["ifc"],
        help="Faça upload do arquivo IFC para análise",
        key="ifc_upload",
    )

    if uploaded_file and st.button("🔍 Analisar IFC", use_container_width=True, key="btn_analyze"):
        with st.spinner("Processando modelo IFC..."):
            try:
                with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                data = analyze_ifc(tmp_path)
                st.session_state.ifc_data = data
                st.session_state.report = None
                st.session_state.chat_history = []
                st.session_state.agent = None
                st.success(f"✅ Modelo analisado: **{data['project_name']}**")

            except Exception as e:
                st.error(f"❌ Erro ao processar IFC:\n{e}")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    st.divider()
    st.markdown("""
    <div style="color:#475569; font-size:0.78rem; text-align:center;">
        M7T5 · Agno + ifcopenshell + Gemini<br>
        Planejamento Construtivo BIM 4D
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown("""
<div class="main-header">
    <h1>🏗️ IFC Construction Sequence Agent</h1>
    <p>Análise BIM para Planejamento Construtivo e Sequência Executiva Preliminar</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Estado: sem arquivo carregado
# ---------------------------------------------------------------------------

if st.session_state.ifc_data is None:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style="text-align:center; padding: 4rem 2rem; background: linear-gradient(135deg,#0f172a,#1e293b);
                    border: 1px dashed #334155; border-radius: 16px; margin-top: 2rem;">
            <div style="font-size:4rem; margin-bottom:1rem;">📐</div>
            <div style="color:#e2e8f0; font-size:1.2rem; font-weight:600; margin-bottom:0.5rem;">
                Nenhum modelo IFC carregado
            </div>
            <div style="color:#64748b; font-size:0.9rem; line-height:1.6;">
                Faça upload de um arquivo <code>.ifc</code> na barra lateral<br>
                e clique em <strong>Analisar IFC</strong> para começar.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# Dados carregados — exibe abas
# ---------------------------------------------------------------------------

data = st.session_state.ifc_data

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral",
    "🔨 Etapas Construtivas",
    "📋 Tabelas",
    "📝 Relatório IA",
    "💬 Chat",
])

# ===========================================================================
# ABA 1 — VISÃO GERAL
# ===========================================================================

with tab1:
    st.markdown("### Resumo do Modelo")

    utility = data.get("utility_level", "N/A")
    dominant = data.get("dominant_stage", "N/A")
    n_storeys = len(data.get("storeys", []))

    cols = st.columns(5)
    metrics = [
        ("🗂️", str(data.get("total_entities", 0)), "Total de Entidades"),
        ("🏢", str(n_storeys), "Pavimentos"),
        ("🔩", str(data.get("total_analyzed", 0)), "Elementos Analisados"),
        ("🏆", dominant, "Etapa Dominante"),
        ("📈", utility, "Utilidade"),
    ]
    for col, (icon, val, label) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.5rem;">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("#### 🏢 Pavimentos Identificados")
        storeys = data.get("storeys", [])
        if storeys:
            for s in storeys:
                elev = f"{s['elevation']} m" if s["elevation"] is not None else "elevação não informada"
                st.markdown(f"""
                <div class="stage-card">
                    <div class="stage-name">📐 {s['name']}</div>
                    <div class="stage-classes">{elev}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Nenhum pavimento (IfcBuildingStorey) identificado.")

    with col_b:
        st.markdown("#### ⚠️ Lacunas de Planejamento")
        gaps = data.get("planning_gaps", [])
        if gaps:
            for g in gaps:
                st.markdown(f'<div class="gap-item">⚠️ {g}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ Nenhuma lacuna crítica identificada.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📈 Nível de Utilidade")
        st.markdown(f'<div style="font-size:1.5rem;">{utility_badge(utility)}</div>', unsafe_allow_html=True)
        st.caption({
            "Alto": "Modelo bem estruturado com materiais, propriedades e quantidades presentes.",
            "Médio": "Modelo com dados parciais. Análise preliminar possível com ressalvas.",
            "Baixo": "Modelo com dados insuficientes para planejamento 4D adequado.",
        }.get(utility, ""))

    # Mapa de calor por pavimento
    st.markdown("---")
    st.markdown("#### 🗺️ Distribuição de Elementos por Pavimento e Etapa")
    storey_dist = data.get("storey_distribution", {})
    if storey_dist:
        df_dist = pd.DataFrame(storey_dist).T.fillna(0).astype(int)
        if not df_dist.empty:
            st.dataframe(df_dist, use_container_width=True)
    else:
        st.info("Distribuição por pavimento não disponível.")

# ===========================================================================
# ABA 2 — ETAPAS CONSTRUTIVAS
# ===========================================================================

with tab2:
    st.markdown("### Etapas Construtivas Identificadas")

    stages = data.get("stages", {})
    stage_classes = data.get("stage_classes", CONSTRUCTION_STAGES)
    identified = data.get("identified_stages", [])
    missing = data.get("missing_stages", [])
    total_analyzed = data.get("total_analyzed", 0)

    col_stages, col_seq = st.columns([1, 1])

    with col_stages:
        st.markdown("#### 📊 Elementos por Etapa")
        for stage in SUGGESTED_ORDER:
            count = stages.get(stage, 0)
            classes = stage_classes.get(stage, [])
            pct = int(count / max(total_analyzed, 1) * 100)
            color = stage_color(stage)
            status = "✅" if count > 0 else "⭕"
            st.markdown(f"""
            <div class="stage-card" style="border-left-color: {color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="stage-name">{status} {stage}</span>
                    <span class="stage-count">{count} elem.</span>
                </div>
                <div class="stage-classes">{', '.join(classes)}</div>
                <div style="background:#0f172a; border-radius:4px; height:4px; margin-top:8px;">
                    <div style="background:{color}; width:{pct}%; height:4px; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_seq:
        st.markdown("#### 📋 Sugestão de Sequência Executiva Preliminar")
        st.caption("Baseada na lógica construtiva padrão e nos dados do modelo.")
        for i, stage in enumerate(SUGGESTED_ORDER):
            count = stages.get(stage, 0)
            color = stage_color(stage)
            present = "✅" if count > 0 else "⭕ (ausente no modelo)"
            st.markdown(f"""
            <div class="seq-step">
                <div class="seq-number" style="background: linear-gradient(135deg, {color}aa, {color});">{i+1}</div>
                <div>
                    <div class="seq-label">{stage}</div>
                    <div class="seq-count">{count} elementos · {present}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if missing:
            st.markdown("<br>", unsafe_allow_html=True)
            st.warning(f"**Etapas sem elementos:** {', '.join(missing)}")

    st.markdown("---")
    st.markdown("#### 🏢 Distribuição por Pavimento")
    storey_dist = data.get("storey_distribution", {})
    if storey_dist:
        busiest = data.get("busiest_storey", "")
        st.info(f"**Pavimento com maior concentração:** {busiest}")
        df_dist = pd.DataFrame(storey_dist).T.fillna(0).astype(int)
        if not df_dist.empty:
            st.bar_chart(df_dist, use_container_width=True)
    else:
        st.info("Sem dados de distribuição por pavimento.")

# ===========================================================================
# ABA 3 — TABELAS
# ===========================================================================

with tab3:
    st.markdown("### 📋 Tabelas Detalhadas")

    t1, t2, t3, t4 = st.tabs([
        "Classes IFC",
        "Etapas vs Classes",
        "Pavimentos",
        "Lacunas",
    ])

    with t1:
        st.markdown("#### Contagem por Classe IFC Principal")
        class_counts = data.get("class_counts", {})
        df_classes = pd.DataFrame([
            {"Classe IFC": k, "Quantidade": v, "% do Total": f"{v/max(data['total_analyzed'],1)*100:.1f}%"}
            for k, v in sorted(class_counts.items(), key=lambda x: -x[1])
        ])
        st.dataframe(df_classes, use_container_width=True, hide_index=True)

    with t2:
        st.markdown("#### Etapas Construtivas e Classes IFC Associadas")
        rows = []
        for stage, classes in CONSTRUCTION_STAGES.items():
            count = stages.get(stage, 0)
            rows.append({
                "Etapa Construtiva": stage,
                "Classes IFC": ", ".join(classes),
                "Quantidade": count,
                "Status": "✅ Presente" if count > 0 else "⭕ Ausente",
            })
        df_stages = pd.DataFrame(rows)
        st.dataframe(df_stages, use_container_width=True, hide_index=True)

    with t3:
        st.markdown("#### Pavimentos Identificados")
        storeys = data.get("storeys", [])
        if storeys:
            df_storeys = pd.DataFrame([
                {
                    "Pavimento": s["name"],
                    "Elevação (m)": s["elevation"] if s["elevation"] is not None else "N/A",
                    "Elementos": sum(data.get("storey_distribution", {}).get(s["name"], {}).values()),
                }
                for s in storeys
            ])
            st.dataframe(df_storeys, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum pavimento identificado.")

    with t4:
        st.markdown("#### Lacunas de Qualidade do Modelo")
        df_gaps = pd.DataFrame([
            {"Indicador": "Sem nome", "Quantidade": data.get("no_name_count", 0)},
            {"Indicador": "Sem material", "Quantidade": data.get("no_material_count", 0)},
            {"Indicador": "Sem propriedades", "Quantidade": data.get("no_properties_count", 0)},
            {"Indicador": "Sem quantidades", "Quantidade": data.get("no_quantities_count", 0)},
        ])
        st.dataframe(df_gaps, use_container_width=True, hide_index=True)
        st.caption("Total de elementos analisados: " + str(data.get("total_analyzed", 0)))

# ===========================================================================
# ABA 4 — RELATÓRIO IA
# ===========================================================================

with tab4:
    st.markdown("### 📝 Relatório Técnico do Agente")
    st.caption("O agente analisa os dados do modelo e gera um relatório técnico de planejamento construtivo.")

    if not resolved_key:
        st.error("⚠️ Configure a API Key na barra lateral para gerar o relatório.")
    else:
        if st.session_state.report is None:
            if st.button("🤖 Gerar Relatório Técnico", use_container_width=True, key="btn_report"):
                with st.spinner("Gerando relatório com o agente BIM 4D..."):
                    try:
                        if st.session_state.agent is None:
                            st.session_state.agent = create_agent(provider, resolved_key, model_name)
                        report = generate_report(st.session_state.agent, data)
                        st.session_state.report = report
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ Erro de configuração: {e}")
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar relatório: {e}")
        else:
            st.success("✅ Relatório gerado pelo agente")
            st.markdown(st.session_state.report)
            if st.button("🔄 Regenerar Relatório", key="btn_regen"):
                st.session_state.report = None
                st.rerun()

# ===========================================================================
# ABA 5 — CHAT
# ===========================================================================

with tab5:
    st.markdown("### 💬 Chat com o Agente BIM 4D")
    st.caption("Faça perguntas sobre o modelo IFC e o planejamento construtivo.")

    examples = [
        "Qual seria uma sequência executiva preliminar para esse modelo?",
        "Quais pavimentos têm mais elementos?",
        "O modelo possui dados suficientes para planejamento 4D?",
        "Quais informações faltam para melhorar o planejamento da obra?",
    ]

    st.markdown("**💡 Exemplos de perguntas:**")
    ex_cols = st.columns(2)
    for i, ex in enumerate(examples):
        with ex_cols[i % 2]:
            if st.button(f"_{ex}_", key=f"ex_{i}", use_container_width=True):
                st.session_state["chat_prefill"] = ex

    st.markdown("---")

    # Exibe histórico
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f'<div class="chat-agent">🤖 <strong>Agente BIM 4D</strong></div>', unsafe_allow_html=True)
                st.markdown(msg["content"])

    # Input
    prefill = st.session_state.pop("chat_prefill", "") if "chat_prefill" in st.session_state else ""
    user_input = st.text_input(
        "Digite sua pergunta:",
        value=prefill,
        placeholder="Ex: Quais pavimentos têm mais elementos?",
        key="chat_input",
        label_visibility="collapsed",
    )

    if st.button("📨 Enviar", key="btn_send", use_container_width=True):
        if not resolved_key:
            st.error("⚠️ Configure a API Key na barra lateral.")
        elif not user_input.strip():
            st.warning("Digite uma pergunta antes de enviar.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("Agente processando..."):
                try:
                    if st.session_state.agent is None:
                        st.session_state.agent = create_agent(provider, resolved_key, model_name)

                    response_gen = chat_with_agent(st.session_state.agent, user_input, data)
                    response_text = ""
                    for chunk in response_gen:
                        if hasattr(chunk, "content"):
                            response_text += chunk.content or ""

                    if not response_text:
                        response_obj = st.session_state.agent.run(
                            f"Contexto: modelo IFC analisado. {user_input}"
                        )
                        response_text = (
                            response_obj.content
                            if hasattr(response_obj, "content")
                            else str(response_obj)
                        )

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                    })
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ Erro de configuração: {e}")
                except Exception as e:
                    st.error(f"❌ Erro no chat: {e}")

    if st.session_state.chat_history:
        if st.button("🗑️ Limpar Chat", key="btn_clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

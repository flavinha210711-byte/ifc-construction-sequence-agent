# IFC Construction Sequence Agent

> Aplicação Python desenvolvida com **Streamlit**, **Agno** e **ifcopenshell** para análise de modelos BIM/IFC com foco em **planejamento construtivo** e **sequência executiva preliminar**.

Desenvolvida para o módulo **M7T5** como avaliação acadêmica.

---

## Objetivo da Aplicação

O **IFC Construction Sequence Agent** analisa a organização de um modelo IFC por pavimentos e tipos de elementos para **sugerir uma sequência construtiva preliminar**, identificando as principais etapas da obra:

- Fundação
- Estrutura vertical e horizontal
- Vedações e aberturas
- Cobertura
- Acabamentos e ambientes

A aplicação apresenta métricas de qualidade do modelo, lacunas de dados para planejamento e gera relatórios técnicos via agente de IA especializado.

---

## Problema AECO Escolhido

**Planejamento Construtivo BIM 4D (Building Construction Sequencing)**

Na indústria AECO, um dos maiores desafios do BIM 4D é extrair, a partir de modelos IFC, uma lógica de execução construtiva que oriente o planejamento de obra. Muitos modelos são entregues com dados incompletos (sem materiais, sem quantidades, sem organização por pavimentos), dificultando o uso direto para planejamento.

Esta aplicação endereça esse problema ao:
1. Ler automaticamente o modelo IFC com `ifcopenshell`
2. Classificar elementos por etapa construtiva
3. Apontar lacunas de dados que dificultam o planejamento
4. Gerar uma sequência executiva preliminar via agente de IA

---

## Como o ifcopenshell é Usado

O módulo [`src/ifc_analyzer.py`](src/ifc_analyzer.py) utiliza `ifcopenshell` para:

- Abrir e parsear o arquivo `.ifc` sem modificá-lo
- Extrair metadados do projeto (`IfcProject`)
- Listar pavimentos (`IfcBuildingStorey`) com elevações
- Mapear elementos contidos em cada pavimento via `IfcRelContainedInSpatialStructure`
- Contar elementos por classe IFC principal (IfcFooting, IfcColumn, IfcBeam, etc.)
- Verificar a presença de materiais (`IfcRelAssociatesMaterial`), property sets (`IfcRelDefinesByProperties`) e quantidades (`IfcElementQuantity`)
- Calcular métricas de qualidade do modelo

---

## Como o Agno é Usado

O módulo [`src/agent.py`](src/agent.py) utiliza o **framework Agno** para:

- Criar um agente com persona de **planejador BIM 4D**
- Integrar os modelos Gemini (Google) ou OpenAI como LLM
- Receber os dados estruturados extraídos pelo `ifcopenshell` como contexto
- Gerar relatórios técnicos com seções pré-definidas
- Responder perguntas no chat com contexto do modelo

O agente usa a classe `agno.agent.Agent` com `markdown=True` e `stream=True` para respostas progressivas.

---

## Como Configurar o Gemini

1. Acesse [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Crie uma nova API Key
3. Copie a chave gerada

### Opção 1 — Via interface (recomendado)
Insira a chave diretamente no campo **🔑 API Key** na barra lateral do app.
A chave digitada na interface **tem prioridade** sobre qualquer outra configuração.

### Opção 2 — Via arquivo `.env`
```bash
cp .env.example .env
# Edite o .env e insira sua chave:
GOOGLE_API_KEY=sua_chave_aqui
```

### Opção 3 — Via `st.secrets` (para deploy no Streamlit Cloud)
Crie o arquivo `.streamlit/secrets.toml`:
```toml
GOOGLE_API_KEY = "sua_chave_aqui"
```

> ⚠️ **Nunca commite sua chave real no GitHub.** O `.gitignore` já exclui `.env` e `secrets.toml`.

---

## Como Inserir a API Key pela Interface

1. Na barra lateral esquerda, localize o campo **🔑 API Key**
2. Digite sua chave — ela é exibida como `●●●●●●●` (tipo password)
3. A chave **não é exibida**, não aparece em logs e não é incluída no relatório
4. A chave digitada aqui tem **prioridade** sobre `.env` e `st.secrets`

---

## Como Rodar Localmente

### Pré-requisitos
- Python 3.10+
- pip

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ifc-construction-sequence-agent.git
cd ifc-construction-sequence-agent

# Crie e ative um ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

> **Nota sobre ifcopenshell**: Em alguns sistemas, é necessário instalar via conda ou pip wheel:
> ```bash
> pip install ifcopenshell
> # ou via conda:
> conda install -c ifcopenshell ifcopenshell
> ```

### Configuração da API Key (opcional)

```bash
cp .env.example .env
# Edite o .env com sua chave Gemini ou OpenAI
```

### Execução

```bash
streamlit run app.py
```

Acesse no navegador: `http://localhost:8501`

---

## Estrutura do Projeto

```
ifc-construction-sequence-agent/
├── app.py                  # Aplicação Streamlit principal
├── requirements.txt        # Dependências Python
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore              # Arquivos ignorados pelo git
├── README.md               # Esta documentação
└── src/
    ├── ifc_analyzer.py     # Análise do arquivo IFC com ifcopenshell
    └── agent.py            # Configuração do agente Agno com Gemini/OpenAI
```

---

## Funcionalidades

| Aba | Conteúdo |
|-----|----------|
| 📊 Visão Geral | Cards com métricas, pavimentos, lacunas de planejamento |
| 🔨 Etapas Construtivas | Etapas identificadas, sequência sugerida, distribuição por pavimento |
| 📋 Tabelas | Tabelas detalhadas de classes IFC, etapas, pavimentos e lacunas |
| 📝 Relatório IA | Relatório técnico gerado pelo agente BIM 4D |
| 💬 Chat | Chat interativo com o agente sobre o modelo IFC |

---

## Stack Tecnológica

| Tecnologia | Uso |
|------------|-----|
| Python 3.10+ | Linguagem principal |
| Streamlit | Interface web |
| ifcopenshell | Leitura e parsing de arquivos IFC |
| Agno | Framework do agente de IA |
| Gemini 2.5 Flash | LLM principal (Google) |
| OpenAI | LLM alternativo |
| pandas | Manipulação e exibição de dados |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## Notas Acadêmicas

- O modelo IFC **não é editado** pela aplicação
- Não é realizada análise geométrica complexa
- O foco é exclusivamente **planejamento construtivo e sequência executiva**
- O código é original e independente de outros projetos do módulo
- Nenhuma API Key real está incluída no repositório

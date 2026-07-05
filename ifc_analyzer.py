"""
IFC Analyzer Module
Responsável por ler e extrair dados estruturados de arquivos IFC usando ifcopenshell.
Foco: planejamento construtivo e sequência executiva preliminar.
"""

import ifcopenshell
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Mapeamento de etapas construtivas
# ---------------------------------------------------------------------------

CONSTRUCTION_STAGES = {
    "Fundação": ["IfcFooting", "IfcPile", "IfcPlate"],
    "Estrutura Vertical": ["IfcColumn"],
    "Estrutura Horizontal": ["IfcBeam", "IfcSlab"],
    "Vedação": ["IfcWall", "IfcWallStandardCase", "IfcCurtainWall"],
    "Aberturas": ["IfcDoor", "IfcWindow"],
    "Cobertura": ["IfcRoof"],
    "Acabamentos": ["IfcCovering"],
    "Ambientes": ["IfcSpace"],
}

MAIN_CLASSES = [
    "IfcFooting", "IfcColumn", "IfcBeam", "IfcSlab",
    "IfcWall", "IfcDoor", "IfcWindow", "IfcRoof",
    "IfcCovering", "IfcSpace",
]

SUGGESTED_ORDER = [
    "Fundação",
    "Estrutura Vertical",
    "Estrutura Horizontal",
    "Vedação",
    "Cobertura",
    "Aberturas",
    "Acabamentos",
    "Ambientes",
]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _has_material(element) -> bool:
    """Verifica se o elemento possui material associado."""
    try:
        associations = element.HasAssociations
        for assoc in associations:
            if assoc.is_a("IfcRelAssociatesMaterial"):
                return True
    except Exception:
        pass
    return False


def _has_properties(element) -> bool:
    """Verifica se o elemento possui property sets."""
    try:
        for definition in element.IsDefinedBy:
            if definition.is_a("IfcRelDefinesByProperties"):
                return True
    except Exception:
        pass
    return False


def _has_quantities(element) -> bool:
    """Verifica se o elemento possui quantity sets."""
    try:
        for definition in element.IsDefinedBy:
            if definition.is_a("IfcRelDefinesByProperties"):
                prop_def = definition.RelatingPropertyDefinition
                if prop_def.is_a("IfcElementQuantity"):
                    return True
    except Exception:
        pass
    return False


def _get_storey_elements(ifc_file) -> dict:
    """Mapeia elementos contidos em cada pavimento."""
    storey_elements: dict = {}

    storeys = ifc_file.by_type("IfcBuildingStorey")
    for storey in storeys:
        name = storey.Name or f"Pavimento sem nome (ID {storey.id()})"
        elements_in_storey = []

        try:
            for rel in storey.ContainsElements:
                if rel.is_a("IfcRelContainedInSpatialStructure"):
                    for element in rel.RelatedElements:
                        elements_in_storey.append(element)
        except Exception:
            pass

        storey_elements[name] = elements_in_storey

    return storey_elements


# ---------------------------------------------------------------------------
# Função principal de análise
# ---------------------------------------------------------------------------

def analyze_ifc(file_path: str) -> dict:
    """
    Lê o arquivo IFC e extrai todas as informações necessárias para
    planejamento construtivo e sequência executiva preliminar.

    Returns:
        dict com todos os dados estruturados do modelo.
    """
    try:
        ifc_file = ifcopenshell.open(file_path)
    except Exception as e:
        raise RuntimeError(f"Erro ao abrir o arquivo IFC: {e}")

    result: dict = {}

    # ------------------------------------------------------------------
    # 1. Informações do projeto
    # ------------------------------------------------------------------
    projects = ifc_file.by_type("IfcProject")
    result["project_name"] = projects[0].Name if projects else "Projeto sem nome"
    result["total_entities"] = len(ifc_file.by_type("IfcRoot"))

    # ------------------------------------------------------------------
    # 2. Pavimentos
    # ------------------------------------------------------------------
    storeys = ifc_file.by_type("IfcBuildingStorey")
    storey_info = []
    for s in storeys:
        elevation = None
        try:
            if s.Elevation is not None:
                elevation = round(float(s.Elevation), 3)
        except Exception:
            pass
        storey_info.append({
            "name": s.Name or f"Pavimento ID {s.id()}",
            "elevation": elevation,
        })
    # Ordena por elevação (None por último)
    storey_info.sort(key=lambda x: (x["elevation"] is None, x["elevation"] or 0))
    result["storeys"] = storey_info

    # ------------------------------------------------------------------
    # 3. Contagem de elementos por classe IFC principal
    # ------------------------------------------------------------------
    class_counts: dict = {}
    for cls in MAIN_CLASSES:
        elements = ifc_file.by_type(cls)
        class_counts[cls] = len(elements)
    result["class_counts"] = class_counts
    result["total_analyzed"] = sum(class_counts.values())

    # ------------------------------------------------------------------
    # 4. Elementos sem informação
    # ------------------------------------------------------------------
    all_elements = []
    for cls in MAIN_CLASSES:
        all_elements.extend(ifc_file.by_type(cls))

    no_name = sum(1 for e in all_elements if not e.Name)
    no_material = sum(1 for e in all_elements if not _has_material(e))
    no_properties = sum(1 for e in all_elements if not _has_properties(e))
    no_quantities = sum(1 for e in all_elements if not _has_quantities(e))

    result["no_name_count"] = no_name
    result["no_material_count"] = no_material
    result["no_properties_count"] = no_properties
    result["no_quantities_count"] = no_quantities

    # ------------------------------------------------------------------
    # 5. Etapas construtivas
    # ------------------------------------------------------------------
    stages: dict = {}
    for stage_name, ifc_classes in CONSTRUCTION_STAGES.items():
        total = 0
        for cls in ifc_classes:
            total += len(ifc_file.by_type(cls))
        stages[stage_name] = total
    result["stages"] = stages
    result["stage_classes"] = CONSTRUCTION_STAGES
    result["suggested_order"] = SUGGESTED_ORDER

    # Etapa mais representativa
    if stages:
        dominant_stage = max(stages, key=lambda k: stages[k])
        result["dominant_stage"] = dominant_stage if stages[dominant_stage] > 0 else "N/A"
    else:
        result["dominant_stage"] = "N/A"

    # ------------------------------------------------------------------
    # 6. Distribuição por pavimento
    # ------------------------------------------------------------------
    storey_elements_map = _get_storey_elements(ifc_file)
    storey_distribution: dict = {}

    for storey_name, elements in storey_elements_map.items():
        counts_per_stage: dict = defaultdict(int)
        for element in elements:
            ifc_class = element.is_a()
            for stage_name, ifc_classes in CONSTRUCTION_STAGES.items():
                if ifc_class in ifc_classes:
                    counts_per_stage[stage_name] += 1
                    break
        storey_distribution[storey_name] = dict(counts_per_stage)

    result["storey_distribution"] = storey_distribution

    # Pavimento com maior concentração de elementos
    if storey_distribution:
        busiest_storey = max(
            storey_distribution,
            key=lambda k: sum(storey_distribution[k].values())
        )
        result["busiest_storey"] = busiest_storey
    else:
        result["busiest_storey"] = "N/A"

    # ------------------------------------------------------------------
    # 7. Nível de utilidade para planejamento
    # ------------------------------------------------------------------
    total_analyzed = result["total_analyzed"]
    if total_analyzed == 0:
        utility_level = "Baixo"
    else:
        score = 0
        # Elementos com material
        material_pct = 1 - (no_material / max(total_analyzed, 1))
        # Elementos com propriedades
        props_pct = 1 - (no_properties / max(total_analyzed, 1))
        # Elementos com quantidades
        qty_pct = 1 - (no_quantities / max(total_analyzed, 1))
        # Pavimentos identificados
        has_storeys = 1 if len(storeys) > 0 else 0
        # Etapas presentes
        present_stages = sum(1 for v in stages.values() if v > 0)
        stages_pct = present_stages / max(len(CONSTRUCTION_STAGES), 1)

        score = (material_pct * 0.25 + props_pct * 0.25 +
                 qty_pct * 0.20 + has_storeys * 0.10 + stages_pct * 0.20)

        if score >= 0.65:
            utility_level = "Alto"
        elif score >= 0.35:
            utility_level = "Médio"
        else:
            utility_level = "Baixo"

    result["utility_level"] = utility_level

    # ------------------------------------------------------------------
    # 8. Etapas identificadas (com pelo menos 1 elemento)
    # ------------------------------------------------------------------
    result["identified_stages"] = [k for k, v in stages.items() if v > 0]
    result["missing_stages"] = [k for k, v in stages.items() if v == 0]

    # ------------------------------------------------------------------
    # 9. Lacunas de planejamento
    # ------------------------------------------------------------------
    gaps = []
    if no_material > 0:
        gaps.append(f"{no_material} elemento(s) sem material definido")
    if no_properties > 0:
        gaps.append(f"{no_properties} elemento(s) sem property sets")
    if no_quantities > 0:
        gaps.append(f"{no_quantities} elemento(s) sem quantidades (IfcElementQuantity)")
    if no_name > 0:
        gaps.append(f"{no_name} elemento(s) sem nome (Name vazio)")
    if len(result["missing_stages"]) > 0:
        gaps.append(f"Etapas ausentes: {', '.join(result['missing_stages'])}")
    result["planning_gaps"] = gaps

    return result

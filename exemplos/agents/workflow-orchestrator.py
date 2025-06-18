from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import requests
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"
RAG_API_URL = "http://localhost:8000/search"

# --------------------------------------------------------------
# Step 1: Define the data models
# --------------------------------------------------------------


class LegalSubTask(BaseModel):
    """Subtarefa jurídica definida pelo orchestrator"""

    task_type: str = Field(description="Tipo da subtarefa jurídica")
    description: str = Field(description="O que esta subtarefa deve abordar")
    search_strategy: str = Field(description="Estratégia de busca no RAG")
    priority_level: str = Field(description="Alta, Média ou Baixa prioridade")


class OrchestratorPlan(BaseModel):
    """Plano estruturado do orchestrator para análise jurídica"""

    case_analysis: str = Field(description="Análise inicial do caso ou consulta")
    legal_areas: List[str] = Field(description="Áreas do direito envolvidas")
    subtasks: List[LegalSubTask] = Field(
        description="Lista de subtarefas identificadas"
    )
    expected_outcome: str = Field(description="Resultado esperado da análise")


class SubTaskResult(BaseModel):
    """Resultado produzido por um worker"""

    findings: str = Field(description="Achados e análise da subtarefa")
    sources: List[str] = Field(description="Fontes consultadas")
    recommendations: Optional[str] = Field(description="Recomendações específicas")


class SuggestedRefinement(BaseModel):
    """Refinamentos sugeridos para uma subtarefa"""

    subtask_name: str = Field(description="Nome da subtarefa")
    suggested_refinement: str = Field(description="Refinamento sugerido")


class FinalAnalysis(BaseModel):
    """Análise final e síntese"""

    coherence_score: float = Field(
        description="Quão bem as subtarefas se complementam (0-1)"
    )
    suggested_refinements: List[SuggestedRefinement] = Field(
        description="Refinamentos sugeridos"
    )
    final_legal_opinion: str = Field(description="Parecer jurídico final completo")


# --------------------------------------------------------------
# Step 2: RAG integration
# --------------------------------------------------------------


def search_legal_documents(query: str, limit: int = 5) -> List[Dict]:
    """Buscar documentos jurídicos no RAG"""
    try:
        payload = {"query": query, "limit": limit}
        response = requests.post(RAG_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException:
        return []


# --------------------------------------------------------------
# Step 3: Implement orchestrator
# --------------------------------------------------------------


class LegalOrchestrator:
    def __init__(self):
        self.subtask_results = {}

    def create_analysis_plan(
        self, consultation: str, case_context: str = ""
    ) -> OrchestratorPlan:
        """Orchestrator: Analisar consulta e criar plano de subtarefas"""

        prompt = f"""
        Analise esta consulta jurídica e quebre em subtarefas lógicas.
        
        Consulta: {consultation}
        Contexto adicional: {case_context if case_context else "Não fornecido"}
        
        Identifique:
        1. As áreas do direito envolvidas
        2. Subtarefas específicas necessárias (ex: análise normativa, busca de precedentes, análise de responsabilidade)
        3. Estratégia de pesquisa para cada subtarefa
        4. Prioridade de cada subtarefa
        
        Seja específico sobre o que cada subtarefa deve abordar e como pesquisar por informações relevantes.
        """

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            response_format=OrchestratorPlan,
        )
        return completion.choices[0].message.parsed

    def execute_subtask(
        self, consultation: str, subtask: LegalSubTask
    ) -> SubTaskResult:
        """Worker: Executar uma subtarefa específica com contexto das anteriores"""

        # Buscar documentos relevantes usando a estratégia definida
        documents = search_legal_documents(subtask.search_strategy)
        documents_context = "\n".join(
            [f"- {doc.get('page_content', '')}" for doc in documents[:3]]
        )

        # Criar contexto das subtarefas anteriores
        previous_context = "\n\n".join(
            [
                f"=== {task_type} ===\n{result.findings}"
                for task_type, result in self.subtask_results.items()
            ]
        )

        prompt = f"""
        Execute esta subtarefa jurídica específica:
        
        Consulta original: {consultation}
        Tipo da subtarefa: {subtask.task_type}
        Descrição: {subtask.description}
        Prioridade: {subtask.priority_level}
        
        Contexto de subtarefas anteriores:
        {previous_context if previous_context else "Esta é a primeira subtarefa."}
        
        Documentos jurídicos encontrados:
        {documents_context if documents_context else "Nenhum documento específico encontrado."}
        
        Forneça uma análise focada nesta subtarefa específica, citando fontes quando aplicável.
        """

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            response_format=SubTaskResult,
        )
        return completion.choices[0].message.parsed

    def synthesize_analysis(
        self, consultation: str, plan: OrchestratorPlan
    ) -> FinalAnalysis:
        """Reviewer: Sintetizar todas as subtarefas em parecer final"""

        subtasks_text = "\n\n".join(
            [
                f"=== {task_type} ===\n{result.findings}"
                for task_type, result in self.subtask_results.items()
            ]
        )

        all_sources = []
        for result in self.subtask_results.values():
            all_sources.extend(result.sources)

        prompt = f"""
        Sintetize esta análise jurídica completa:
        
        Consulta original: {consultation}
        Áreas do direito: {", ".join(plan.legal_areas)}
        Resultado esperado: {plan.expected_outcome}
        
        Análises das subtarefas:
        {subtasks_text}
        
        Avalie a coerência entre as subtarefas (score 0-1), sugira refinamentos se necessário,
        e elabore um parecer jurídico final que integre todos os achados de forma coesa.
        
        O parecer final deve ser estruturado, fundamentado e apresentar uma conclusão clara.
        """

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            response_format=FinalAnalysis,
        )
        return completion.choices[0].message.parsed

    def process_legal_consultation(
        self, consultation: str, case_context: str = ""
    ) -> Dict:
        """Processar consulta jurídica completa usando orchestrator-workers"""

        print(f"Iniciando análise jurídica para: {consultation[:80]}...")

        # Orchestrator: Criar plano de análise
        plan = self.create_analysis_plan(consultation, case_context)
        print(f"Plano criado com {len(plan.subtasks)} subtarefas")
        print(f"Áreas identificadas: {', '.join(plan.legal_areas)}")

        # Workers: Executar cada subtarefa
        for subtask in plan.subtasks:
            print(f"Executando: {subtask.task_type}")
            result = self.execute_subtask(consultation, subtask)
            self.subtask_results[subtask.task_type] = result

        # Reviewer: Sintetizar análise final
        print("Sintetizando parecer final...")
        final_analysis = self.synthesize_analysis(consultation, plan)

        return {
            "plan": plan,
            "subtask_results": self.subtask_results,
            "final_analysis": final_analysis,
        }


def format_legal_analysis(result: Dict) -> str:
    """Formatar a análise jurídica para apresentação"""

    plan = result["plan"]
    final = result["final_analysis"]

    formatted = f"""
{"=" * 80}
ANÁLISE JURÍDICA COMPLETA
{"=" * 80}

ÁREAS DO DIREITO ENVOLVIDAS:
{", ".join(plan.legal_areas)}

ESTRATÉGIA DE ANÁLISE:
{plan.case_analysis}

SUBTAREFAS EXECUTADAS:
"""

    for i, subtask in enumerate(plan.subtasks, 1):
        formatted += (
            f"{i}. {subtask.task_type} (Prioridade: {subtask.priority_level})\n"
        )

    formatted += f"""
SCORE DE COERÊNCIA: {final.coherence_score:.2f}

PARECER JURÍDICO FINAL:
{final.final_legal_opinion}
"""

    if final.suggested_refinements:
        formatted += "\nREFINAMENTOS SUGERIDOS:\n"
        for refinement in final.suggested_refinements:
            formatted += (
                f"- {refinement.subtask_name}: {refinement.suggested_refinement}\n"
            )

    return formatted


# --------------------------------------------------------------
# Step 4: Test examples
# --------------------------------------------------------------


if __name__ == "__main__":
    orchestrator = LegalOrchestrator()

    # Exemplo 1: Caso complexo de engenharia
    complex_case = """
    Sou engenheiro civil e estava responsável técnico por uma obra residencial. 
    Durante a construção, houve um problema estrutural que causou rachaduras nas paredes. 
    O proprietário está me processando por danos materiais e morais, alegando negligência. 
    A construtora também está me responsabilizando pelo problema. 
    Preciso entender minha responsabilidade civil, possíveis defesas, e se posso cobrar 
    regressivamente da construtora que não seguiu minhas especificações técnicas.
    """

    case_context = """
    Contexto adicional: A obra foi iniciada em 2023, tenho ART recolhida, 
    forneci projeto estrutural detalhado, mas a construtora usou materiais 
    diferentes dos especificados sem me comunicar.
    """

    print("PROCESSANDO CASO COMPLEXO...")
    result = orchestrator.process_legal_consultation(complex_case, case_context)
    print(format_legal_analysis(result))

    print("\n" + "=" * 80)

    # Exemplo 2: Consulta mais simples
    simple_consultation = """
    Preciso saber se posso exercer a profissão de engenheiro civil 
    sem ter registro no CREA. Sou formado mas ainda não fiz o registro.
    """

    print("PROCESSANDO CONSULTA SIMPLES...")
    orchestrator2 = LegalOrchestrator()  # Nova instância para limpar estado
    result2 = orchestrator2.process_legal_consultation(simple_consultation)
    print(format_legal_analysis(result2))

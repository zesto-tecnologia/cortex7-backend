"""
Database models for the Cortex system.
Import all models here for Alembic to detect them.
"""

from shared.models.empresa import Empresa, Departamento
from shared.models.usuario import Usuario
from shared.models.documento import Documento
from shared.models.financeiro import (
    CentroCusto,
    Fornecedor,
    ContaPagar,
    CartaoCorporativo,
    FaturaCartao,
    LancamentoCartao,
)
from shared.models.rh import Funcionario, ContratoTrabalho
from shared.models.juridico import Contrato, ProcessoJuridico
from shared.models.suprimentos import OrdemCompra
from shared.models.workflow import Workflow, Tarefa
from shared.models.auditoria import LogAgente, Auditoria, CacheEmbedding, AgenteConfig

__all__ = [
    # Empresa
    "Empresa",
    "Departamento",
    # Usuario
    "Usuario",
    # Documento
    "Documento",
    # Financeiro
    "CentroCusto",
    "Fornecedor",
    "ContaPagar",
    "CartaoCorporativo",
    "FaturaCartao",
    "LancamentoCartao",
    # RH
    "Funcionario",
    "ContratoTrabalho",
    # Juridico
    "Contrato",
    "ProcessoJuridico",
    # Suprimentos
    "OrdemCompra",
    # Workflow
    "Workflow",
    "Tarefa",
    # Auditoria
    "LogAgente",
    "Auditoria",
    "CacheEmbedding",
    "AgenteConfig",
]
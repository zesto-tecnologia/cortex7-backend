"""
CrewAI-compatible tools for Data Warehouse Financial Analytics.
Provides direct SQL query capabilities to the OMIE financial data warehouse.
"""

from crewai.tools import BaseTool
from typing import Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_db_engine():
    """Get database engine for DW queries."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/cortex"
    ).replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return create_engine(db_url, pool_pre_ping=True)


class QueryRevenueByClientTool(BaseTool):
    name: str = "Query Revenue by Client"
    description: str = (
        "Analisa receita por cliente do Data Warehouse OMIE. "
        "Retorna receitas agrupadas por cliente com filtros opcionais de período. "
        "Input: periodo opcional (ex: '2023', '2023-Q1', '2023-01') ou vazio para todos os dados. "
        "Retorna: Lista dos top 20 clientes com receita total, número de títulos e ticket médio."
    )

    def _run(self, periodo: str = "") -> str:
        """Execute the tool."""
        try:
            engine = get_db_engine()

            # Base query
            query = """
                SELECT
                    c.trade_name as cliente,
                    c.vertical,
                    c.key_account,
                    c.state as estado,
                    COUNT(f.id) as num_titulos,
                    SUM(f.title_value) as receita_total,
                    AVG(f.title_value) as ticket_medio,
                    SUM(f.total_taxes_withheld) as impostos_retidos
                FROM fact_financial_transactions f
                JOIN dim_clients c ON f.client_id = c.id
                LEFT JOIN dim_dates d ON f.due_date_id = d.id
                WHERE f.status IN ('RECEBIDO', 'PAGO')
            """

            # Add period filter if provided
            if periodo:
                if len(periodo) == 4:  # Year
                    query += f" AND d.year = {periodo}"
                elif '-Q' in periodo:  # Quarter
                    year, quarter = periodo.split('-Q')
                    query += f" AND d.year_quarter = '{year}-Q{quarter}'"
                elif len(periodo) == 7:  # Year-Month
                    query += f" AND d.year_month = '{periodo}'"

            query += """
                GROUP BY c.trade_name, c.vertical, c.key_account, c.state
                ORDER BY receita_total DESC
                LIMIT 20
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return f"Nenhuma receita encontrada para o período: {periodo or 'todos'}"

                # Format results
                data = []
                for row in rows:
                    data.append({
                        'cliente': row[0],
                        'vertical': row[1],
                        'key_account': row[2],
                        'estado': row[3],
                        'num_titulos': row[4],
                        'receita_total': float(row[5]) if row[5] else 0,
                        'ticket_medio': float(row[6]) if row[6] else 0,
                        'impostos_retidos': float(row[7]) if row[7] else 0,
                    })

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error querying revenue by client: {e}")
            return f"Erro ao consultar receita por cliente: {str(e)}"


class QueryPLAnalysisTool(BaseTool):
    name: str = "Query P&L Analysis"
    description: str = (
        "Analisa P&L (Profit & Loss) do Data Warehouse OMIE por categorias. "
        "Retorna análise de receitas e despesas por categoria hierárquica. "
        "Input: periodo opcional (ex: '2023', '2023-Q1', '2023-01'), tipo opcional ('receita' ou 'despesa'). "
        "Formato: 'periodo|tipo' ou vazio para todos. "
        "Retorna: Análise P&L com totais por categoria."
    )

    def _run(self, filtros: str = "") -> str:
        """Execute the tool."""
        try:
            engine = get_db_engine()

            # Parse filters
            periodo = ""
            tipo = ""
            if filtros:
                parts = filtros.split("|")
                periodo = parts[0] if len(parts) > 0 else ""
                tipo = parts[1].lower() if len(parts) > 1 else ""

            query = """
                SELECT
                    cat.level_1,
                    cat.name_pt as categoria,
                    cat.category_type as tipo,
                    d.fiscal_year as ano,
                    d.fiscal_quarter as trimestre,
                    COUNT(f.id) as num_transacoes,
                    SUM(f.title_value) as valor_total,
                    SUM(f.total_taxes_withheld) as impostos_retidos,
                    SUM(f.net_value) as valor_liquido
                FROM fact_financial_transactions f
                JOIN dim_categories cat ON f.category_id = cat.id
                LEFT JOIN dim_dates d ON f.due_date_id = d.id
                WHERE 1=1
            """

            # Add period filter
            if periodo:
                if len(periodo) == 4:  # Year
                    query += f" AND d.year = {periodo}"
                elif '-Q' in periodo:  # Quarter
                    year, quarter = periodo.split('-Q')
                    query += f" AND d.year_quarter = '{year}-Q{quarter}'"
                elif len(periodo) == 7:  # Year-Month
                    query += f" AND d.year_month = '{periodo}'"

            # Add type filter
            if tipo:
                query += f" AND LOWER(cat.category_type) LIKE '%{tipo}%'"

            query += """
                GROUP BY cat.level_1, cat.name_pt, cat.category_type, d.fiscal_year, d.fiscal_quarter
                ORDER BY d.fiscal_year DESC, d.fiscal_quarter DESC, valor_total DESC
                LIMIT 50
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return f"Nenhum dado P&L encontrado para os filtros: {filtros or 'todos'}"

                # Format results
                data = []
                for row in rows:
                    data.append({
                        'nivel_1': row[0],
                        'categoria': row[1],
                        'tipo': row[2],
                        'ano': row[3],
                        'trimestre': row[4],
                        'num_transacoes': row[5],
                        'valor_total': float(row[6]) if row[6] else 0,
                        'impostos_retidos': float(row[7]) if row[7] else 0,
                        'valor_liquido': float(row[8]) if row[8] else 0,
                    })

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error querying P&L analysis: {e}")
            return f"Erro ao consultar análise P&L: {str(e)}"


class QueryCashFlowTool(BaseTool):
    name: str = "Query Cash Flow Analysis"
    description: str = (
        "Analisa fluxo de caixa do Data Warehouse OMIE. "
        "Retorna entradas, saídas e saldo por período. "
        "Input: numero_meses (int, ex: 6 para últimos 6 meses) ou vazio para 12 meses. "
        "Retorna: Análise de fluxo de caixa mensal com receitas, despesas e saldo."
    )

    def _run(self, numero_meses: str = "12") -> str:
        """Execute the tool."""
        try:
            engine = get_db_engine()
            meses = int(numero_meses) if numero_meses else 12

            query = f"""
                SELECT
                    d.year_month as periodo,
                    COUNT(f.id) as total_transacoes,
                    SUM(CASE WHEN f.status IN ('RECEBIDO', 'PAGO') AND cat.category_type LIKE '%Receita%'
                        THEN f.title_value ELSE 0 END) as entradas,
                    SUM(CASE WHEN f.status IN ('RECEBIDO', 'PAGO') AND cat.category_type LIKE '%Despesa%'
                        THEN f.title_value ELSE 0 END) as saidas,
                    SUM(CASE WHEN f.status IN ('A VENCER', 'VENCE HOJE', 'ATRASADO')
                        THEN f.open_value ELSE 0 END) as saldo_futuro,
                    COUNT(CASE WHEN f.status = 'ATRASADO' THEN 1 END) as titulos_atrasados
                FROM fact_financial_transactions f
                JOIN dim_dates d ON f.due_date_id = d.id
                LEFT JOIN dim_categories cat ON f.category_id = cat.id
                WHERE d.date_value >= CURRENT_DATE - INTERVAL '{meses} months'
                GROUP BY d.year_month
                ORDER BY d.year_month DESC
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return f"Nenhum dado de fluxo de caixa encontrado para os últimos {meses} meses"

                # Format results and calculate net flow
                data = []
                for row in rows:
                    entradas = float(row[2]) if row[2] else 0
                    saidas = float(row[3]) if row[3] else 0
                    data.append({
                        'periodo': row[0],
                        'total_transacoes': row[1],
                        'entradas': entradas,
                        'saidas': saidas,
                        'saldo_liquido': entradas - saidas,
                        'saldo_futuro': float(row[4]) if row[4] else 0,
                        'titulos_atrasados': row[5],
                    })

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error querying cash flow: {e}")
            return f"Erro ao consultar fluxo de caixa: {str(e)}"


class QueryOverdueAnalysisTool(BaseTool):
    name: str = "Query Overdue Transactions"
    description: str = (
        "Analisa títulos atrasados e inadimplência do Data Warehouse OMIE. "
        "Retorna clientes com títulos em atraso, valores e dias de atraso. "
        "Input: dias_minimos (int, ex: 30 para atrasos acima de 30 dias) ou vazio para todos. "
        "Retorna: Lista de clientes inadimplentes com análise de risco."
    )

    def _run(self, dias_minimos: str = "0") -> str:
        """Execute the tool."""
        try:
            engine = get_db_engine()
            dias = int(dias_minimos) if dias_minimos else 0

            query = f"""
                SELECT
                    c.trade_name as cliente,
                    c.key_account,
                    c.vertical,
                    COUNT(f.id) as titulos_atrasados,
                    SUM(f.open_value) as valor_total_atrasado,
                    MIN(CURRENT_DATE - d.date_value) as dias_atraso_maximo,
                    AVG(CURRENT_DATE - d.date_value) as dias_atraso_medio,
                    STRING_AGG(DISTINCT f.title_number, ', ') as titulos
                FROM fact_financial_transactions f
                JOIN dim_clients c ON f.client_id = c.id
                JOIN dim_dates d ON f.due_date_id = d.id
                WHERE f.status IN ('ATRASADO', 'ABERTO')
                  AND d.date_value < CURRENT_DATE
                  AND (CURRENT_DATE - d.date_value) >= {dias}
                GROUP BY c.trade_name, c.key_account, c.vertical
                HAVING SUM(f.open_value) > 0
                ORDER BY valor_total_atrasado DESC
                LIMIT 30
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return f"Nenhum título atrasado encontrado (mínimo {dias} dias)"

                # Format results
                data = []
                for row in rows:
                    data.append({
                        'cliente': row[0],
                        'key_account': row[1],
                        'vertical': row[2],
                        'titulos_atrasados': row[3],
                        'valor_total_atrasado': float(row[4]) if row[4] else 0,
                        'dias_atraso_maximo': row[5],
                        'dias_atraso_medio': float(row[6]) if row[6] else 0,
                        'numeros_titulos': row[7][:200] if row[7] else "",  # Limit string length
                    })

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error querying overdue transactions: {e}")
            return f"Erro ao consultar títulos atrasados: {str(e)}"


class QueryTaxAnalysisTool(BaseTool):
    name: str = "Query Tax Analysis"
    description: str = (
        "Analisa carga tributária e impostos retidos do Data Warehouse OMIE. "
        "Retorna análise de impostos por categoria e período. "
        "Input: periodo opcional (ex: '2023', '2023-Q1') ou vazio para ano atual. "
        "Retorna: Análise detalhada de impostos: COFINS, CSLL, PIS, IR, ISS, INSS."
    )

    def _run(self, periodo: str = "") -> str:
        """Execute the tool."""
        try:
            engine = get_db_engine()

            query = """
                SELECT
                    cat.name_pt as categoria,
                    d.fiscal_year as ano,
                    COUNT(f.id) as num_transacoes,
                    SUM(f.title_value) as receita_bruta,
                    SUM(f.tax_cofins) as cofins,
                    SUM(f.tax_csll) as csll,
                    SUM(f.tax_pis) as pis,
                    SUM(f.tax_ir) as ir,
                    SUM(f.tax_iss) as iss,
                    SUM(f.tax_inss) as inss,
                    SUM(f.total_taxes_withheld) as total_impostos,
                    ROUND(100.0 * SUM(f.total_taxes_withheld) / NULLIF(SUM(f.title_value), 0), 2) as carga_tributaria_pct
                FROM fact_financial_transactions f
                JOIN dim_categories cat ON f.category_id = cat.id
                LEFT JOIN dim_dates d ON f.due_date_id = d.id
                WHERE f.status IN ('RECEBIDO', 'PAGO')
            """

            # Add period filter
            if periodo:
                if len(periodo) == 4:  # Year
                    query += f" AND d.year = {periodo}"
                elif '-Q' in periodo:  # Quarter
                    year, quarter = periodo.split('-Q')
                    query += f" AND d.year_quarter = '{year}-Q{quarter}'"
                else:
                    query += f" AND d.fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)"
            else:
                query += f" AND d.fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)"

            query += """
                GROUP BY cat.name_pt, d.fiscal_year
                HAVING SUM(f.title_value) > 0
                ORDER BY total_impostos DESC
                LIMIT 30
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return f"Nenhum dado tributário encontrado para o período: {periodo or 'ano atual'}"

                # Format results
                data = []
                for row in rows:
                    data.append({
                        'categoria': row[0],
                        'ano': row[1],
                        'num_transacoes': row[2],
                        'receita_bruta': float(row[3]) if row[3] else 0,
                        'cofins': float(row[4]) if row[4] else 0,
                        'csll': float(row[5]) if row[5] else 0,
                        'pis': float(row[6]) if row[6] else 0,
                        'ir': float(row[7]) if row[7] else 0,
                        'iss': float(row[8]) if row[8] else 0,
                        'inss': float(row[9]) if row[9] else 0,
                        'total_impostos': float(row[10]) if row[10] else 0,
                        'carga_tributaria_pct': float(row[11]) if row[11] else 0,
                    })

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error querying tax analysis: {e}")
            return f"Erro ao consultar análise tributária: {str(e)}"


class QueryCustomSQLTool(BaseTool):
    name: str = "Query Custom SQL"
    description: str = (
        "Executa query SQL customizada no Data Warehouse OMIE. "
        "ATENÇÃO: Use apenas para queries complexas não cobertas por outras ferramentas. "
        "Input: query SQL completa (SELECT apenas, sem UPDATE/DELETE/DROP). "
        "Tabelas disponíveis: fact_financial_transactions, dim_clients, dim_categories, "
        "dim_dates, dim_cost_centers, dim_departments. "
        "Retorna: Resultado da query em JSON."
    )

    def _run(self, sql_query: str) -> str:
        """Execute the tool."""
        try:
            # Security check: only allow SELECT queries
            query_upper = sql_query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return "Erro: Apenas queries SELECT são permitidas"

            forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            if any(keyword in query_upper for keyword in forbidden_keywords):
                return f"Erro: Query contém palavras proibidas: {', '.join(forbidden_keywords)}"

            engine = get_db_engine()

            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = result.fetchall()
                columns = result.keys()

                if not rows:
                    return "Query executada com sucesso, mas não retornou resultados"

                # Format results
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, Decimal):
                            value = float(value)
                        row_dict[col] = value
                    data.append(row_dict)

                # Limit results to prevent huge responses
                if len(data) > 100:
                    data = data[:100]
                    return json.dumps({
                        'warning': f'Resultados limitados a 100 linhas (total: {len(rows)})',
                        'data': data
                    }, cls=DecimalEncoder, ensure_ascii=False, indent=2)

                return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error executing custom SQL: {e}")
            return f"Erro ao executar query customizada: {str(e)}"


def get_datawarehouse_tools():
    """Get all Data Warehouse analysis tools."""
    return [
        QueryRevenueByClientTool(),
        QueryPLAnalysisTool(),
        QueryCashFlowTool(),
        QueryOverdueAnalysisTool(),
        QueryTaxAnalysisTool(),
        QueryCustomSQLTool(),
    ]

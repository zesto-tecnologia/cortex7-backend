# AI Service Tools Documentation

Complete reference for all AI agent tools and their endpoints.

## Overview

The AI service integrates with existing backend microservices through CrewAI-native tools. Each tool makes HTTP calls to specific service endpoints.

## Service URLs

- **HR Service**: `http://hr-service:8003`
- **Financial Service**: `http://financial-service:8002`
- **Legal Service**: `http://legal-service:8004`
- **Procurement Service**: `http://procurement-service:8005`
- **Documents Service**: `http://documents-service:8006`

## HR Service Tools

### 1. Get Funcionarios (Get Employees)

**Purpose:** Retrieve active employees for a company

**Endpoint:** `GET /funcionarios/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `status` (hardcoded: "ativo")
- `limit` (hardcoded: 100)

**Usage:**
```python
# Agent will call this to get employee list
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "nome": "John Doe",
    "cargo": "Developer",
    "departamento_id": "uuid",
    "status": "ativo"
  }
]
```

**Notes:** This is the primary tool for HR queries. It returns employee IDs that can be used with other HR tools.

---

### 2. Get Ferias (Get Vacation Info)

**Purpose:** Get vacation information for a specific employee

**Endpoint:** `GET /ferias/funcionario/{funcionario_id}`

**Parameters:**
- `funcionario_id` (required, UUID string)

**Usage:**
```python
# Must first get employee ID from Get Funcionarios
# Then query vacation info for that employee
"funcionario_id": "employee-uuid-here"
```

**Returns:**
```json
{
  "funcionario_id": "uuid",
  "periodo_aquisitivo": "2024-2025",
  "dias_disponiveis": 20,
  "dias_utilizados": 10,
  "historico": [...]
}
```

**Notes:** Requires employee ID. Use two-step approach: first get employees, then query vacation for specific employee.

---

### 3. Get Contratos Trabalhistas (Employment Contracts)

**Purpose:** Get employment contracts for a specific employee

**Endpoint:** `GET /contratos/funcionario/{funcionario_id}`

**Parameters:**
- `funcionario_id` (required, UUID string)

**Usage:**
```python
# Must first get employee ID from Get Funcionarios
"funcionario_id": "employee-uuid-here"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "funcionario_id": "uuid",
    "tipo_contrato": "CLT",
    "data_inicio": "2023-01-01",
    "salario": 5000.00
  }
]
```

**Notes:** Returns all contracts for the employee (current and historical).

---

## Financial Service Tools

### 1. Get Contas Pagar (Accounts Payable)

**Purpose:** Retrieve accounts payable for a company

**Endpoint:** `GET /contas-pagar/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `limit` (hardcoded: 100)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "fornecedor_id": "uuid",
    "valor": 1500.00,
    "data_vencimento": "2024-12-31",
    "status": "pendente"
  }
]
```

---

### 2. Get Fornecedores (Suppliers)

**Purpose:** Retrieve supplier information

**Endpoint:** `GET /fornecedores/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `limit` (hardcoded: 100)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "nome": "Supplier Name",
    "cnpj": "12345678000190",
    "contato": "contact@supplier.com"
  }
]
```

---

### 3. Get Centros Custo (Cost Centers)

**Purpose:** Retrieve cost centers for budget tracking

**Endpoint:** `GET /centros-custo/`

**Parameters:**
- `empresa_id` (required, UUID string)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "codigo": "CC001",
    "nome": "Marketing",
    "orcamento": 50000.00
  }
]
```

---

## Legal Service Tools

### 1. Get Contratos Legais (Legal Contracts)

**Purpose:** Retrieve legal contracts

**Endpoint:** `GET /contratos/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `limit` (hardcoded: 100)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "tipo": "service_agreement",
    "contraparte": "Partner Company",
    "data_inicio": "2024-01-01",
    "data_fim": "2024-12-31",
    "status": "vigente"
  }
]
```

---

### 2. Get Prazos Legais (Legal Deadlines)

**Purpose:** Get upcoming legal deadlines

**Endpoint:** `GET /prazos/todos/{empresa_id}`

**Parameters:**
- `empresa_id` (required, UUID string - path parameter)

**Usage:**
```python
# Note: empresa_id is part of the URL path
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
{
  "total_prazos": 5,
  "prazos": [
    {
      "tipo": "contract_expiration",
      "descricao": "Contract renewal deadline",
      "data": "2024-12-15",
      "dias_restantes": 30,
      "prioridade": "high"
    }
  ]
}
```

---

### 3. Get Processos Legais (Legal Processes)

**Purpose:** Get ongoing legal processes and lawsuits

**Endpoint:** `GET /processos/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `limit` (hardcoded: 100)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "numero_processo": "1234567-89.2024.8.00.0000",
    "tipo": "trabalhista",
    "status": "em_andamento",
    "risco": "medio"
  }
]
```

---

## Documents Service Tools

### 1. Search Documents

**Purpose:** Semantic search for documents

**Endpoint:** `GET /search/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `query` (required, string - search query)
- `limit` (hardcoded: 10)

**Usage:**
```python
{
  "empresa_id": "11111111-1111-1111-1111-111111111111",
  "query": "employee handbook"
}
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "titulo": "Employee Handbook 2024",
    "tipo": "policy",
    "relevance_score": 0.95
  }
]
```

---

### 2. Get Documents

**Purpose:** List all documents for a company

**Endpoint:** `GET /`

**Parameters:**
- `empresa_id` (required, UUID string)
- `limit` (hardcoded: 50)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "titulo": "Document Title",
    "tipo": "contract",
    "departamento": "Legal",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Procurement Service Tools

### 1. Get Ordens Compra (Purchase Orders)

**Purpose:** Retrieve purchase orders

**Endpoint:** `GET /ordens-compra/`

**Parameters:**
- `empresa_id` (required, UUID string)

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "numero": "PO-2024-001",
    "fornecedor_id": "uuid",
    "valor_total": 10000.00,
    "status": "aprovado"
  }
]
```

---

### 2. Get Aprovacoes Pendentes (Pending Approvals)

**Purpose:** Get purchase orders awaiting approval

**Endpoint:** `GET /aprovacoes/`

**Parameters:**
- `empresa_id` (required, UUID string)
- `status` (hardcoded: "pendente")

**Usage:**
```python
"empresa_id": "11111111-1111-1111-1111-111111111111"
```

**Returns:**
```json
[
  {
    "id": "uuid",
    "ordem_compra_id": "uuid",
    "nivel_aprovacao": 1,
    "status": "pendente",
    "aprovador_id": "uuid"
  }
]
```

---

## Tool Usage Patterns

### Pattern 1: Direct Query (Most Tools)
```
User asks → Agent uses tool with empresa_id → Returns data
```
Example: "Show me our suppliers" → Get Fornecedores tool

### Pattern 2: Two-Step Query (HR Vacation & Contracts)
```
User asks → Get Funcionarios (list employees) 
         → Get Ferias/Contratos (specific employee)
```
Example: "Show vacation days for John" → Get Funcionarios → Find John's ID → Get Ferias with that ID

### Pattern 3: Search & Retrieve (Documents)
```
User asks → Search Documents (semantic search)
         → Get specific documents if needed
```

## Testing Tools

You can test tools directly by calling the endpoints:

```bash
# Test HR employees
curl "http://localhost:8003/funcionarios/?empresa_id=11111111-1111-1111-1111-111111111111&status=ativo&limit=100"

# Test legal deadlines
curl "http://localhost:8004/prazos/todos/11111111-1111-1111-1111-111111111111"

# Test financial accounts payable
curl "http://localhost:8002/contas-pagar/?empresa_id=11111111-1111-1111-1111-111111111111&limit=100"

# Test document search
curl "http://localhost:8006/search/?empresa_id=11111111-1111-1111-1111-111111111111&query=contract&limit=10"
```

## Common Test UUID

For testing purposes:
```
11111111-1111-1111-1111-111111111111
```

## Error Handling

All tools return error messages in this format:
```
"Error retrieving [resource]: [error details]"
```

Common errors:
- **404 Not Found**: Endpoint doesn't exist or resource not found
- **405 Method Not Allowed**: Wrong HTTP method for endpoint
- **500 Server Error**: Service is down or internal error
- **Connection Error**: Service is unreachable

## Tool Implementation Notes

### CrewAI Native Format

All tools use CrewAI's `BaseTool` class:

```python
from crewai.tools import BaseTool

class MyTool(BaseTool):
    name: str = "Tool Name"
    description: str = "What the tool does. Input: parameters"
    
    def _run(self, param1: str, param2: str = "") -> str:
        """Execute the tool."""
        # Implementation
        return "Result as string"
```

### Key Points:
- Inherit from `crewai.tools.BaseTool`
- Define `name` and `description` as class attributes
- Implement `_run()` method (not `_arun()`)
- Return results as strings (JSON-serialized if needed)
- Include parameter descriptions in the `description` field

## Service Health Checks

Before using tools, verify services are healthy:

```bash
curl http://localhost:8003/health  # HR
curl http://localhost:8004/health  # Legal
curl http://localhost:8005/health  # Procurement
curl http://localhost:8006/health  # Documents
curl http://localhost:8002/health  # Financial
```

All should return:
```json
{"status": "healthy"}
```

## See Also

- [README.md](./README.md) - Service architecture and overview
- [SETUP.md](./SETUP.md) - Installation and configuration
- Postman Collection: `/backend/Cortex_API.postman_collection.json`


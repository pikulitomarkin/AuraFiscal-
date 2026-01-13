# 📁 Estrutura Completa do Projeto

```
d:\leitor pdf e geração de notas\
│
├── 📄 app.py                          # ⭐ APLICAÇÃO PRINCIPAL STREAMLIT
│
├── 📄 setup.py                        # Script de inicialização do sistema
├── 📄 setup.ps1                       # Script PowerShell de configuração
├── 📄 requirements.txt                # Dependências do projeto
│
├── 📄 .env.example                    # Exemplo de variáveis de ambiente
├── 📄 .env                            # ⚠️ Configurações (NÃO COMMITAR)
├── 📄 .gitignore                      # Arquivos ignorados pelo Git
│
├── 📄 README.md                       # Documentação principal
├── 📄 INSTALL.md                      # Guia de instalação rápida
│
├── 📂 config/                         # ⚙️ CONFIGURAÇÕES
│   ├── __init__.py
│   ├── settings.py                    # Configurações centralizadas (Pydantic)
│   └── database.py                    # Setup do PostgreSQL + SQLAlchemy
│
├── 📂 src/                            # 🔧 CÓDIGO FONTE PRINCIPAL
│   ├── __init__.py
│   │
│   ├── 📂 auth/                       # 🔐 AUTENTICAÇÃO
│   │   ├── __init__.py
│   │   └── authentication.py          # Login, JWT, bcrypt
│   │
│   ├── 📂 pdf/                        # 📄 PROCESSAMENTO DE PDF
│   │   ├── __init__.py
│   │   └── extractor.py               # Extração via pdfplumber + Regex
│   │
│   ├── 📂 api/                        # 🌐 INTEGRAÇÃO COM API
│   │   ├── __init__.py
│   │   ├── client.py                  # Cliente HTTP assíncrono (httpx)
│   │   └── nfse_service.py            # Lógica de emissão NFS-e
│   │
│   ├── 📂 models/                     # 📊 MODELOS DE DADOS
│   │   ├── __init__.py
│   │   └── schemas.py                 # Schemas Pydantic (validação)
│   │
│   ├── 📂 database/                   # 💾 PERSISTÊNCIA
│   │   ├── __init__.py
│   │   ├── models.py                  # Modelos ORM (SQLAlchemy)
│   │   └── repository.py              # Repository Pattern (CRUD)
│   │
│   └── 📂 utils/                      # 🛠️ UTILITÁRIOS
│       ├── __init__.py
│       ├── logger.py                  # Sistema de logs (Loguru)
│       ├── validators.py              # Validação CPF/CNPJ/Email
│       └── certificate.py             # Gestão de Certificado A1
│
├── 📂 tests/                          # 🧪 TESTES UNITÁRIOS
│   ├── __init__.py
│   ├── test_extractor.py              # Testes do PDF extractor
│   └── test_nfse_service.py           # Testes do serviço NFS-e
│
├── 📂 docs/                           # 📚 DOCUMENTAÇÃO
│   ├── architecture.md                # Arquitetura detalhada do sistema
│   ├── api_payload_example.json       # Exemplos de payload da API
│   ├── database_setup.sql             # Script SQL de criação do BD
│   └── TECHNICAL_REFERENCE.md         # Referência técnica completa
│
├── 📂 .streamlit/                     # 🎨 CONFIGURAÇÕES STREAMLIT
│   └── config.toml                    # Tema, porta, upload size
│
├── 📂 logs/                           # 📋 LOGS DA APLICAÇÃO
│   └── nfse_automation.log            # Log principal (rotacionado)
│
├── 📂 certs/                          # 🔒 CERTIFICADOS DIGITAIS
│   └── seu_certificado.pfx            # ⚠️ Certificado A1 (NÃO COMMITAR)
│
└── 📂 uploads/                        # 📤 ARQUIVOS TEMPORÁRIOS
    └── (PDFs temporários)

```

---

## 🎯 Arquivos Principais

### 1. `app.py` (Aplicação Streamlit)
**Responsabilidade**: Interface web completa  
**Componentes**:
- Login e autenticação
- Upload de PDF
- Dashboard de emissão
- Relatórios e configurações

### 2. `config/settings.py` (Configurações)
**Responsabilidade**: Gerenciamento de variáveis de ambiente  
**Usa**: Pydantic Settings para validação

### 3. `src/pdf/extractor.py` (Extração PDF)
**Responsabilidade**: Ler PDFs e extrair dados estruturados  
**Tecnologias**: pdfplumber + Regex

### 4. `src/api/nfse_service.py` (Serviço NFS-e)
**Responsabilidade**: Orquestração de emissão em lote  
**Recursos**: Async, retry, callbacks

### 5. `src/database/repository.py` (Persistência)
**Responsabilidade**: Acesso a dados (Repository Pattern)  
**ORM**: SQLAlchemy 2.0 (async)

---

## 🔄 Fluxo de Execução

```
1. Inicialização
   ├── setup.py → Cria tabelas no PostgreSQL
   ├── app.py → Inicia Streamlit
   └── config/settings.py → Carrega variáveis .env

2. Autenticação
   ├── Login Form (Streamlit)
   ├── src/auth/authentication.py → Valida credenciais
   └── JWT Token → Session State

3. Upload PDF
   ├── Streamlit File Uploader
   ├── src/pdf/extractor.py → Extrai dados
   └── Validação → CPF, Hash, Nome

4. Processamento
   ├── src/api/nfse_service.py → Emissão em lote
   ├── src/api/client.py → Chamadas HTTP assíncronas
   ├── API Gov.br → Recebe payload
   └── Resposta → Protocolo NFS-e

5. Persistência
   ├── src/database/repository.py → Salva resultados
   ├── PostgreSQL → Armazena dados
   └── Logs → Registra operação
```

---

## 📦 Módulos e Suas Funções

### `config/` - Configuração
| Arquivo | Função |
|---------|--------|
| settings.py | Carrega e valida variáveis do .env |
| database.py | Conexão PostgreSQL + Session Management |

### `src/auth/` - Autenticação
| Arquivo | Função |
|---------|--------|
| authentication.py | Login, JWT, bcrypt, session |

### `src/pdf/` - PDF
| Arquivo | Função |
|---------|--------|
| extractor.py | Extração via pdfplumber, Regex, validação |

### `src/api/` - API
| Arquivo | Função |
|---------|--------|
| client.py | Cliente HTTP assíncrono com retry |
| nfse_service.py | Lógica de negócio de emissão |

### `src/models/` - Modelos
| Arquivo | Função |
|---------|--------|
| schemas.py | Pydantic models (validação de dados) |

### `src/database/` - Banco
| Arquivo | Função |
|---------|--------|
| models.py | SQLAlchemy ORM models |
| repository.py | Repository Pattern (CRUD async) |

### `src/utils/` - Utilitários
| Arquivo | Função |
|---------|--------|
| logger.py | Loguru setup (console + file) |
| validators.py | CPF, CNPJ, Email, Hash |
| certificate.py | Certificado A1 (load, validate, sign) |

---

## 🚀 Como Navegar no Código

### Para Adicionar Nova Funcionalidade

1. **Nova página Streamlit**: Edite `app.py` → função `render_*`
2. **Nova validação**: Edite `src/utils/validators.py`
3. **Novo endpoint API**: Edite `src/api/client.py` ou `nfse_service.py`
4. **Nova tabela BD**: Edite `src/database/models.py` → rode `setup.py`
5. **Novo schema**: Edite `src/models/schemas.py`

### Para Debugar Problemas

1. **Erro de autenticação**: `src/auth/authentication.py` + logs
2. **PDF não extrai**: `src/pdf/extractor.py` + regex patterns
3. **API falha**: `src/api/client.py` + logs + `httpx` debug
4. **Banco de dados**: `config/database.py` + PostgreSQL logs
5. **Certificado**: `src/utils/certificate.py` + validade

### Para Entender o Sistema

1. **Comece por**: `README.md` → Visão geral
2. **Depois**: `docs/architecture.md` → Arquitetura
3. **Detalhes**: `docs/TECHNICAL_REFERENCE.md` → Referência
4. **API**: `docs/api_payload_example.json` → Payload
5. **Código**: `app.py` → Fluxo principal

---

## 🎨 Convenções de Código

### Nomenclatura

```python
# Classes: PascalCase
class NFSeService:
    pass

# Funções/métodos: snake_case
def process_batch():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_BATCH_SIZE = 600

# Variáveis: snake_case
total_records = 100
```

### Documentação

```python
def funcao_exemplo(parametro: str) -> bool:
    """
    Breve descrição da função.
    
    Args:
        parametro: Descrição do parâmetro
        
    Returns:
        Descrição do retorno
        
    Raises:
        ValueError: Quando parametro é inválido
    """
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional

def process(
    records: List[Dict[str, str]], 
    config: Optional[Dict] = None
) -> List[ProcessingResult]:
    pass
```

---

## 📊 Dependências Entre Módulos

```
app.py (Streamlit UI)
  ↓
  ├─→ src/auth/authentication.py
  ├─→ src/pdf/extractor.py
  ├─→ src/api/nfse_service.py
  │     ↓
  │     ├─→ src/api/client.py
  │     ├─→ src/models/schemas.py
  │     └─→ src/utils/certificate.py
  │
  └─→ src/database/repository.py
        ↓
        ├─→ src/database/models.py
        └─→ config/database.py
              ↓
              └─→ config/settings.py
```

---

## 🔐 Arquivos Sensíveis (NÃO COMMITAR)

```
⚠️ NUNCA COMMITAR:
├── .env                    # Senhas, secrets, URLs
├── certs/*.pfx             # Certificados digitais
├── certs/*.p12             # Certificados
├── certs/*.pem             # Chaves privadas
├── logs/*.log              # Logs podem conter dados sensíveis
└── uploads/*               # PDFs com dados pessoais
```

---

**Última Atualização**: 11/01/2026  
**Versão da Estrutura**: 1.0

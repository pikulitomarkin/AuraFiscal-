# Arquitetura do Sistema de Automação NFS-e

## Visão Geral

Sistema desenvolvido em Python para automação de emissão em lote de Notas Fiscais de Serviço Eletrônica (NFS-e) através da API Nacional do Gov.br, com interface web em Streamlit.

## Stack Tecnológica

### Frontend
- **Streamlit 1.30+**: Interface web interativa e responsiva
- **Pandas**: Manipulação e visualização de dados tabulares

### Backend
- **Python 3.11+**: Linguagem principal
- **httpx**: Cliente HTTP assíncrono para comunicação com APIs
- **asyncio**: Processamento assíncrono e concorrente

### Processamento de Documentos
- **pdfplumber**: Extração de texto de PDFs
- **Regex**: Parsing de dados estruturados (CPF, Hash, Nomes)

### Persistência
- **PostgreSQL**: Banco de dados relacional
- **SQLAlchemy 2.0**: ORM assíncrono
- **Alembic**: Migrações de banco de dados

### Segurança
- **bcrypt**: Hash de senhas
- **python-jose**: Tokens JWT
- **pyOpenSSL**: Gestão de certificado digital A1
- **cryptography**: Operações criptográficas

### Validação e Qualidade
- **Pydantic**: Validação de schemas e dados
- **validate-docbr**: Validação de CPF/CNPJ
- **Loguru**: Sistema de logs estruturado

## Arquitetura de Camadas

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│                    (Streamlit UI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Login     │  │   Upload    │  │  Reports    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Auth        │  │  PDF Extract │  │  NFS-e       │ │
│  │  Manager     │  │  Service     │  │  Service     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Validators  │  │  Certificate │  │  API Client  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    DATA ACCESS LAYER                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Repository  │  │  ORM Models  │  │  Database    │ │
│  │  Pattern     │  │  (SQLAlchemy)│  │  Session     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   EXTERNAL SERVICES                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PostgreSQL  │  │  API Gov.br  │  │  File System │ │
│  │  Database    │  │  NFS-e       │  │  (PDFs/Logs) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

### 1. Autenticação
```
User → Login Form → Auth Manager → Verify Credentials → JWT Token → Session State
```

### 2. Upload e Extração
```
PDF Upload → pdfplumber → Regex Extraction → Validation → Filtered Records
```

### 3. Processamento em Lote
```
Records → Batch Split → Async Tasks → API Calls → Response Handling → Database Save
```

### 4. Emissão Individual
```
Record → Build Payload → Sign with A1 → POST API → Parse Response → Log Result
```

## Componentes Principais

### 1. Authentication Manager (`src/auth/authentication.py`)
- Verifica credenciais
- Gera e valida tokens JWT
- Integração com bcrypt para hashing

### 2. PDF Extractor (`src/pdf/extractor.py`)
- Extrai texto de PDFs usando pdfplumber
- Aplica regex patterns para localizar dados
- Valida CPFs e estrutura dos dados
- Retorna lista de registros estruturados

### 3. NFS-e Service (`src/api/nfse_service.py`)
- Orquestra emissão em lote
- Gerencia concorrência (asyncio)
- Retry logic e error handling
- Callback de progresso

### 4. API Client (`src/api/client.py`)
- Cliente HTTP assíncrono (httpx)
- Retry automático com exponential backoff
- Timeout configurável
- Logging de requisições

### 5. Certificate Manager (`src/utils/certificate.py`)
- Carrega certificado A1 (.pfx)
- Valida validade do certificado
- Extrai informações do titular
- Assina payloads

### 6. Repository Pattern (`src/database/repository.py`)
- Abstração de acesso a dados
- Operações CRUD assíncronas
- Transações gerenciadas
- Consultas otimizadas

## Padrões de Design Utilizados

### 1. Singleton
- `NFSeService`: Instância única compartilhada
- `CertificateManager`: Gerenciamento global do certificado
- `DocumentValidator`: Validador reutilizável

### 2. Repository Pattern
- Separação entre lógica de negócio e acesso a dados
- Facilita testes e manutenção
- Operações assíncronas encapsuladas

### 3. Dependency Injection
- Configurações via Pydantic Settings
- Injeção de dependências em serviços
- Facilita testes unitários

### 4. Factory Pattern
- `get_nfse_service()`: Lazy initialization
- `get_db_session()`: Context manager para sessões

### 5. Strategy Pattern
- Diferentes estratégias de extração de PDF
- Múltiplos validadores intercambiáveis

## Segurança

### 1. Autenticação
- Passwords com bcrypt (cost factor 12)
- Tokens JWT com expiração (8 horas)
- Session state do Streamlit

### 2. Certificado Digital
- Armazenamento seguro (.pfx protegido)
- Validação de validade antes de uso
- Assinatura de payloads

### 3. API Communication
- HTTPS obrigatório
- Certificate-based authentication
- Retry com backoff exponencial

### 4. Database
- Prepared statements (SQLAlchemy)
- Transações ACID
- Connection pooling

## Performance

### 1. Processamento Assíncrono
- asyncio para I/O-bound operations
- Concorrência configurável (default: 10)
- Batch processing

### 2. Database Optimization
- Índices em campos de busca
- Batch inserts
- Connection pooling

### 3. Caching
- Session state do Streamlit
- Singleton services

## Tratamento de Erros

### 1. Níveis de Tratamento
- **API**: Retry automático, fallback
- **Processamento**: Isolamento de erros por registro
- **Database**: Rollback automático
- **UI**: Mensagens amigáveis

### 2. Logging
- Logs estruturados (Loguru)
- Níveis: DEBUG, INFO, WARNING, ERROR
- Rotação automática (10 MB)
- Retenção de 30 dias

## Escalabilidade

### Pontos de Escalabilidade:
1. **Horizontal**: Múltiplas instâncias Streamlit (load balancer)
2. **Concorrência**: Ajustar `CONCURRENT_REQUESTS`
3. **Database**: PostgreSQL suporta réplicas e sharding
4. **Async Processing**: Celery para jobs background (futuro)

## Próximos Passos (Roadmap)

1. **Autenticação Avançada**: OAuth2, LDAP
2. **Relatórios Avançados**: Grafana, metabase
3. **Notificações**: Email, SMS, Webhook
4. **Multi-tenant**: Suporte a múltiplas empresas
5. **API REST**: Endpoints para integração externa
6. **Testes**: Coverage > 80%
7. **CI/CD**: GitHub Actions, Docker
8. **Monitoramento**: Prometheus, APM

---

**Versão**: 1.0.0  
**Última Atualização**: Janeiro 2026  
**Autor**: Arquiteto de Software Sênior

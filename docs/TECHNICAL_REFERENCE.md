# 📚 Referência Técnica - Sistema NFS-e

## Sumário Executivo

Sistema automatizado de emissão em lote de NFS-e Nacional desenvolvido em Python com interface Streamlit, processando 100-600 registros por operação através de extração via PDF e integração assíncrona com API Gov.br.

---

## 1. Especificações Técnicas

### 1.1 Requisitos de Sistema

| Componente | Versão Mínima | Recomendado |
|------------|---------------|-------------|
| Python | 3.11 | 3.11+ |
| PostgreSQL | 12 | 14+ |
| RAM | 2 GB | 4 GB+ |
| Espaço em Disco | 500 MB | 2 GB+ |
| CPU | 2 cores | 4 cores+ |

### 1.2 Dependências Principais

```
streamlit==1.30.0          # Framework web
httpx==0.25.2              # Cliente HTTP assíncrono
sqlalchemy==2.0.25         # ORM
pdfplumber==0.10.3         # Processamento PDF
pydantic==2.5.3            # Validação de dados
bcrypt==4.1.2              # Segurança
loguru==0.7.2              # Logging
```

---

## 2. Arquitetura de Componentes

### 2.1 Camadas da Aplicação

```
┌─────────────────────────────────────────┐
│  PRESENTATION (Streamlit)               │
│  - Login, Upload, Dashboard, Reports    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  BUSINESS LOGIC                         │
│  - Auth Manager                         │
│  - PDF Extractor                        │
│  - NFS-e Service                        │
│  - Validators                           │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  DATA ACCESS (Repository Pattern)       │
│  - NFSeRepository                       │
│  - LogRepository                        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  PERSISTENCE                            │
│  - PostgreSQL                           │
│  - SQLAlchemy ORM                       │
└─────────────────────────────────────────┘
```

### 2.2 Fluxo de Dados

#### Fluxo de Emissão NFS-e

```
1. Upload PDF → 2. Extração → 3. Validação → 4. API Call → 5. Persistência
                     ↓             ↓             ↓             ↓
                 Regex         CPF/Hash      Assíncrono    PostgreSQL
                 Pattern       Validator     (httpx)       (SQLAlchemy)
```

---

## 3. API Nacional NFS-e - Referência

### 3.1 Endpoint de Emissão

```http
POST https://api.nfse.gov.br/v1/nfse/emitir
Content-Type: application/json
X-Certificate: [PEM Certificate]
```

### 3.2 Estrutura de Payload

```json
{
  "prestador": {
    "cnpj": "string (14 dígitos)",
    "inscricao_municipal": "string",
    "razao_social": "string (max 150)"
  },
  "tomador": {
    "cpf": "string (11 dígitos)",
    "nome": "string (max 150)"
  },
  "servico": {
    "descricao": "string (max 2000)",
    "valor_servico": "decimal",
    "aliquota_iss": "decimal (0-5)",
    "item_lista_servico": "string (LC 116/2003)"
  },
  "hash_transacao": "string (único)"
}
```

### 3.3 Códigos de Resposta

| Código | Descrição | Ação |
|--------|-----------|------|
| 200 | Sucesso | NFS-e emitida |
| 400 | Erro de validação | Verificar payload |
| 401 | Não autorizado | Verificar certificado |
| 429 | Rate limit | Retry com backoff |
| 500 | Erro servidor | Retry 3x |

### 3.4 Rate Limits

- **Requisições/minuto**: 100
- **Lote máximo**: 600 registros
- **Timeout**: 30 segundos
- **Retry**: Exponential backoff (2s, 4s, 8s)

---

## 4. Extração de PDF

### 4.1 Padrões Regex

```python
PATTERNS = {
    'cpf': r'\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b',
    'hash': r'\b[A-Fa-f0-9]{32,64}\b',
    'nome': r'(?:Nome|Cliente|Tomador)[:\s]+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ][a-záàâãéèêíïóôõöúçñ\s]+)'
}
```

### 4.2 Formato de PDF Esperado

**Estrutura mínima por registro:**

```
Nome: João da Silva
CPF: 123.456.789-00
Hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
---
```

### 4.3 Validações Aplicadas

- ✅ CPF válido (dígitos verificadores)
- ✅ Hash presente (mínimo 32 caracteres)
- ✅ Nome não vazio
- ✅ Campos obrigatórios preenchidos

---

## 5. Banco de Dados

### 5.1 Schema Principal

#### Tabela: `nfse_emissoes`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | PK |
| hash_transacao | VARCHAR(64) | Único, Indexed |
| numero_nfse | VARCHAR(20) | Número da nota |
| protocolo | VARCHAR(50) | Protocolo de recepção |
| cpf_tomador | VARCHAR(11) | Indexed |
| nome_tomador | VARCHAR(150) | - |
| status | VARCHAR(20) | sucesso/erro/pendente |
| mensagem | TEXT | Detalhes |
| valor_servico | NUMERIC(10,2) | - |
| created_at | TIMESTAMP | Indexed |

#### Tabela: `logs_processamento`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | PK |
| batch_id | VARCHAR(36) | UUID, Unique |
| total_registros | INTEGER | - |
| sucessos | INTEGER | - |
| erros | INTEGER | - |
| nome_arquivo | VARCHAR(255) | - |
| duracao_segundos | INTEGER | - |

### 5.2 Índices Criados

```sql
CREATE INDEX idx_nfse_hash ON nfse_emissoes(hash_transacao);
CREATE INDEX idx_nfse_cpf ON nfse_emissoes(cpf_tomador);
CREATE INDEX idx_nfse_status ON nfse_emissoes(status);
CREATE INDEX idx_nfse_created ON nfse_emissoes(created_at);
```

### 5.3 Queries Otimizadas

```python
# Buscar por CPF (últimas 100)
SELECT * FROM nfse_emissoes 
WHERE cpf_tomador = '12345678900'
ORDER BY created_at DESC 
LIMIT 100;

# Estatísticas do mês
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'sucesso') as sucessos
FROM nfse_emissoes
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE);
```

---

## 6. Segurança

### 6.1 Certificado Digital A1

**Formato**: PKCS#12 (.pfx)  
**Algoritmo**: RSA 2048+  
**Validação**: Antes de cada emissão

```python
# Verificação de validade
if certificate_manager.is_valid():
    cert_pem = certificate_manager.get_certificate_pem()
```

### 6.2 Autenticação

**Método**: JWT (JSON Web Token)  
**Expiração**: 8 horas  
**Hash de Senha**: bcrypt (cost factor 12)

```python
# Login
token = auth_manager.login(username, password)

# Validação
payload = auth_manager.verify_token(token)
```

### 6.3 Proteções Implementadas

- ✅ CSRF protection (Streamlit)
- ✅ SQL Injection (Prepared Statements)
- ✅ Senhas hasheadas (bcrypt)
- ✅ Tokens com expiração
- ✅ Certificado validado
- ✅ HTTPS recomendado

---

## 7. Performance

### 7.1 Benchmarks

| Operação | Tempo Médio | Throughput |
|----------|-------------|------------|
| Extração PDF (100 reg) | 2-3s | 33-50 reg/s |
| Emissão API (individual) | 300-500ms | 2-3 req/s |
| Lote 100 (concorrente) | 15-20s | 5-7 reg/s |
| Lote 600 (concorrente) | 90-120s | 5-7 reg/s |

### 7.2 Otimizações

```python
# Concorrência configurável
CONCURRENT_REQUESTS = 10  # Ajustar conforme API

# Batch processing
for i in range(0, total, batch_size):
    batch = registros[i:i + batch_size]
    tasks = [process(r) for r in batch]
    await asyncio.gather(*tasks)
```

### 7.3 Gargalos Identificados

1. **API Rate Limit**: Limita a 100 req/min
2. **Certificado**: Operação síncrona de assinatura
3. **Database**: Inserts individuais (usar batch)

---

## 8. Monitoramento

### 8.1 Logs Estruturados

```python
# Formato
{time} | {level} | {name}:{function}:{line} - {message}

# Níveis
DEBUG: Detalhes de execução
INFO: Operações normais
WARNING: Situações anormais não críticas
ERROR: Erros que impedem operação
```

### 8.2 Métricas Recomendadas

- Taxa de sucesso por lote
- Tempo médio de processamento
- Erros por tipo (API, validação, etc)
- Volume de emissões por dia/mês
- Uso de recursos (CPU, RAM, DB)

### 8.3 Alertas

```yaml
Críticos:
  - Taxa de erro > 10%
  - API offline > 5min
  - Certificado expira < 7 dias
  - Disk space < 10%

Avisos:
  - Taxa de erro > 5%
  - Processamento > 2min
  - Certificado expira < 30 dias
```

---

## 9. Troubleshooting

### 9.1 Problemas Comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| CPF inválido | Dígito verificador | Validar antes de enviar |
| API timeout | Rede lenta | Aumentar NFSE_API_TIMEOUT |
| Certificado expirado | Validade vencida | Renovar certificado |
| Erro 401 | Cert não reconhecido | Verificar emissora do cert |
| PDF vazio | Texto não extraível | Usar OCR ou PDF editável |

### 9.2 Comandos de Diagnóstico

```powershell
# Verificar logs
Get-Content logs\nfse_automation.log -Tail 50

# Testar banco
psql -U nfse_user -d nfse_db -c "SELECT COUNT(*) FROM nfse_emissoes;"

# Verificar certificado
python -c "from src.utils.certificate import certificate_manager; print(certificate_manager.get_certificate_info())"

# Testar API
python -c "from src.api.nfse_service import get_nfse_service; import asyncio; print(asyncio.run(get_nfse_service().consultar_status_api()))"
```

---

## 10. Roadmap Técnico

### v1.1 (Q1 2026)
- [ ] API REST para integração externa
- [ ] Webhooks de notificação
- [ ] Dashboard analytics avançado
- [ ] Suporte a múltiplos prestadores

### v1.2 (Q2 2026)
- [ ] Processamento background (Celery)
- [ ] Cache distribuído (Redis)
- [ ] Replicação de banco
- [ ] Kubernetes deployment

### v1.3 (Q3 2026)
- [ ] Machine Learning para detecção de erros
- [ ] OCR para PDFs escaneados
- [ ] Multi-tenancy
- [ ] Auditoria completa

---

## 11. Contatos e Referências

### Documentação Oficial
- **NFS-e Nacional**: https://nfse.gov.br/documentacao
- **Streamlit**: https://docs.streamlit.io
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **httpx**: https://www.python-httpx.org

### Suporte Técnico
- **Logs**: `logs/nfse_automation.log`
- **Issues**: [GitHub Issues]
- **Email**: suporte@empresa.com.br

---

**Versão do Documento**: 1.0  
**Data**: 11/01/2026  
**Autor**: Equipe de Desenvolvimento

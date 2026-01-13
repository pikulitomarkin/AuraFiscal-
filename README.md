# Sistema de Automação de Emissão de NFS-e Nacional (API ADN)

> **⚠️ Versão 2.0.0** - Atualizado para API ADN Oficial do Gov.br

## 📋 Descrição

Sistema automatizado para emissão em lote de Notas Fiscais de Serviço Eletrônica (NFS-e) através da **API NFS-e ADN (Ambiente de Disponibilização Nacional)** oficial do Gov.br, com extração de dados via PDF e interface web amigável.

### 🆕 Novidades da Versão 2.0
- ✅ **Integração com API ADN Oficial** - Endpoint `/adn/DFe`
- ✅ **Geração de XML Padrão SPED** - Formato oficial do governo
- ✅ **Compressão GZIP + Base64** - Otimização de tráfego de rede
- ✅ **Processamento em Lote Otimizado** - Até 50 documentos por requisição
- ✅ **Chave de Acesso NFS-e** - Identificador único de 50 caracteres
- ✅ **NSU (Número Sequencial Único)** - Rastreamento completo

## 🏗️ Arquitetura

```
nfse-automation/
├── app.py                      # Aplicação principal Streamlit
├── requirements.txt            # Dependências do projeto
├── .env.example               # Exemplo de variáveis de ambiente
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configurações centralizadas
│   └── database.py            # Configuração do PostgreSQL
├── src/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── authentication.py  # Sistema de autenticação
│   ├── pdf/
│   │   ├── __init__.py
│   │   └── extractor.py       # Extração de dados do PDF
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py          # Cliente HTTP assíncrono (API ADN)
│   │   └── nfse_service.py    # Lógica de integração com API ADN
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Modelos de dados (Pydantic + API ADN)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py          # Modelos ORM (SQLAlchemy)
│   │   └── repository.py      # Camada de acesso a dados
│   └── utils/
│       ├── __init__.py
│       ├── xml_generator.py   # 🆕 Gerador de XML NFS-e
│       ├── validators.py      # Validações (CPF, CNPJ, etc)
│       ├── certificate.py     # Gestão de certificado digital A1
│       └── logger.py          # Sistema de logs
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_nfse_service.py
│   └── test_api_adn_integration.py  # 🆕 Testes API ADN
└── docs/
    ├── api_adn_reference.json      # 🆕 Especificação OpenAPI ADN
    ├── MIGRATION_GUIDE_ADN.md      # 🆕 Guia de Migração
    ├── api_payload_example.json
    └── architecture.md
```

## 🚀 Tecnologias

### Core
- **Frontend**: Streamlit 1.30+
- **Backend**: Python 3.11+
- **HTTP Client**: httpx (assíncrono)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async) + asyncpg

### Processamento
- **PDF**: pdfplumber + Regex
- **XML**: xml.etree.ElementTree (geração de XML NFS-e)
- **Compressão**: gzip + base64 (payload API ADN)

### Validação & Segurança
- **Validação**: Pydantic 2.5 + validate-docbr
- **Autenticação**: JWT + bcrypt
- **Certificado Digital A1**: pyOpenSSL + cryptography

### API ADN
- **Endpoint**: `https://api.nfse.gov.br/adn/DFe`
- **Formato**: XML → GZIP → Base64
- **Namespace**: `http://www.sped.fazenda.gov.br/nfse`
- **Versão**: 1.00

## ⚙️ Configuração

1. Clone o repositório
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente: `venv\Scripts\activate` (Windows)
4. Instale as dependências: `pip install -r requirements.txt`
5. Configure as variáveis de ambiente (copie `.env.example` para `.env`)
6. Execute as migrações do banco de dados
7. Inicie a aplicação: `streamlit run app.py`

## 📊 Funcionalidades

### Core
- ✅ Autenticação segura de usuários (JWT + bcrypt)
- ✅ Upload e processamento de PDFs em lote (100-600 registros)
- ✅ Extração automatizada via Regex (Nome, CPF, Hash)
- ✅ Persistência de resultados em PostgreSQL
- ✅ Logs detalhados de operações (Loguru)
- ✅ Tratamento robusto de erros

### API ADN (Novidades v2.0)
- ✅ **Geração de XML NFS-e Padrão SPED** - Formato oficial
- ✅ **Compressão GZIP** - Redução de 70-80% no tráfego
- ✅ **Codificação Base64** - Transporte seguro
- ✅ **Processamento em Lote (até 50 docs)** - Otimizado
- ✅ **Integração Assíncrona** - Alta performance
- ✅ **Chave de Acesso Única** - 50 caracteres
- ✅ **NSU (Número Sequencial)** - Rastreamento completo
- ✅ **Barra de Progresso em Tempo Real** - Feedback visual
- ✅ **Assinatura Digital com Certificado A1** - Segurança

### Ambientes
- 🔧 **Homologação**: Testes sem validade fiscal
- ✅ **Produção**: Emissão oficial de NFS-e

## 📝 Licença

Proprietário - Uso Interno

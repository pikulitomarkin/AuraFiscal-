# 📋 Documentação de Entrega - Sistema de Emissão de NFS-e Nacional

## 📌 Visão Geral do Projeto

Sistema completo para **emissão automatizada de Notas Fiscais de Serviço Eletrônica (NFS-e)** no padrão nacional, com interface web intuitiva desenvolvida em Streamlit. O sistema permite emissão individual e em lote, extração automática de dados de PDFs, geração de DANFSE com QR Code, e gestão completa do histórico de notas emitidas.

---

## 🎯 Funcionalidades Principais

### 1. 📝 Emissão Individual de NFS-e
- Formulário completo para cadastro de dados do tomador
- Configuração detalhada do serviço prestado
- Validação automática de CPF/CNPJ
- Cálculo automático de ISS e valores
- Geração simultânea de XML assinado e DANFSE (PDF)
- **Download direto** dos arquivos XML e PDF após emissão

### 2. 📋 Emissão em Lote
- **Extração automática** de dados de arquivos PDF
- Processamento de múltiplas NFS-e em sequência
- Barra de progresso em tempo real
- Logs detalhados do processamento
- Tratamento de erros com retry automático
- Estatísticas de sucesso/falha
- **Download automático em ZIP** de todos os PDFs ao final do processamento

### 3. 📊 Dashboard e Gestão
- **Persistência de dados**: Histórico mantido entre sessões
- Listagem completa de NFS-e emitidas
- Visualização detalhada de cada nota
- Busca e filtros por tomador, CPF, valor
- Estatísticas visuais (métricas, gráficos)
- Exportação de dados

### 4. 📥 Downloads e Exportações
- **Download individual**: XML e PDF de cada nota
- **Download em massa**: 
  - Todos os PDFs em ZIP
  - Todos os XMLs em ZIP
- **Download automático**: PDFs gerados automaticamente após emissão em lote
- Nomes de arquivo organizados com timestamp

### 5. 🔐 Segurança e Certificação
- Assinatura digital com certificado A1
- Validação automática de certificados
- Suporte a mTLS (Mutual TLS)
- Gestão de validade de certificados
- Logs de segurança

### 6. 📄 Geração de DANFSE
- Layout profissional com todas as informações fiscais
- **QR Code integrado** para consulta online
- Campos personalizados (hash do paciente)
- Formato PDF de alta qualidade
- Compatível com impressão e envio digital

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10+**
- **Streamlit 1.30.0** - Framework web para dashboard
- **aiohttp** - Cliente HTTP assíncrono
- **lxml** - Processamento de XML
- **cryptography 41.0.7** - Assinatura digital

### Geração de Documentos
- **ReportLab 4.0.7** - Geração de PDFs (DANFSE)
- **qrcode[pil] 7.4.2** - Geração de QR Codes

### Extração de Dados
- **PyPDF2 / pdfplumber** - Extração de dados de PDFs

### Persistência
- **JSON** - Armazenamento local do histórico
- **SQLite** (opcional) - Banco de dados

### Outros
- **pandas** - Manipulação de dados tabulares
- **asyncio** - Processamento assíncrono

---

## 📁 Estrutura do Projeto

```
leitor-pdf-geracao-notas/
├── app_nfse_enhanced.py          # Dashboard principal (Streamlit)
├── emitir_nfse_completo.py       # Lógica de emissão de NFS-e
├── gerar_danfse_v2.py            # Geração de DANFSE com QR Code
├── analisar_pdf.py               # Extração de dados de PDFs
├── requirements.txt              # Dependências Python
├── nfse_emitidas.json           # Persistência de histórico (gerado automaticamente)
│
├── config/
│   ├── settings.py              # Configurações do sistema
│   └── database.py              # Conexão com banco de dados
│
├── src/
│   ├── api/
│   │   └── nfse_service.py      # Cliente API SEFIN
│   ├── auth/
│   │   └── authentication.py    # Autenticação e tokens
│   ├── models/
│   │   └── schemas.py           # Modelos de dados
│   ├── pdf/
│   │   └── extractor.py         # Extrator de PDFs
│   ├── utils/
│   │   ├── certificate.py       # Gerenciador de certificados
│   │   └── logger.py            # Sistema de logs
│   └── database/
│       └── repository.py        # Repositório de dados
│
├── certs/
│   ├── cert.pem                 # Certificado A1
│   └── key.pem                  # Chave privada
│
├── outputs/
│   ├── xml/                     # XMLs assinados gerados
│   └── pdf/                     # DANFSEs gerados
│
└── docs/
    ├── INICIO_RAPIDO.md         # Guia de início rápido
    ├── GUIA_EMISSAO_NFSE.md    # Guia completo de emissão
    └── CERTIFICATE_SETUP.md     # Configuração de certificados
```

---

## 🚀 Como Usar

### Instalação

```bash
# 1. Clonar repositório
git clone <repositorio>
cd leitor-pdf-geracao-notas

# 2. Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar certificado A1
# Colocar cert.pem e key.pem na pasta certs/
```

### Execução

```bash
streamlit run app_nfse_enhanced.py
```

O sistema abrirá automaticamente no navegador em `http://localhost:8501`

---

## 💼 Fluxos de Uso

### Fluxo 1: Emissão Individual

1. Acesse **"Emitir NFS-e"** no menu lateral
2. Preencha os dados do tomador (CPF/CNPJ, nome, contatos)
3. Configure o serviço (valor, descrição, item de lista)
4. Clique em **"Emitir NFS-e"**
5. Aguarde o processamento (assinatura + envio à SEFIN)
6. **Baixe** XML e PDF diretamente na tela de sucesso
7. A nota é salva automaticamente no histórico

### Fluxo 2: Emissão em Lote

1. Acesse **"Emissão em Lote"** no menu lateral
2. Faça **upload do PDF** com os registros dos clientes
3. Visualize os dados extraídos automaticamente
4. Configure o serviço (valor padrão aplicado a todos)
5. Defina o limite de notas a processar
6. Clique em **"Iniciar Emissão em Lote"**
7. Acompanhe o progresso em tempo real
8. **Download automático** aparece ao final com ZIP contendo todos os PDFs
9. Visualize estatísticas e detalhamento de sucessos/falhas

### Fluxo 3: Gestão do Histórico

1. Acesse **"NFS-e Emitidas"** no menu lateral
2. Visualize todas as notas emitidas (com persistência entre sessões)
3. Use busca para filtrar por tomador ou CPF
4. Veja detalhes completos de cada nota
5. **Baixe arquivos individuais** (XML ou PDF)
6. **Download em massa**:
   - Botão "Baixar Todos os PDFs (ZIP)"
   - Botão "Baixar Todos os XMLs (ZIP)"
7. **Limpe histórico** com confirmação em duas etapas

---

## 📊 Recursos do Dashboard

### Página: Início
- **Métricas principais**: Total de notas, valor total, ISS total
- **Gráficos**:
  - Distribuição temporal de emissões
  - Top 10 tomadores por valor
  - Análise de faturamento mensal
- **Últimas NFS-e emitidas** com acesso rápido

### Página: Emitir NFS-e
- Formulário completo e validado
- Campos obrigatórios marcados com *
- Cálculo automático de valores
- Feedback visual de sucesso/erro
- Downloads disponíveis imediatamente

### Página: Emissão em Lote
- Upload de PDF com preview
- Extração automática de dados
- Estatísticas antes e depois
- Barra de progresso
- Logs em tempo real
- Download automático ao final

### Página: NFS-e Emitidas
- **Lista completa** com paginação
- **Busca/Filtros** por múltiplos critérios
- **Detalhes expandíveis** de cada nota
- **Ações em massa**:
  - Download de todos os PDFs
  - Download de todos os XMLs
  - Limpeza de histórico (com confirmação)
- **Estatísticas** visuais do histórico

### Página: Configurações
- Informações do certificado
- Status de conexão com SEFIN
- Logs do sistema
- Limpeza de cache

---

## 🔒 Segurança e Conformidade

### Assinatura Digital
- Certificado A1 (PFX/P12) convertido para PEM
- Assinatura XML conforme padrão NFSe Nacional
- Validação de certificado antes de cada emissão

### API SEFIN
- Autenticação por token JWT
- Comunicação via HTTPS
- Suporte a mTLS quando necessário
- Retry automático em caso de falha

### Dados Sensíveis
- **nfse_emitidas.json** incluído no .gitignore
- Certificados não versionados
- Logs de erro sem dados sensíveis

---

## 📈 Diferenciais Técnicos

### 1. **Persistência Inteligente**
- Histórico salvo automaticamente em JSON
- Carregamento automático ao iniciar
- Backup incremental após cada emissão

### 2. **Download Automático**
- ZIP gerado automaticamente após emissão em lote
- Botão de download aparece sem necessidade de navegação
- Nomes de arquivo com timestamp para organização

### 3. **Extração de PDF Avançada**
- Reconhecimento automático de campos
- Suporte a múltiplos formatos de PDF
- Validação de dados extraídos

### 4. **QR Code no DANFSE**
- Link direto para consulta online da nota
- Gerado automaticamente com a chave de acesso
- Posicionamento otimizado no layout

### 5. **Processamento Assíncrono**
- Emissões em lote sem bloqueio de UI
- Retry automático em caso de erro temporário
- Logs em tempo real

### 6. **UX Aprimorada**
- Confirmação em duas etapas para ações destrutivas
- Feedback visual claro (cores, ícones)
- Mensagens de erro descritivas
- Tutorial integrado

---

## 🐛 Tratamento de Erros

### Erros Comuns e Soluções

| Erro | Causa | Solução Implementada |
|------|-------|---------------------|
| Certificado inválido | Expirado ou formato incorreto | Validação prévia + mensagem clara |
| Falha na API SEFIN | Timeout ou indisponibilidade | Retry automático (3 tentativas) |
| PDF não processável | Formato incompatível | Validação e mensagem de erro |
| st.download_button em form | Restrição do Streamlit | Botões movidos para fora do formulário |
| Dados não persistem | Erro ao salvar JSON | Try/catch com fallback |

---

## 📝 Logs e Auditoria

### Sistema de Logs
- **app_logger**: Logs da aplicação
- **Níveis**: INFO, WARNING, ERROR
- **Localização**: Console + arquivo (opcional)

### Rastreabilidade
- Cada emissão gera log com timestamp
- Erros salvos com stack trace completo
- Histórico de ações do usuário

---

## 🎨 Identidade Visual

### Cores e Ícones
- 🟢 Verde: Sucesso, confirmações
- 🔵 Azul: Informações, ações principais
- 🟡 Amarelo: Avisos, atenção
- 🔴 Vermelho: Erros, ações destrutivas

### Emojis Consistentes
- 📝 Emissão
- 📋 Lote
- 📊 Estatísticas
- 📥 Download
- 🔒 Segurança
- ⚙️ Configurações

---

## 📦 Entregáveis

### Arquivos de Código
- ✅ `app_nfse_enhanced.py` - Dashboard completo
- ✅ `emitir_nfse_completo.py` - Lógica de emissão
- ✅ `gerar_danfse_v2.py` - Geração de DANFSE com QR Code
- ✅ `analisar_pdf.py` - Extrator de PDFs
- ✅ Módulos em `src/` - Arquitetura organizada

### Documentação
- ✅ `DOCUMENTACAO_ENTREGA.md` - Este documento
- ✅ `README.md` - Visão geral do projeto
- ✅ `INICIO_RAPIDO.md` - Guia de início rápido
- ✅ `GUIA_EMISSAO_NFSE.md` - Manual de emissão
- ✅ `CERTIFICATE_SETUP.md` - Configuração de certificados

### Configuração
- ✅ `requirements.txt` - Dependências Python
- ✅ `.gitignore` - Arquivos não versionados
- ✅ Estrutura de pastas organizada

---

## 🎓 Conhecimentos Necessários

### Para Uso
- Básico de navegação web
- Entendimento de NFS-e e emissão fiscal
- Acesso ao certificado digital A1

### Para Manutenção
- Python intermediário
- Streamlit básico
- Git/GitHub
- APIs REST
- XML e assinatura digital

---

## 🚦 Status do Projeto

### Funcionalidades Implementadas ✅
- [x] Emissão individual de NFS-e
- [x] Emissão em lote com extração de PDF
- [x] Geração de DANFSE com QR Code
- [x] Persistência de histórico (JSON)
- [x] Dashboard com estatísticas
- [x] Download individual de XML/PDF
- [x] Download em massa (ZIP)
- [x] Download automático após lote
- [x] Limpeza de histórico com confirmação
- [x] Sistema de logs
- [x] Tratamento de erros

### Melhorias Futuras 🔮
- [ ] Banco de dados relacional (PostgreSQL/MySQL)
- [ ] API REST para integração externa
- [ ] Consulta de NFS-e emitidas na SEFIN
- [ ] Cancelamento de NFS-e
- [ ] Relatórios contábeis
- [ ] Envio automático de e-mail com PDF
- [ ] Integração com WhatsApp
- [ ] Multi-tenant (múltiplas empresas)

---

## 📞 Suporte e Contato

### Documentação Adicional
- `GUIA_EMISSAO_NFSE.md` - Instruções detalhadas de emissão
- `INICIO_RAPIDO.md` - Primeiros passos
- `STATUS_PROJETO.md` - Histórico de desenvolvimento

### Logs de Erro
- Verificar terminal onde o Streamlit está rodando
- Arquivo de log (se configurado)
- Sessão do navegador (F12 > Console)

---

## 📄 Licença

Este projeto está sob a licença especificada no arquivo `LICENSE`.

---

## 🙏 Agradecimentos

Desenvolvido para automatizar e simplificar o processo de emissão de NFS-e no padrão nacional brasileiro, garantindo conformidade fiscal e agilidade operacional.

---

**Versão da Documentação:** 2.0  
**Data de Última Atualização:** 14 de Janeiro de 2026  
**Versão do Sistema:** 2.0.0

---

## 📋 Checklist de Entrega

- [x] Sistema funcional e testado
- [x] Emissão individual operacional
- [x] Emissão em lote operacional
- [x] Download automático implementado
- [x] Persistência de dados funcionando
- [x] QR Code no DANFSE
- [x] Documentação completa
- [x] Código versionado (Git)
- [x] Dependências listadas
- [x] Tratamento de erros robusto

**Status:** ✅ **PRONTO PARA PRODUÇÃO**

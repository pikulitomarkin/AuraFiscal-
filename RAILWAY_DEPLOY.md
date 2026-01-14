# NFS-e Automation System - Deploy Railway

## 🚀 Deploy no Railway

### Pré-requisitos
1. Conta no [Railway](https://railway.app)
2. CLI do Railway instalado (opcional)
3. Certificado digital A1 convertido para PEM

### Passo 1: Converter Certificado para Base64

```powershell
# No Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("certificados/cert.pem")) | Out-File cert_b64.txt -NoNewline
[Convert]::ToBase64String([IO.File]::ReadAllBytes("certificados/key.pem")) | Out-File key_b64.txt -NoNewline
```

### Passo 2: Criar Projeto no Railway

1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Conecte seu repositório

### Passo 3: Configurar Variáveis de Ambiente

No painel do Railway, vá em **Variables** e adicione:

```
# Aplicação
APP_NAME=NFS-e Automation System
DEBUG=False
SECRET_KEY=sua-chave-secreta-muito-forte

# API NFS-e (Produção)
NFSE_API_BASE_URL=https://sefin.nfse.gov.br
ADN_RECEPCAO_LOTE_ENDPOINT=/SefinNacional/nfse
NFSE_API_AMBIENTE=PRODUCAO
NFSE_API_TIMEOUT=30

# Certificado Digital (Base64)
CERTIFICATE_CERT_PEM=<conteudo_do_cert_b64.txt>
CERTIFICATE_KEY_PEM=<conteudo_do_key_b64.txt>
CERTIFICATE_PATH=certificados/cert.pem
CERTIFICATE_PASSWORD=sua_senha

# Banco de Dados (Railway cria automaticamente se adicionar PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Volume Persistente (se configurado)
RAILWAY_VOLUME_MOUNT_PATH=/app/data
```

### Passo 4: Configurar Volume Persistente

⚠️ **IMPORTANTE**: Para manter o histórico de NFS-e entre deploys:

1. No painel do Railway, clique em **Settings**
2. Vá para a seção **Volumes**
3. Clique em **+ New Volume**
4. Configure:
   - **Mount Path**: `/app/data`
   - **Name**: `nfse-data`
5. Salve as alterações

Isso garantirá que o arquivo `nfse_emitidas.json` seja preservado mesmo após redeploy.

### Passo 5: Adicionar PostgreSQL (Opcional)

1. No projeto Railway, clique em "New"
2. Selecione "Database" > "PostgreSQL"
3. A variável `DATABASE_URL` será configurada automaticamente

### Passo 6: Deploy

O Railway fará deploy automático a cada push no repositório.

Para deploy manual via CLI:
```bash
railway up
```

### 📁 Arquivos de Configuração

| Arquivo | Descrição |
|---------|-----------|
| `Procfile` | Comando de inicialização |
| `railway.json` | Configurações do Railway |
| `nixpacks.toml` | Configuração do build |
| `.streamlit/config.toml` | Configurações do Streamlit |
| `railway_init.py` | Script de inicialização |

### 🔐 Segurança

- **NUNCA** commite arquivos `.pem` ou `.pfx` no repositório
- Use variáveis de ambiente para dados sensíveis
- O `.gitignore` já está configurado para ignorar certificados

### 🔍 Logs

Acompanhe os logs no painel do Railway:
- Build logs: durante o deploy
- Deploy logs: aplicação rodando

### ⚠️ Troubleshooting

**Erro de certificado:**
- Verifique se CERTIFICATE_CERT_PEM e CERTIFICATE_KEY_PEM estão em Base64 válido
- Confirme que não há quebras de linha no Base64

**Porta em uso:**
- Railway define a porta automaticamente via $PORT
- Não defina porta fixa no código

**Histórico de notas sumindo:**
- Configure um volume persistente em Settings > Volumes
- Mount Path: `/app/data`
- Sem volume, os dados são perdidos a cada deploy

**Timeout:**
- Aumente `healthcheckTimeout` se necessário
- Primeira requisição pode demorar (cold start)

### 📞 Suporte

Em caso de dúvidas sobre o Sistema Nacional NFS-e:
- [Portal NFS-e](https://www.gov.br/nfse)
- [Documentação API](https://www.gov.br/nfse/pt-br/assuntos/documentacao-tecnica)

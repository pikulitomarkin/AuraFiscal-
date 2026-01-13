# ⚡ Referência Rápida - Comandos e Atalhos

## 🚀 Inicialização Rápida

```powershell
# Setup inicial (primeira vez)
.\setup.ps1

# Configurar .env
notepad .env

# Inicializar banco de dados
python setup.py

# Rodar aplicação
streamlit run app.py
```

---

## 📝 Comandos Essenciais

### Ambiente Virtual

```powershell
# Criar
python -m venv venv

# Ativar
.\venv\Scripts\Activate.ps1

# Desativar
deactivate

# Instalar dependências
pip install -r requirements.txt

# Atualizar dependências
pip install -r requirements.txt --upgrade
```

### Aplicação

```powershell
# Rodar Streamlit
streamlit run app.py

# Rodar em porta específica
streamlit run app.py --server.port 8080

# Rodar sem abrir navegador
streamlit run app.py --server.headless true

# Limpar cache Streamlit
streamlit cache clear
```

### Testes

```powershell
# Rodar todos os testes
pytest tests/ -v

# Rodar com coverage
pytest tests/ --cov=src --cov-report=html

# Rodar teste específico
pytest tests/test_extractor.py -v

# Rodar testes assíncronos
pytest tests/test_nfse_service.py -v
```

### Banco de Dados

```powershell
# Conectar ao PostgreSQL
psql -U nfse_user -d nfse_db

# Backup
pg_dump -U nfse_user -d nfse_db -F c -f backup_$(Get-Date -Format 'yyyyMMdd').dump

# Restore
pg_restore -U nfse_user -d nfse_db -v backup_20260111.dump

# Queries úteis
psql -U nfse_user -d nfse_db -c "SELECT COUNT(*) FROM nfse_emissoes;"
psql -U nfse_user -d nfse_db -c "SELECT * FROM v_estatisticas_diarias LIMIT 10;"
```

---

## 🐛 Debug e Logs

### Visualizar Logs

```powershell
# Últimas 50 linhas
Get-Content logs\nfse_automation.log -Tail 50

# Seguir logs em tempo real
Get-Content logs\nfse_automation.log -Wait -Tail 10

# Buscar erros
Select-String -Path logs\nfse_automation.log -Pattern "ERROR"

# Últimas 100 linhas com erro
Get-Content logs\nfse_automation.log -Tail 100 | Select-String "ERROR"
```

### Python Debug

```python
# Adicionar breakpoint
import pdb; pdb.set_trace()

# Imprimir variável com contexto
from src.utils.logger import app_logger
app_logger.debug(f"Variável X: {x}")

# Verificar tipo
print(f"Tipo: {type(variavel)}")
```

---

## 🔐 Certificado Digital

### Verificar Certificado

```powershell
# Via Python
python -c "from src.utils.certificate import certificate_manager; print(certificate_manager.get_certificate_info())"

# Verificar validade
python -c "from src.utils.certificate import certificate_manager; print('Válido' if certificate_manager.is_valid() else 'Inválido')"

# Ver data de expiração
python -c "from src.utils.certificate import certificate_manager; print(certificate_manager.get_expiration_date())"
```

### Converter Certificado (se necessário)

```powershell
# PFX para PEM
openssl pkcs12 -in certificado.pfx -out certificado.pem -nodes

# Extrair apenas certificado
openssl pkcs12 -in certificado.pfx -clcerts -nokeys -out cert.pem

# Extrair apenas chave privada
openssl pkcs12 -in certificado.pfx -nocerts -nodes -out key.pem
```

---

## 🔧 Utilitários Python

### Gerar Hash de Senha

```powershell
python -c "import bcrypt; senha = input('Senha: ').encode(); print(bcrypt.hashpw(senha, bcrypt.gensalt()).decode())"
```

### Validar CPF

```powershell
python -c "from src.utils.validators import validator; print(validator.validate_cpf(input('CPF: ')))"
```

### Testar Conexão com API

```python
# Criar arquivo test_api.py
from src.api.nfse_service import get_nfse_service
import asyncio

async def test():
    service = get_nfse_service()
    disponivel = await service.consultar_status_api()
    print(f"API Disponível: {disponivel}")

asyncio.run(test())
```

```powershell
# Executar
python test_api.py
```

---

## 📊 Queries SQL Úteis

### Estatísticas

```sql
-- Total de emissões
SELECT COUNT(*) FROM nfse_emissoes;

-- Emissões de hoje
SELECT COUNT(*) FROM nfse_emissoes WHERE DATE(created_at) = CURRENT_DATE;

-- Taxa de sucesso últimos 7 dias
SELECT 
    DATE(created_at) as data,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'sucesso') as sucessos,
    ROUND(COUNT(*) FILTER (WHERE status = 'sucesso')::NUMERIC / COUNT(*) * 100, 2) as taxa
FROM nfse_emissoes
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- Top 10 erros
SELECT mensagem, COUNT(*) as qtd
FROM nfse_emissoes
WHERE status = 'erro'
GROUP BY mensagem
ORDER BY qtd DESC
LIMIT 10;
```

### Consultas

```sql
-- Buscar por CPF
SELECT * FROM nfse_emissoes WHERE cpf_tomador = '12345678900' ORDER BY created_at DESC LIMIT 10;

-- Buscar por Hash
SELECT * FROM nfse_emissoes WHERE hash_transacao = 'abc123' LIMIT 1;

-- Buscar por Protocolo
SELECT * FROM nfse_emissoes WHERE protocolo = 'PROT2023...' LIMIT 1;

-- Logs de processamento
SELECT * FROM logs_processamento ORDER BY inicio_processamento DESC LIMIT 20;
```

### Manutenção

```sql
-- Limpar registros antigos (mais de 1 ano)
DELETE FROM nfse_emissoes WHERE created_at < CURRENT_DATE - INTERVAL '1 year';

-- Vacuum (otimizar)
VACUUM ANALYZE nfse_emissoes;

-- Reindex
REINDEX TABLE nfse_emissoes;

-- Ver tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🌐 URLs Importantes

```
Aplicação Local:
http://localhost:8501

Documentação API NFS-e (exemplo):
https://api.nfse.gov.br/v1/docs

PostgreSQL Admin (pgAdmin):
http://localhost:5050
```

---

## 🔑 Variáveis de Ambiente Essenciais

```env
# Mínimo necessário no .env

DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/nfse_db"
SECRET_KEY="chave-secreta-aleatoria"
CERTIFICATE_PATH="./certs/certificado.pfx"
CERTIFICATE_PASSWORD="senha_cert"
ADMIN_PASSWORD_HASH="$2b$12$hash_bcrypt"
NFSE_API_BASE_URL="https://api.nfse.gov.br/v1"
```

---

## 📦 Estrutura de Diretórios Mínima

```
projeto/
├── .env                  # Configurações
├── app.py               # Aplicação
├── requirements.txt     # Dependências
├── config/              # Configs
├── src/                 # Código fonte
├── logs/                # Logs (criado auto)
└── certs/               # Certificados
```

---

## 🚨 Troubleshooting Rápido

### Erro: ModuleNotFoundError

```powershell
# Verificar ambiente ativo
Get-Command python | Select-Object Source

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: Banco de Dados

```powershell
# Verificar se PostgreSQL está rodando
Get-Service postgresql*

# Testar conexão
psql -U postgres -c "SELECT version();"

# Recriar banco
python setup.py
```

### Erro: Certificado

```powershell
# Verificar arquivo existe
Test-Path .\certs\certificado.pfx

# Verificar senha no .env
notepad .env
```

### Erro: API Timeout

```env
# Aumentar timeout no .env
NFSE_API_TIMEOUT=60
```

---

## 📱 Atalhos de Teclado (Streamlit)

- `R` - Rerun app
- `C` - Clear cache
- `Ctrl+C` (terminal) - Parar servidor

---

## 🎯 Checklist Pré-Deployment

- [ ] Configurar .env com credenciais de produção
- [ ] Alterar SECRET_KEY para valor único e forte
- [ ] Verificar validade do certificado (> 30 dias)
- [ ] Backup do banco de dados configurado
- [ ] Logs com rotação configurada
- [ ] HTTPS configurado no servidor
- [ ] Firewall configurado (liberar apenas portas necessárias)
- [ ] Monitoramento configurado
- [ ] Teste de carga realizado
- [ ] Documentação atualizada

---

## 💡 Dicas Úteis

### Performance

```python
# Ajustar concorrência
CONCURRENT_REQUESTS=20  # Mais rápido, mas stressará mais a API

# Batch size menor para feedback mais frequente
batch_size = 50
```

### Segurança

```powershell
# Gerar SECRET_KEY forte
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Verificar permissões de arquivo
icacls .env
```

### Manutenção

```powershell
# Limpar cache Python
py -3 -m pip cache purge

# Atualizar pip
python -m pip install --upgrade pip

# Ver versão de pacotes
pip list

# Ver pacotes desatualizados
pip list --outdated
```

---

## 📞 Comandos de Emergência

### Parar Tudo

```powershell
# Parar Streamlit
Ctrl+C

# Matar processo Python
taskkill /F /IM python.exe
```

### Backup Rápido

```powershell
# Banco
pg_dump -U nfse_user -d nfse_db -F c -f emergency_backup.dump

# Arquivos
Compress-Archive -Path .\* -DestinationPath backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip
```

### Rollback

```powershell
# Restaurar backup
pg_restore -U nfse_user -d nfse_db -c -v emergency_backup.dump

# Reverter código
git reset --hard HEAD~1
```

---

**Última Atualização**: 11/01/2026  
**Versão**: 1.0

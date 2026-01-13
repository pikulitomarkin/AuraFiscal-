# 🚀 Guia de Instalação Rápida

## Pré-requisitos

- **Python 3.11+** instalado
- **PostgreSQL** rodando localmente ou remotamente
- **Certificado Digital A1** (arquivo .pfx)
- **Windows** (para este guia - adapte para Linux/Mac)

## Instalação em 5 Passos

### 1️⃣ Clone ou Baixe o Projeto

```powershell
cd "d:\leitor pdf e geração de notas"
```

### 2️⃣ Execute o Script de Setup Automático

```powershell
# Dá permissão para executar scripts (primeira vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Executa o setup
.\setup.ps1
```

O script irá:
- ✅ Verificar Python
- ✅ Criar ambiente virtual (venv)
- ✅ Instalar todas as dependências
- ✅ Copiar .env.example para .env
- ✅ Criar diretórios necessários
- ✅ Gerar hash da senha do admin

### 3️⃣ Configure o Arquivo `.env`

Abra o arquivo `.env` e configure:

```env
# Banco de Dados PostgreSQL
DATABASE_URL="postgresql+asyncpg://usuario:senha@localhost:5432/nfse_db"

# Chave secreta (gere uma aleatória)
SECRET_KEY="sua-chave-secreta-aqui-mude-em-producao"

# Certificado Digital A1
CERTIFICATE_PATH="./certs/seu_certificado.pfx"
CERTIFICATE_PASSWORD="senha_do_certificado"

# Senha Admin (gerada pelo setup.ps1)
ADMIN_PASSWORD_HASH="$2b$12$hash_gerado_pelo_script"
```

### 4️⃣ Coloque o Certificado

Copie seu certificado digital A1 (.pfx) para a pasta `certs/`:

```powershell
# Exemplo
Copy-Item "C:\caminho\seu_certificado.pfx" ".\certs\"
```

### 5️⃣ Inicialize o Banco de Dados

```powershell
# Ative o ambiente virtual
.\venv\Scripts\Activate.ps1

# Execute o script de inicialização
python setup.py
```

Você verá:
```
✅ Banco de dados inicializado com sucesso!
✅ Certificado válido: Sua Empresa LTDA
```

## 🎉 Executar a Aplicação

```powershell
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

**Credenciais de Login:**
- **Usuário:** `admin`
- **Senha:** A que você definiu no setup.ps1

## 🔧 Comandos Úteis

### Atualizar Dependências
```powershell
pip install -r requirements.txt --upgrade
```

### Executar Testes
```powershell
pytest tests/ -v
```

### Ver Logs
```powershell
Get-Content logs\nfse_automation.log -Tail 50 -Wait
```

### Acessar PostgreSQL
```powershell
psql -U usuario -d nfse_db
```

### Gerar Nova Senha Hash
```powershell
python -c "import bcrypt; print(bcrypt.hashpw(b'senha123', bcrypt.gensalt()).decode())"
```

## 📊 Estrutura do Banco de Dados

O sistema criará automaticamente 3 tabelas:

- **nfse_emissoes**: Registro de todas as NFS-e emitidas
- **logs_processamento**: Logs de processamento em lote
- **usuarios**: Usuários do sistema (futuro)

## 🐛 Troubleshooting

### Erro: Certificado Inválido
```
⚠️ Certificado não configurado ou inválido
```
**Solução:** Verifique o caminho e senha do certificado no `.env`

### Erro: Banco de Dados
```
❌ Erro ao conectar ao banco de dados
```
**Solução:** 
1. Verifique se PostgreSQL está rodando
2. Crie o banco: `CREATE DATABASE nfse_db;`
3. Confira `DATABASE_URL` no `.env`

### Erro: Dependência Faltando
```
ModuleNotFoundError: No module named 'pdfplumber'
```
**Solução:** Reinstale dependências
```powershell
pip install -r requirements.txt
```

### API Offline
```
❌ API Nacional NFS-e está OFFLINE
```
**Solução:** Verifique `NFSE_API_BASE_URL` no `.env`. Em desenvolvimento, pode estar apontando para mock/sandbox.

## 📖 Documentação Adicional

- [Arquitetura do Sistema](docs/architecture.md)
- [Exemplo de Payload API](docs/api_payload_example.json)
- [README Principal](README.md)

## 🔐 Segurança em Produção

### ⚠️ IMPORTANTE - Antes de Deploy

1. **Altere SECRET_KEY:** Gere uma chave forte e única
2. **Use HTTPS:** Configure SSL/TLS no servidor
3. **Proteja o .env:** Nunca commite para Git
4. **Certificado Seguro:** Armazene em HSM ou vault
5. **Backups:** Configure backup automático do PostgreSQL
6. **Firewall:** Restrinja acesso ao banco de dados
7. **Monitoramento:** Configure alertas de erros

## 📞 Suporte

Em caso de dúvidas:
1. Verifique os logs em `logs/nfse_automation.log`
2. Execute os testes: `pytest tests/ -v`
3. Consulte a documentação oficial da API NFS-e

---

**Versão:** 1.0.0  
**Última Atualização:** Janeiro 2026

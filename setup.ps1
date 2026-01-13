# Script PowerShell para Configuração Inicial do Projeto
# Execute com: .\setup.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup - Sistema de Automação NFS-e  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python não encontrado! Instale Python 3.11+" -ForegroundColor Red
    exit 1
}

# 2. Criar ambiente virtual
Write-Host ""
Write-Host "[2/6] Criando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Ambiente virtual já existe" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Ambiente virtual criado" -ForegroundColor Green
}

# 3. Ativar ambiente virtual e instalar dependências
Write-Host ""
Write-Host "[3/6] Instalando dependências..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✓ Dependências instaladas" -ForegroundColor Green

# 4. Configurar .env
Write-Host ""
Write-Host "[4/6] Configurando variáveis de ambiente..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ Arquivo .env já existe" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Arquivo .env criado (configure as variáveis)" -ForegroundColor Green
}

# 5. Criar diretórios
Write-Host ""
Write-Host "[5/6] Criando diretórios..." -ForegroundColor Yellow
$dirs = @("logs", "certs", "uploads")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
Write-Host "✓ Diretórios criados" -ForegroundColor Green

# 6. Gerar hash de senha para admin
Write-Host ""
Write-Host "[6/6] Gerando hash de senha..." -ForegroundColor Yellow
Write-Host "Digite a senha para o usuário admin:" -ForegroundColor Cyan
$senha = Read-Host -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($senha)
$senhaTexto = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$pythonScript = @"
import bcrypt
senha = '$senhaTexto'
hash_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hash_senha)
"@

$hash = python -c $pythonScript
Write-Host ""
Write-Host "✓ Hash gerado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Adicione esta linha ao arquivo .env:" -ForegroundColor Yellow
Write-Host "ADMIN_PASSWORD_HASH=`"$hash`"" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup concluído!                     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Configure as variáveis no arquivo .env" -ForegroundColor White
Write-Host "2. Coloque seu certificado .pfx na pasta certs/" -ForegroundColor White
Write-Host "3. Execute: python setup.py (inicializa o banco)" -ForegroundColor White
Write-Host "4. Execute: streamlit run app.py" -ForegroundColor White
Write-Host ""

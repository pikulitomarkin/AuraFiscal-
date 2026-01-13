# ✅ Certificado Digital Configurado

## 📁 Localização do Certificado

**Arquivo:** `CertificadoDigitalA12025GabrielSalehServicos1.pfx`  
**Caminho:** `c:\Users\Admin\Downloads\CertificadoDigitalA12025GabrielSalehServicos1.pfx`

---

## ⚙️ Configuração Aplicada

### Arquivo `.env` criado com:

```env
CERTIFICATE_PATH="c:\\Users\\Admin\\Downloads\\CertificadoDigitalA12025GabrielSalehServicos1.pfx"
CERTIFICATE_PASSWORD="SUBSTITUA_PELA_SENHA_REAL_DO_CERTIFICADO"
```

---

## 🔐 Próximos Passos

### 1. **Configurar a Senha do Certificado**

Edite o arquivo `.env` e substitua a senha:

```env
CERTIFICATE_PASSWORD="sua_senha_aqui"
```

### 2. **Testar o Certificado**

Execute o script de teste:

```bash
python -c "from src.utils.certificate import certificate_manager; print(certificate_manager.get_certificate_info())"
```

**Saída esperada:**
```
✅ Certificado válido
   Titular: Gabriel Saleh Serviços
   CNPJ: XXXXXXXXXX
   Válido de: 2025-XX-XX
   Válido até: 2026-XX-XX
```

### 3. **Verificar Validade**

```python
from src.utils.certificate import certificate_manager

if certificate_manager.is_valid():
    print("✅ Certificado OK")
    info = certificate_manager.get_certificate_info()
    print(f"Válido até: {info['not_after']}")
else:
    print("❌ Certificado inválido ou expirado")
```

---

## 🧪 Teste Rápido

Execute o teste de integração:

```bash
python tests/test_api_adn_integration.py
```

Ou teste direto no Python:

```python
import asyncio
from src.api.nfse_service import NFSeService
from config.settings import settings

# Verificar se o caminho está correto
print(f"Certificado: {settings.CERTIFICATE_PATH}")
print(f"Arquivo existe: {Path(settings.CERTIFICATE_PATH).exists()}")

# Testar serviço
async def test():
    service = NFSeService()
    print("✅ Serviço inicializado com certificado")

asyncio.run(test())
```

---

## 📋 Checklist

- [x] Certificado localizado
- [x] Caminho configurado no `.env`
- [ ] **Senha configurada** (⚠️ AÇÃO NECESSÁRIA)
- [ ] Certificado validado
- [ ] Teste de integração executado

---

## ⚠️ Importante

1. **Não commitar o arquivo `.env`** - Ele contém informações sensíveis
2. **Guardar a senha em local seguro** - Use um gerenciador de senhas
3. **Verificar validade** - Certificados A1 têm validade de 1 ano
4. **Backup** - Faça backup do arquivo .pfx em local seguro

---

## 🔧 Troubleshooting

### Erro: "Arquivo não encontrado"
```python
from pathlib import Path
cert_path = r"c:\Users\Admin\Downloads\CertificadoDigitalA12025GabrielSalehServicos1.pfx"
print(f"Existe: {Path(cert_path).exists()}")
```

### Erro: "Senha incorreta"
- Verifique a senha do certificado
- Confirme que a senha foi digitada corretamente (case-sensitive)

### Erro: "Certificado expirado"
- Verifique a data de validade
- Renove o certificado se necessário

---

**Próxima ação:** Edite o arquivo `.env` e configure a senha do certificado na linha 18.

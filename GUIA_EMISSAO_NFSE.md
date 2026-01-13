# 📄 Guia de Emissão de NFS-e com XML + PDF

## ✅ Sistema Completo Funcionando

O sistema está **100% operacional** para emitir NFS-e via **Sefin Nacional** com geração automática de:
- ✅ **XML assinado** digitalmente (Exclusive C14N)
- ✅ **PDF (DANFSE)** - Documento Auxiliar da NFS-e

---

## 🚀 Emissão Completa (Recomendado)

### Uso Simples
```bash
py emitir_nfse_completo.py
```

**Resultado:**
- ✅ NFS-e autorizada pela Sefin Nacional
- ✅ XML salvo: `nfse_[chave].xml`
- ✅ PDF salvo: `nfse_[chave].pdf`

### Personalizar Dados

Edite o arquivo `emitir_nfse_completo.py` na função `exemplo_emissao()`:

```python
# Prestador (seu CNPJ)
prestador = PrestadorServico(
    cnpj="59418245000186",
    razao_social="GABRIEL SALEH SERVICOS MEDICOS LTDA",
    # ... outros campos
)

# Tomador (cliente)
tomador = TomadorServico(
    cpf="10463540948",  # ou cnpj="12345678901234"
    nome="Cliente Teste"
)

# Serviço
servico = Servico(
    descricao="Consulta medica especializada",
    item_lista_servico="04.01.01",  # Código tributação
    valor_servico=89.00,
    aliquota_iss=2.00,
    valor_iss=1.78
)
```

---

## 📋 Visualizar NFS-e Emitida

### Ver Informações Detalhadas
```bash
py visualizar_nfse.py nfse_[chave].xml
```

**Exibe:**
- Chave de Acesso
- Número da NFS-e
- Status (100 = Autorizada)
- Dados do Prestador
- Dados do Tomador
- Valores (Base, ISS, Líquido)
- Descrição do Serviço

---

## 🔍 Consultar NFS-e na API (Opcional)

### Consultar Última Emitida
```bash
py consultar_nfse.py
```

### Consultar por Chave Específica
```bash
py consultar_nfse.py 42054072259418245000186000000000000326017884398537
```

---

## 📄 Gerar PDF de XML Existente

Se você já tem um XML e quer apenas gerar o PDF:

```bash
py gerar_danfse_v2.py nfse_[chave].xml
```

---

## 📁 Arquivos Gerados

Após cada emissão:

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `nfse_[chave].xml` | NFS-e autorizada (XML completo) | ~10 KB |
| `nfse_[chave].pdf` | DANFSE (representação visual) | ~3-5 KB |
| `xml_dps_sem_assinatura.xml` | DPS antes da assinatura | ~1 KB |
| `xml_dps_assinado.xml` | DPS assinado enviado | ~5 KB |

---

## 🔐 Certificado Digital

**Localização:** `certificados/cert.pem` e `certificados/key.pem`

**Validade:** Até 18/02/2026

**CNPJ:** 59418245000186

---

## ⚙️ Configuração de Ambiente

### Produção
Edite `config/settings.py`:
```python
NFSE_API_BASE_URL = "https://sefin.nfse.gov.br"  # Produção
```

### Homologação (Atual)
```python
NFSE_API_BASE_URL = "https://sefin.producaorestrita.nfse.gov.br"
```

---

## 🔢 Numeração de NFS-e

**Importante:** O sistema incrementa automaticamente o número da DPS em `src/utils/xml_generator.py`.

**Formato do número:**
- Série: `00001` (fixo)
- Número: sequencial (1, 2, 3, ...)

**Para produção:** Implemente controle de numeração em banco de dados.

---

## 📊 Exemplo de Emissão

```python
from emitir_nfse_completo import emitir_nfse_com_pdf

# Criar dados
prestador = PrestadorServico(...)
tomador = TomadorServico(...)
servico = Servico(...)

# Emitir
resultado = await emitir_nfse_com_pdf(prestador, tomador, servico)

# Verificar resultado
if resultado['sucesso']:
    print(f"Chave: {resultado['chave_acesso']}")
    print(f"XML: {resultado['xml_path']}")
    print(f"PDF: {resultado['pdf_path']}")
```

---

## 🐛 Solução de Problemas

### Erro E0714 (Assinatura inválida)
✅ **Resolvido!** O sistema usa Exclusive C14N que funciona corretamente.

### Erro E0014 (DPS duplicada)
Incremente o número da DPS em `src/utils/xml_generator.py` (linha 79).

### Erro E0121 (Razão social não deve ser informada)
✅ **Resolvido!** Campo `xNome` do prestador está comentado.

### Erro 403 (Forbidden)
Verifique se os certificados mTLS estão corretos:
- `certificados/cert.pem`
- `certificados/key.pem`

---

## 📦 Dependências

```bash
pip install lxml cryptography httpx reportlab
```

---

## ✅ Status Atual

| Componente | Status |
|------------|--------|
| Geração XML XSD v1.01 | ✅ Funcionando |
| Assinatura Digital (Exclusive C14N) | ✅ Funcionando |
| Comunicação API Sefin | ✅ Funcionando |
| Autenticação mTLS | ✅ Funcionando |
| Geração PDF (DANFSE) | ✅ Funcionando |
| Validação de dados | ✅ Funcionando |

---

## 🎯 Próximos Passos

1. **Emissão em Lote**: Processar múltiplos clientes do PDF
2. **Banco de Dados**: Armazenar NFS-e emitidas
3. **Controle de Numeração**: Sequencial automático
4. **Envio por E-mail**: Enviar PDF para cliente
5. **Ambiente de Produção**: Mudar para produção real

---

## 📞 Suporte

Para dúvidas sobre a API Sefin Nacional:
- Documentação: https://sefin.nfse.gov.br/docs
- Swagger: https://sefin.producaorestrita.nfse.gov.br/swagger

---

**Última Atualização:** 12/01/2026  
**Versão:** 2.0 - Sistema Completo XML + PDF

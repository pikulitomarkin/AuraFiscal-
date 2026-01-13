# 🏗️ Análise Completa da Arquitetura API NFS-e

## 📚 Baseado no Manual Oficial ADN (Março/2025)

---

## 🎯 Descoberta Crítica

### Erro E1242 Explicado
**"Tipo DF-e não tratado pelo Sistema Nacional NFS-e"**

Este erro ocorreu porque estávamos enviando uma **DPS** (Declaração de Prestação de Serviço - documento para ser autorizado) para um endpoint que espera **NFS-e já autorizadas** (documento fiscal pronto).

---

## 🏢 Arquitetura do Sistema Nacional NFS-e

### 1. Sistema Autorizador (Sefin Nacional)
**Função**: EMITIR/AUTORIZAR NFS-e a partir de DPS

- **O que faz**: Recebe DPS, valida, autoriza e gera NFS-e
- **Usado por**: Contribuintes que emitem notas
- **Endpoint presumido**: Não documentado no manual do ADN
- **Possível localização**: 
  - Portal web: https://adn.nfse.gov.br/contribuintes
  - API Contribuintes: https://adn.producaorestrita.nfse.gov.br/contribuintes/docs

### 2. API ADN (Ambiente de Dados Nacional)
**Função**: COMPARTILHAMENTO e DISTRIBUIÇÃO de NFS-e

- **O que faz**: Repositório central de NFS-e já autorizadas
- **Usado por**: Municípios conveniados e sistemas de consulta
- **Endpoint**: POST /adn/DFe (apenas para municípios compartilharem notas)

---

## 📋 APIs Documentadas no Manual

### Para MUNICÍPIOS (não é nosso caso):

#### 1. API DF-e para Municípios
```
POST /DFe/                  - Compartilhar lote de NFS-e já autorizadas
GET  /DFe/{UltimoNSU}      - Distribuir DFe a partir do NSU
GET  /DFe/{NSU}            - Consultar DFe por NSU
```

#### 2. API NFS-e
```
GET /nfse/{chaveAcesso}    - Consultar NFS-e pela chave
```

#### 3. API DPS
```
GET  /dps/{id}             - Recuperar chave NFS-e a partir do ID DPS
HEAD /dps/{id}             - Verificar se NFS-e foi gerada
```

#### 4. API Eventos
```
POST /nfse/{chaveAcesso}/eventos                        - Registrar evento
GET  /nfse/{chaveAcesso}/eventos                        - Listar eventos
GET  /nfse/{chaveAcesso}/eventos/{tipoEvento}           - Eventos por tipo
GET  /nfse/{chaveAcesso}/eventos/{tipoEvento}/{numSeq} - Evento específico
```

#### 5. API DANFSe
```
GET /danfse/{chaveAcesso}  - Gerar PDF da NFS-e
```

---

## 🔍 APIs NÃO Documentadas (mas existem)

### Para CONTRIBUINTES (nosso caso):

O manual menciona:
> "Ambiente de Produção Restrita destinado a realização de testes das API´s do ADN por parte dos municípios conveniados"
> 
> **Link:** https://adn.producaorestrita.nfse.gov.br/**contribuintes**/docs/index.html

Note o path `/contribuintes` - isso indica APIs específicas para contribuintes emitirem notas!

**Endpoints presumidos (não documentados no manual do ADN):**
```
POST /contribuintes/nfse     - Emitir NFS-e a partir de DPS
GET  /contribuintes/nfse/{chaveAcesso} - Consultar NFS-e emitida
POST /contribuintes/nfse/{chaveAcesso}/cancelar - Cancelar NFS-e
```

---

## 🔄 Fluxo Correto de Emissão

### Fluxo que TENTAMOS (ERRADO):
```
1. Contribuinte gera DPS
2. Contribuinte envia DPS → POST /adn/DFe
3. ❌ ERRO E1242 - Endpoint espera NFS-e, não DPS
```

### Fluxo CORRETO (presumido):
```
1. Contribuinte gera DPS assinada digitalmente
2. Contribuinte envia DPS → POST /contribuintes/nfse (ou similar)
3. Sefin Nacional valida e autoriza
4. Sefin Nacional retorna NFS-e autorizada com chave de acesso
5. (Opcional) Sefin Nacional compartilha automaticamente com ADN → POST /DFe
6. (Opcional) Contribuinte ou terceiros consultam no ADN
```

---

## 🎯 Próximas Ações

### 1. Acessar Documentação Swagger da Produção Restrita
**URL**: https://adn.producaorestrita.nfse.gov.br/contribuintes/docs/index.html

**Objetivo**: Descobrir endpoints de EMISSÃO para contribuintes

### 2. Testar no Ambiente de Produção Restrita

**Configurações:**
```bash
# .env
NFSE_API_BASE_URL="https://adn.producaorestrita.nfse.gov.br"
NFSE_API_AMBIENTE="HOMOLOGACAO"
```

**Endpoints para testar:**
- `/contribuintes/nfse` (POST - emissão)
- `/contribuintes/dps` (POST - autorização de DPS)
- Verificar documentação Swagger interativa

### 3. Validar Certificado Digital

Garantir que o certificado A1 está:
- ✅ Válido até 18/02/2026
- ✅ Pertence ao CNPJ 59418245000186
- ✅ Cadastrado no portal ADN
- ✅ Habilitado para emissão em produção

### 4. Verificar Cadastro no Portal

**Portal**: https://adn.nfse.gov.br

Verificar:
- [ ] CNPJ 59418245000186 está cadastrado
- [ ] Município Florianópolis está habilitado
- [ ] Certificado digital está vinculado
- [ ] Perfil de acesso permite emissão

---

## 📊 Comparação: Municípios vs Contribuintes

| Aspecto | Municípios Conveniados | Contribuintes Emissores |
|---------|------------------------|------------------------|
| **Função** | Compartilhar NFS-e autorizadas | Emitir novas NFS-e |
| **Endpoint Base** | /adn/DFe | /contribuintes/* |
| **Documentação** | Manual completo ADN | Não documentado no manual ADN |
| **Enviam** | NFS-e já autorizadas (XML) | DPS (XML assinado) |
| **Recebem** | NSU de recepção | NFS-e autorizada com chave |
| **Exemplo URL** | POST /DFe/ | POST /contribuintes/nfse (?) |

---

## 🚀 Recomendação Final

### PASSO 1: Acessar Swagger Produção Restrita
Abrir navegador com certificado digital instalado:
```
https://adn.producaorestrita.nfse.gov.br/contribuintes/docs/index.html
```

### PASSO 2: Identificar Endpoint Correto
Procurar por:
- "Emissão de NFS-e"
- "Autorização de DPS"
- "Geração de NFS-e"
- Métodos POST relacionados a contribuintes

### PASSO 3: Atualizar Código
Uma vez identificado o endpoint correto:
1. Atualizar `config/settings.py` com URL correta
2. Ajustar `src/api/client.py` para usar endpoint de emissão
3. Testar com cliente do PDF (Luciana Ribeiro Fantini)

### PASSO 4: Validar e Migrar para Produção
1. Testar em produção restrita
2. Validar resposta da API
3. Migrar para produção: https://adn.nfse.gov.br
4. Emitir nota real

---

## 📝 Notas Importantes

1. **O manual fornecido é para MUNICÍPIOS**, não contribuintes
2. **APIs de contribuintes** não estão documentadas no manual do ADN
3. **Portal web** provavelmente usa APIs de contribuintes que precisamos descobrir
4. **Swagger da produção restrita** deve ter toda documentação necessária
5. **Certificado digital** é essencial - deve estar configurado no navegador para acessar Swagger

---

## 🔗 Links Úteis

- **Portal ADN Produção**: https://adn.nfse.gov.br
- **Portal ADN Produção Restrita**: https://adn.producaorestrita.nfse.gov.br
- **Swagger Municípios (Prod Restrita)**: https://adn.producaorestrita.nfse.gov.br/municipios/docs/index.html
- **Swagger Contribuintes (Prod Restrita)**: https://adn.producaorestrita.nfse.gov.br/contribuintes/docs/index.html

---

*Documento criado em: 11/01/2026*  
*Baseado em: Manual ADN v1.0 (Março/2025)*

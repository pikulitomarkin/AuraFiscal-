# 🔍 GUIA: Capturar Endpoint Real do Portal NFS-e

## Passo a Passo para Descobrir o Endpoint Correto

### 1️⃣ Abrir o Portal e DevTools

1. Acesse o portal onde você emite NFS-e manualmente
2. **Antes de fazer login ou emitir**, pressione **F12** para abrir o DevTools
3. Clique na aba **"Network"** (Rede)
4. Certifique-se que está gravando (botão vermelho ● ativo)

### 2️⃣ Limpar e Preparar

1. Clique no ícone 🚫 (Clear) para limpar requisições antigas
2. Marque as opções:
   - ✅ **Preserve log** (preservar log)
   - ✅ **Disable cache** (desabilitar cache)

### 3️⃣ Emitir uma Nota de Teste

1. Preencha o formulário de emissão normalmente
2. Use dados simples para teste (pode ser valor mínimo)
3. **Clique em "Emitir"** ou "Enviar"
4. Aguarde a resposta do sistema

### 4️⃣ Identificar a Requisição

Na lista de requisições (Network), procure por:

**Características da requisição de emissão:**
- **Method**: POST (cor vermelha/rosa geralmente)
- **Type/Content-Type**: `application/json` ou `application/xml`
- **Status**: 200, 201 (sucesso) ou 400/500 (erro)
- **URL**: Deve conter palavras como:
  - `/nfse`
  - `/dps`
  - `/emitir`
  - `/gerar`
  - `/enviar`

### 5️⃣ Inspecionar a Requisição

Clique na requisição identificada e anote:

#### **Headers (Cabeçalhos)**
```
General:
  Request URL: https://xxxxx.nfse.gov.br/xxxxx/nfse
  Request Method: POST
  Status Code: 200 OK

Request Headers:
  Content-Type: application/json
  Authorization: Bearer xxx... (se houver)
```

#### **Payload (Dados Enviados)**
Na aba **"Payload"** ou **"Request"**, copie o JSON ou XML enviado.

**Procure especialmente por:**
- Estrutura do JSON/XML
- Se o XML está comprimido (base64)
- Campos obrigatórios

#### **Response (Resposta)**
Na aba **"Response"**, veja:
- Se retorna XML da NFS-e gerada
- Se retorna JSON com chave de acesso
- Códigos de erro (se houver)

### 6️⃣ Informações Importantes para Coletar

Envie para mim:

1. **URL Completa**: 
   ```
   Exemplo: POST https://adn.nfse.gov.br/contribuintes/emitir
   ```

2. **Content-Type**:
   ```
   Exemplo: application/json
   ```

3. **Estrutura do Payload** (primeiras linhas):
   ```json
   {
     "DPS": "...",
     "formato": "...",
     ...
   }
   ```

4. **Estrutura da Response** (primeiras linhas):
   ```json
   {
     "chaveAcesso": "...",
     "numeroNota": "...",
     ...
   }
   ```

---

## 🎯 Dica Rápida

Se preferir, pode simplesmente:

1. Abrir DevTools (F12)
2. Ir em Network
3. Limpar (🚫)
4. Emitir uma nota
5. **Clicar com botão direito** na requisição POST → **Copy** → **Copy as cURL**
6. Colar aqui o comando cURL completo

Eu posso extrair todas as informações do comando cURL!

---

## ❓ Perguntas para Facilitar

Se não encontrar requisição POST, verifique:

1. O portal usa WebSocket? (procure por `ws://` ou `wss://`)
2. Usa iframe? (conteúdo carregado de outro domínio)
3. Abre popup? (janela nova para emitir)

---

Aguardo suas descobertas! 🔎

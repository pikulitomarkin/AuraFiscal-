# 🚀 INÍCIO RÁPIDO - Dashboard NFS-e

## ⚡ Executar Agora (3 passos)

### 1️⃣ Abra o PowerShell no diretório do projeto

```powershell
cd "d:\leitor pdf e geração de notas"
```

### 2️⃣ Execute o dashboard

```powershell
streamlit run app_nfse_enhanced.py
```

### 3️⃣ Acesse no navegador

**URL:** http://localhost:8501

**Login:** Use as credenciais configuradas (admin/senha padrão)

---

## 📤 Emitir Sua Primeira NFS-e

### Passo 1: Login
- Faça login com suas credenciais

### Passo 2: Menu de Emissão
- Clique em **"📤 Emissão Individual"** no menu lateral

### Passo 3: Preencher Dados do Tomador
```
CPF/CNPJ: 12345678901
Nome: João da Silva
E-mail: joao@email.com (opcional)
Telefone: (51) 99999-9999 (opcional)
```

### Passo 4: Endereço do Tomador (Opcional)
```
CEP: 90000-000
Logradouro: Rua Exemplo
Número: 123
Bairro: Centro
Cidade: Porto Alegre
UF: RS
```

### Passo 5: Dados do Serviço
```
Valor do Serviço: R$ 100,00
Alíquota ISS: 2%
Item Lista: 1.09
Descrição: Prestação de serviços conforme contrato
```

### Passo 6: Emitir
- Clique no botão **"🚀 Emitir NFS-e"**
- Aguarde o processamento (5-10 segundos)
- ✅ Sucesso! Veja a chave de acesso e baixe XML/PDF

---

## 📥 Baixar XML e PDF

### Opção 1: Após Emissão
- Logo após emitir, clique em:
  - **📄 Baixar XML** - Arquivo XML assinado
  - **📑 Baixar PDF** - DANFSE em PDF

### Opção 2: Lista de NFS-e
- Vá em **"📜 NFS-e Emitidas"** no menu
- Encontre a NFS-e desejada
- Expanda o card
- Clique nos botões de download

---

## 🔍 Consultar NFS-e Emitidas

1. Acesse **"📜 NFS-e Emitidas"**
2. Use os filtros:
   - 🔍 Filtrar por Nome
   - 🔍 Filtrar por CPF
3. Ordene:
   - Mais Recentes / Mais Antigas
   - Maior Valor / Menor Valor
4. Expanda para ver detalhes completos

---

## ⚙️ Configurações

Acesse **"⚙️ Configurações"** para ver:

- 🔐 Informações do certificado digital
- 🌐 Configuração da API
- 🗑️ Limpar histórico
- 🔄 Reiniciar sessão

---

## 🆘 Problemas Comuns

### Dashboard não abre
```powershell
# Instale o Streamlit
pip install streamlit

# Execute novamente
streamlit run app_nfse_enhanced.py
```

### Erro de importação
```powershell
# Certifique-se de estar no diretório correto
cd "d:\leitor pdf e geração de notas"

# Verifique se os arquivos existem
ls emitir_nfse_completo.py
ls gerar_danfse_v2.py
```

### Certificado não encontrado
```powershell
# Verifique se os certificados existem
ls certificados\cert.pem
ls certificados\key.pem
```

### Erro na emissão
- Verifique a conexão com a internet
- Confirme que o certificado está válido
- Veja os logs no terminal onde o Streamlit está rodando

---

## 📊 Interface do Dashboard

```
╔═══════════════════════════════════════════════════════════╗
║                  🔐 Sistema de Emissão NFS-e              ║
║                                                           ║
║  ⚙️ Menu Principal          📊 Área de Trabalho          ║
║  ─────────────────          ─────────────────────────    ║
║                                                           ║
║  📊 Dashboard               ┌─────────────────────────┐  ║
║  📤 Emissão Individual      │  [Conteúdo Principal]   │  ║
║  📋 Emissão em Lote         │                         │  ║
║  📜 NFS-e Emitidas          │  • Formulários          │  ║
║  ⚙️ Configurações           │  • Tabelas              │  ║
║                             │  • Métricas             │  ║
║  👤 Usuário: admin          │  • Botões de ação       │  ║
║  🚪 Sair                    │                         │  ║
║                             └─────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📱 Recursos do Dashboard

### 📊 Dashboard Principal
- Total de NFS-e emitidas
- Valor total arrecadado
- Últimas 5 emissões
- Status do sistema

### 📤 Emissão Individual
- Formulário completo
- Validação em tempo real
- Emissão + XML + PDF automático
- Download imediato

### 📜 Lista de NFS-e
- Todas as NFS-e emitidas
- Filtros avançados
- Ordenação flexível
- Download de XML/PDF
- Visualização inline

### ⚙️ Configurações
- Info do certificado
- Config da API
- Ferramentas de manutenção

---

## 🎯 Casos de Uso

### Caso 1: Emissão Única
"Preciso emitir uma NFS-e para um cliente"

1. Menu → Emissão Individual
2. Preencha dados do tomador
3. Configure o serviço
4. Emita e baixe XML/PDF

### Caso 2: Consultar NFS-e Antiga
"Preciso encontrar uma nota emitida ontem"

1. Menu → NFS-e Emitidas
2. Use o filtro por nome ou CPF
3. Ordene por "Mais Recentes"
4. Baixe XML/PDF novamente

### Caso 3: Visualizar XML
"Quero ver o conteúdo do XML"

1. Menu → NFS-e Emitidas
2. Expanda a NFS-e desejada
3. Clique em "👁️ Visualizar XML"
4. Veja o XML formatado

### Caso 4: Limpar Histórico
"Quero limpar todas as NFS-e da sessão"

1. Menu → Configurações
2. Seção "Manutenção"
3. Clique em "🗑️ Limpar Histórico"

---

## 📈 Métricas Exibidas

### No Dashboard
- **NFS-e Emitidas:** Quantidade total
- **Valor Total:** Soma de todos os valores
- **Sistema:** Status operacional
- **Certificado:** Validade

### Na Lista de NFS-e
- **Total de NFS-e:** Após filtros
- **Valor Total:** Soma filtrada
- **Total ISS:** ISS calculado

---

## 🔑 Atalhos Úteis

| Ação | Como Fazer |
|------|------------|
| Emitir NFS-e | Menu → Emissão Individual → Preencher → Emitir |
| Baixar XML | Lista → Expanda NFS-e → Baixar XML |
| Baixar PDF | Lista → Expanda NFS-e → Baixar PDF |
| Ver detalhes | Lista → Expanda NFS-e |
| Filtrar lista | Lista → Campo de filtro no topo |
| Limpar histórico | Configurações → Manutenção → Limpar |

---

## 💡 Dicas

### ✅ Boas Práticas
- Preencha todos os campos obrigatórios
- Confira CPF/CNPJ antes de emitir
- Salve os arquivos XML/PDF em local seguro
- Use descrições claras do serviço

### ⚠️ Atenções
- Cada emissão consome um número sequencial
- Não é possível cancelar pelo dashboard (use API)
- Histórico é limpo ao sair/reiniciar sessão
- Certificado expira em 18/02/2026

### 🚫 Evite
- CPF/CNPJ inválidos
- Valores zerados ou negativos
- Descrições muito genéricas
- Emissões duplicadas

---

## 📞 Suporte

### Documentação Completa
- `GUIA_EMISSAO_NFSE.md` - Guia completo
- `README_DASHBOARD_ENHANCED.md` - Docs do dashboard
- `STATUS_PROJETO.md` - Status do sistema

### Logs e Debug
- Veja o terminal onde o Streamlit está rodando
- Logs ficam em `logs/`
- Mensagens de erro aparecem na interface

### Arquivos Importantes
- `app_nfse_enhanced.py` - Dashboard
- `emitir_nfse_completo.py` - Emissão
- `gerar_danfse_v2.py` - PDF
- `certificados/` - Certificados digitais

---

## 🎉 Pronto!

Agora é só usar! 🚀

```powershell
streamlit run app_nfse_enhanced.py
```

**Boa sorte com suas emissões de NFS-e!** ✨

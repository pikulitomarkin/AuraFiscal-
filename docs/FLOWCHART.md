# 🔄 Fluxograma Completo do Sistema

## 📊 Diagrama de Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                    INÍCIO DO SISTEMA                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  1. AUTENTICAÇÃO                                │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Login Screen │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────┐        ┌──────────────┐                  │
│  │ Valida Username  │───────▶│ Verifica     │                  │
│  │ e Password       │        │ Hash bcrypt  │                  │
│  └──────┬───────────┘        └──────┬───────┘                  │
│         │                           │                           │
│         │                           ▼                           │
│         │                    ┌──────────────┐                  │
│         │                    │ Gera Token   │                  │
│         │                    │ JWT (8h)     │                  │
│         │                    └──────┬───────┘                  │
│         │                           │                           │
│         └───────────────────────────┘                           │
│                         │                                        │
│                         ▼                                        │
│              ┌─────────────────┐                                │
│              │ Session Valid?  │                                │
│              └────┬────────┬───┘                                │
│                   │        │                                     │
│                 YES       NO → Volta ao Login                   │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  2. DASHBOARD PRINCIPAL                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   🏠 Início  │  │ 📤 Emissão   │  │ 📊 Relatórios│         │
│  └──────────────┘  └──────┬───────┘  └──────────────┘         │
│                            │                                     │
│                            │ [Usuário seleciona]                │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  3. UPLOAD DE PDF                               │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Streamlit File       │                                       │
│  │ Uploader             │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐         ┌──────────────────┐         │
│  │ PDF Bytes Recebido   │────────▶│ Verifica Tamanho │         │
│  └──────────────────────┘         │ (< 50 MB)        │         │
│                                    └─────────┬────────┘         │
│                                              │                   │
│                                              ▼                   │
│                                    ┌──────────────────┐         │
│                                    │ Válido?          │         │
│                                    └───┬──────────┬───┘         │
│                                        │          │              │
│                                       YES        NO → Erro      │
└────────────────────────────────────────┼──────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  4. EXTRAÇÃO DE DADOS                           │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ pdfplumber.open()    │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │ Para cada página:    │                                       │
│  │   page.extract_text()│                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ Aplicar Regex Patterns:          │                           │
│  │  • CPF: \d{3}.\d{3}.\d{3}-\d{2}  │                           │
│  │  • Hash: [A-F0-9]{32,64}         │                           │
│  │  • Nome: (?:Nome|Cliente)[:\s]+  │                           │
│  └──────────┬───────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐        ┌──────────────────┐          │
│  │ Registros Extraídos  │───────▶│ Validar CPF      │          │
│  └──────────────────────┘        │ (dígito verif.)  │          │
│                                   └─────────┬────────┘          │
│                                             │                    │
│                                             ▼                    │
│                                   ┌──────────────────┐          │
│                                   │ Filtrar Válidos  │          │
│                                   └─────────┬────────┘          │
└───────────────────────────────────────────────┼──────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  5. PREVIEW E CONFIGURAÇÃO                      │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Exibir Tabela com:   │                                       │
│  │  - Nome              │                                       │
│  │  - CPF               │                                       │
│  │  - Hash              │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐        ┌──────────────────┐          │
│  │ Configurar Serviço:  │        │ • Valor (R$)     │          │
│  │  Form Streamlit      │───────▶│ • Alíquota ISS   │          │
│  └──────────────────────┘        │ • Descrição      │          │
│                                   │ • Item Lista     │          │
│                                   └─────────┬────────┘          │
│                                             │                    │
│                                             ▼                    │
│                                   ┌──────────────────┐          │
│                                   │ Submit Button    │          │
│                                   └─────────┬────────┘          │
└───────────────────────────────────────────────┼──────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  6. PROCESSAMENTO EM LOTE                       │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Criar Log no BD      │                                       │
│  │ (batch_id, timestamp)│                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ Dividir em Batches               │                           │
│  │ (tamanho: CONCURRENT_REQUESTS)   │                           │
│  └──────────┬───────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ Para cada batch:                 │                           │
│  │                                  │                           │
│  │  ┌───────────────────────────┐  │                           │
│  │  │ Criar Tasks Assíncronas   │  │                           │
│  │  │ (asyncio.gather)          │  │                           │
│  │  └────────┬──────────────────┘  │                           │
│  │           │                      │                           │
│  │           ▼                      │                           │
│  │  ┌───────────────────────────┐  │                           │
│  │  │ Para cada registro:       │  │                           │
│  │  │                           │  │                           │
│  │  │  1. Montar Payload        │  │                           │
│  │  │  2. Assinar c/ Cert A1    │  │                           │
│  │  │  3. POST API Gov.br       │  │                           │
│  │  │  4. Parse Response        │  │                           │
│  │  │  5. Salvar Resultado      │  │                           │
│  │  └────────┬──────────────────┘  │                           │
│  │           │                      │                           │
│  │           ▼                      │                           │
│  │  ┌───────────────────────────┐  │                           │
│  │  │ Atualizar Progresso       │  │                           │
│  │  │ (progress_bar)            │  │                           │
│  │  └───────────────────────────┘  │                           │
│  └──────────────────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │ Aguardar Conclusão   │                                       │
│  │ de Todos os Batches  │                                       │
│  └──────────┬───────────┘                                       │
└──────────────┼──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  7. EMISSÃO INDIVIDUAL                          │
│            (Executado para cada registro)                       │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Build NFSeRequest    │                                       │
│  │  • Prestador         │                                       │
│  │  • Tomador (CPF)     │                                       │
│  │  • Serviço (Valor)   │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │ Validar com Pydantic │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐        ┌──────────────────┐          │
│  │ Converter para JSON  │───────▶│ Assinar Payload  │          │
│  └──────────────────────┘        │ (Certificado A1) │          │
│                                   └─────────┬────────┘          │
│                                             │                    │
│                                             ▼                    │
│                                   ┌──────────────────┐          │
│                                   │ httpx.post()     │          │
│                                   │ (timeout: 30s)   │          │
│                                   └─────────┬────────┘          │
│                                             │                    │
│                                   ┌─────────▼────────┐          │
│                                   │ Sucesso?         │          │
│                                   └────┬────────┬────┘          │
│                                        │        │                │
│                                      YES       NO                │
│                                        │        │                │
│                                        │        ▼                │
│                                        │  ┌──────────────┐      │
│                                        │  │ Retry (3x)   │      │
│                                        │  │ Exp Backoff  │      │
│                                        │  └──────┬───────┘      │
│                                        │         │               │
│                                        │    ┌────▼─────┐        │
│                                        │    │ Erro?    │        │
│                                        │    └────┬─────┘        │
│                                        │         │               │
│                                        ▼         ▼               │
│                                   ┌──────────────────┐          │
│                                   │ Log Resultado    │          │
│                                   │  • Hash          │          │
│                                   │  • Status        │          │
│                                   │  • Protocolo     │          │
│                                   │  • Mensagem      │          │
│                                   └─────────┬────────┘          │
└───────────────────────────────────────────────┼──────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  8. PERSISTÊNCIA                                │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Repository.save()    │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ SQLAlchemy INSERT:               │                           │
│  │                                  │                           │
│  │  INSERT INTO nfse_emissoes       │                           │
│  │  (hash, cpf, nome, status,       │                           │
│  │   numero_nfse, protocolo...)     │                           │
│  │  VALUES (...)                    │                           │
│  └──────────┬───────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐        ┌──────────────────┐          │
│  │ Commit Transaction   │───────▶│ Log Operação     │          │
│  └──────────────────────┘        └──────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  9. EXIBIÇÃO DE RESULTADOS                      │
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │ Atualizar Log BD     │                                       │
│  │ (sucessos, erros)    │                                       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ Exibir Métricas:                 │                           │
│  │  • Total Processado              │                           │
│  │  • Sucessos (%)                  │                           │
│  │  • Erros                         │                           │
│  └──────────┬───────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────┐                           │
│  │ Tabela de Resultados:            │                           │
│  │  • Hash | CPF | Nome             │                           │
│  │  • Status | NFS-e | Protocolo    │                           │
│  │  • Mensagem                      │                           │
│  └──────────┬───────────────────────┘                           │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │ Download CSV         │                                       │
│  │ (opcional)           │                                       │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   FIM           │
                    └─────────────────┘
```

---

## 🔀 Fluxo de Tratamento de Erros

```
┌─────────────────────┐
│  Erro Detectado     │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Tipo de Erro?│
    └───┬──────────┘
        │
        ├─────────────────────────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│ Erro de Rede/    │                    │ Erro de Validação│
│ Timeout          │                    │ (CPF, Hash, etc) │
└────┬─────────────┘                    └────┬─────────────┘
     │                                        │
     ▼                                        ▼
┌──────────────────┐              ┌──────────────────────┐
│ Retry Automático │              │ Registrar Erro       │
│ (3x, backoff)    │              │ Continuar p/ Próximo │
└────┬─────────────┘              └──────────────────────┘
     │
     ▼
┌──────────────────┐
│ Sucesso?         │
└───┬──────────┬───┘
    │          │
   YES        NO
    │          │
    │          ▼
    │   ┌──────────────────┐
    │   │ Registrar Erro   │
    │   │ Final            │
    │   └──────────────────┘
    │          │
    └──────────┴───────────▶ Continuar Processamento
```

---

## 📊 Estados do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                  ESTADOS POSSÍVEIS                      │
└─────────────────────────────────────────────────────────┘

1. INICIAL
   └─► Login Screen

2. AUTENTICADO
   └─► Dashboard (Menu Principal)
       ├─► Home
       ├─► Emissão (Upload/Config/Process)
       ├─► Relatórios
       └─► Configurações

3. PROCESSANDO
   └─► Emissão em andamento
       ├─► Progress Bar ativa
       ├─► Status: "Processando X/Y"
       └─► Não permite nova operação

4. CONCLUÍDO
   └─► Resultados exibidos
       ├─► Métricas
       ├─► Tabela de resultados
       └─► Opção de download

5. ERRO
   └─► Mensagem de erro
       ├─► Detalhes do erro
       ├─► Sugestão de correção
       └─► Opção de tentar novamente

6. DESCONECTADO
   └─► Token expirado → Volta ao Login
```

---

## ⚡ Fluxo de Dados Simplificado

```
PDF → Bytes → Texto → Regex → Dados → Validação → Payload → API → Resposta → BD → UI
 ↓      ↓       ↓       ↓       ↓         ↓         ↓      ↓      ↓       ↓     ↓
File Upload  pdfplumber Extract CPF Pydantic JSON  httpx Gov.br SQLAlchemy Streamlit
```

---

## 🔄 Ciclo de Vida de uma NFS-e

```
1. Extração do PDF
   └─► Registro com CPF, Nome, Hash

2. Validação
   └─► CPF válido? Hash presente?

3. Preparação
   └─► Montar payload JSON

4. Assinatura
   └─► Certificado A1 assina payload

5. Envio
   └─► POST para API Nacional

6. Resposta
   └─► Protocolo + Número NFS-e

7. Persistência
   └─► Salvar no PostgreSQL

8. Auditoria
   └─► Log completo da operação
```

---

**Legenda:**
- `┌─┐ └─┘` = Caixas de processo
- `│ ─ ▼` = Setas de fluxo
- `YES/NO` = Decisões
- `[Texto]` = Ações do usuário

---

**Versão**: 1.0  
**Data**: 11/01/2026

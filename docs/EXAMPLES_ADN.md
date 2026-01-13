# 💡 Exemplos Práticos - API ADN

## 1. Geração de XML Simples

```python
from src.utils.xml_generator import NFSeXMLGenerator
from src.models.schemas import NFSeRequest, TomadorServico, Servico, PrestadorServico, TipoAmbiente
from decimal import Decimal

# Inicializar gerador
generator = NFSeXMLGenerator(ambiente=TipoAmbiente.HOMOLOGACAO)

# Dados do prestador
prestador = PrestadorServico(
    cnpj="12345678000190",
    inscricao_municipal="123456",
    razao_social="Minha Empresa LTDA",
    nome_fantasia="Minha Empresa"
)

# Dados do tomador (cliente)
tomador = TomadorServico(
    cpf="12345678901",
    nome="João da Silva",
    email="joao@email.com"
)

# Dados do serviço
servico = Servico(
    discriminacao="Serviço de consultoria técnica",
    codigo_servico_municipal="01.01",
    item_lista_servico="01.01",
    valor_servicos=Decimal("1000.00"),
    aliquota_iss=Decimal("5.00"),
    valor_iss=Decimal("50.00"),
    iss_retido=False
)

# Montar requisição
nfse_request = NFSeRequest(
    prestador=prestador,
    tomador=tomador,
    servico=servico
)

# Gerar XML
xml = generator.gerar_xml_nfse(nfse_request)
print(xml)
```

**Saída:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <Prestador>
    <CNPJ>12345678000190</CNPJ>
    <InscricaoMunicipal>123456</InscricaoMunicipal>
    <RazaoSocial>Minha Empresa LTDA</RazaoSocial>
  </Prestador>
  <Tomador>
    <CPF>12345678901</CPF>
    <Nome>João da Silva</Nome>
  </Tomador>
  <Servico>
    <Discriminacao>Serviço de consultoria técnica</Discriminacao>
    <Valores>
      <ValorServicos>1000.00</ValorServicos>
      <AliquotaISS>5.00</AliquotaISS>
      <ValorISS>50.00</ValorISS>
    </Valores>
  </Servico>
</DPS>
```

---

## 2. Compressão e Codificação

```python
# Usando o XML do exemplo anterior
xml_comprimido = generator.comprimir_e_codificar(xml)

print(f"Tamanho original: {len(xml)} bytes")
print(f"Tamanho comprimido: {len(xml_comprimido)} bytes")
print(f"Taxa de compressão: {(1 - len(xml_comprimido)/len(xml))*100:.1f}%")

print("\nPrimeiros 100 caracteres do Base64:")
print(xml_comprimido[:100])
```

**Saída:**
```
Tamanho original: 1247 bytes
Tamanho comprimido: 487 bytes
Taxa de compressão: 60.9%

Primeiros 100 caracteres do Base64:
H4sIAAAAAAAA/+1cW3PbNhZ+z6/gOJO0nU4lURIlyrKzY0uO3UntOLa8zTTTGYAESKINAlwAlJz99T0ALhIpybZk2e5s...
```

---

## 3. Envio para API ADN

```python
import asyncio
from src.api.client import NFSeAPIClient

async def enviar_lote():
    # Preparar XMLs comprimidos
    lote_xml = generator.gerar_lote_comprimido([nfse_request])
    
    # Inicializar cliente
    client = NFSeAPIClient()
    
    # Enviar para API
    response = await client.recepcionar_lote(lote_xml)
    
    # Processar resposta
    print("Resposta da API ADN:")
    print(f"Ambiente: {response['TipoAmbiente']}")
    print(f"Data/Hora: {response['DataHoraProcessamento']}")
    
    for doc in response['Lote']:
        print(f"\nDocumento:")
        print(f"  Chave de Acesso: {doc['ChaveAcesso']}")
        print(f"  NSU: {doc['NsuRecepcao']}")
        print(f"  Status: {doc['StatusProcessamento']}")
        
        if doc['Erros']:
            print(f"  Erros: {doc['Erros']}")
        if doc['Alertas']:
            print(f"  Alertas: {doc['Alertas']}")

# Executar
asyncio.run(enviar_lote())
```

**Saída esperada:**
```
Resposta da API ADN:
Ambiente: HOMOLOGACAO
Data/Hora: 2026-01-11T10:30:00Z

Documento:
  Chave de Acesso: 12345678901234567890123456789012345678901234567890
  NSU: 000000000001
  Status: PROCESSADO
```

---

## 4. Processamento em Lote (Múltiplos Documentos)

```python
# Lista de registros extraídos do PDF
registros = [
    {"cpf": "12345678901", "nome": "João Silva", "hash": "abc123"},
    {"cpf": "98765432109", "nome": "Maria Santos", "hash": "def456"},
    {"cpf": "11122233344", "nome": "Pedro Oliveira", "hash": "ghi789"},
]

# Configuração do serviço
config_servico = {
    "discriminacao": "Serviço de consultoria",
    "codigo_servico_municipal": "01.01",
    "item_lista_servico": "01.01",
    "valor_servicos": Decimal("500.00"),
    "aliquota_iss": Decimal("5.00"),
}

# Usar o serviço de alto nível
from src.api.nfse_service import NFSeService

async def processar_lote():
    service = NFSeService()
    
    # Callback de progresso
    def on_progress(current, total):
        percent = (current / total) * 100
        print(f"Progresso: {current}/{total} ({percent:.1f}%)")
    
    # Processar
    results = await service.emitir_nfse_lote(
        registros=registros,
        config_servico=config_servico,
        callback_progress=on_progress
    )
    
    # Exibir resultados
    for result in results:
        status_icon = "✅" if result.status == "sucesso" else "❌"
        print(f"{status_icon} {result.nome_tomador} - {result.mensagem}")

asyncio.run(processar_lote())
```

**Saída:**
```
Progresso: 3/3 (100.0%)
✅ João Silva - Autorizado - NSU: 000000000001
✅ Maria Santos - Autorizado - NSU: 000000000002
✅ Pedro Oliveira - Autorizado - NSU: 000000000003
```

---

## 5. Tratamento de Erros

```python
from src.models.schemas import ProblemDetails

async def processar_com_erro():
    try:
        client = NFSeAPIClient()
        response = await client.recepcionar_lote(lote_xml)
        
        # Verificar erros individuais
        for doc in response['Lote']:
            if doc['Erros']:
                print(f"⚠️  Documento com erros:")
                for erro in doc['Erros']:
                    print(f"   Código: {erro['Codigo']}")
                    print(f"   Descrição: {erro['Descricao']}")
                    if erro['Complemento']:
                        print(f"   Complemento: {erro['Complemento']}")
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            # Erro de validação
            error_data = e.response.json()
            print(f"❌ Erro 400 - Bad Request:")
            print(f"   Título: {error_data.get('title')}")
            print(f"   Detalhes: {error_data.get('detail')}")
            print(f"   Erros: {error_data.get('errors')}")
        else:
            print(f"❌ Erro HTTP {e.response.status_code}")
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
```

---

## 6. Decodificar XML (Debug)

```python
# Para debug/inspeção, você pode decodificar um XML comprimido
xml_original = generator.decodificar_e_descomprimir(xml_comprimido)

print("XML recuperado:")
print(xml_original)

# Verificar se é idêntico ao original
assert xml_original == xml, "XMLs diferentes!"
print("✅ XMLs são idênticos!")
```

---

## 7. Integração com Streamlit

```python
import streamlit as st
import asyncio

def render_batch_emission():
    st.title("Emissão de NFS-e em Lote")
    
    # Upload do PDF
    uploaded_file = st.file_uploader("Envie o PDF", type="pdf")
    
    if uploaded_file and st.button("Processar Lote"):
        # Extração de dados
        with st.spinner("Extraindo dados do PDF..."):
            extractor = PDFDataExtractor()
            registros = extractor.extract_from_bytes(uploaded_file.read())
        
        st.success(f"✅ {len(registros)} registros extraídos")
        
        # Configuração do serviço
        st.subheader("Configuração do Serviço")
        discriminacao = st.text_input("Descrição", "Serviço de consultoria")
        valor = st.number_input("Valor (R$)", min_value=0.01, value=100.00)
        
        if st.button("Emitir NFS-e"):
            # Criar barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def on_progress(current, total):
                percent = int((current / total) * 100)
                progress_bar.progress(percent)
                status_text.text(f"Processando: {current}/{total}")
            
            # Processar
            config = {
                "discriminacao": discriminacao,
                "valor_servicos": Decimal(str(valor)),
                "aliquota_iss": Decimal("5.00")
            }
            
            service = NFSeService()
            results = asyncio.run(
                service.emitir_nfse_lote(registros, config, on_progress)
            )
            
            # Exibir resultados
            st.success("✅ Processamento concluído!")
            
            # Tabela de resultados
            df_results = pd.DataFrame([
                {
                    "Nome": r.nome_tomador,
                    "CPF": r.cpf_tomador,
                    "Status": r.status,
                    "Chave de Acesso": r.numero_nfse,
                    "NSU": r.protocolo,
                    "Mensagem": r.mensagem
                }
                for r in results
            ])
            
            st.dataframe(df_results)
            
            # Estatísticas
            sucessos = sum(1 for r in results if r.status == "sucesso")
            col1, col2, col3 = st.columns(3)
            col1.metric("Sucessos", sucessos, delta_color="normal")
            col2.metric("Erros", len(results) - sucessos, delta_color="inverse")
            col3.metric("Total", len(results))
```

---

## 8. Validação de Certificado

```python
from src.utils.certificate import certificate_manager

# Verificar certificado antes de processar
if not certificate_manager.is_valid():
    print("❌ Certificado inválido ou expirado!")
    cert_info = certificate_manager.get_certificate_info()
    print(f"   Titular: {cert_info['subject']}")
    print(f"   Válido até: {cert_info['not_after']}")
else:
    print("✅ Certificado válido")
    
    # Obter PEM para autenticação
    cert_pem = certificate_manager.get_certificate_pem()
    
    # Usar no cliente
    client = NFSeAPIClient(certificate_pem=cert_pem)
```

---

## 9. Logging Personalizado

```python
from src.utils.logger import app_logger

# Configurar nível de log
app_logger.level("DEBUG")

# Logs automáticos durante o processamento
app_logger.info("Iniciando processamento de lote")
app_logger.debug(f"Dados: {registros}")
app_logger.success("✅ Lote processado com sucesso")
app_logger.error("❌ Erro ao processar documento")
app_logger.warning("⚠️  Alerta: documento com inconsistência")
```

---

## 10. Teste Completo End-to-End

```python
"""Teste completo do fluxo."""
import asyncio
from decimal import Decimal

async def teste_completo():
    print("🚀 Iniciando teste end-to-end\n")
    
    # 1. Setup
    generator = NFSeXMLGenerator(TipoAmbiente.HOMOLOGACAO)
    service = NFSeService()
    
    # 2. Simular extração de PDF
    registros = [
        {"cpf": "12345678901", "nome": "João Teste", "hash": "test1"},
    ]
    
    # 3. Configurar serviço
    config = {
        "discriminacao": "Teste de integração",
        "codigo_servico_municipal": "01.01",
        "item_lista_servico": "01.01",
        "valor_servicos": Decimal("100.00"),
        "aliquota_iss": Decimal("5.00"),
    }
    
    # 4. Processar
    results = await service.emitir_nfse_lote(registros, config)
    
    # 5. Validar
    assert len(results) == 1, "Deveria retornar 1 resultado"
    result = results[0]
    
    print(f"Status: {result.status}")
    print(f"Nome: {result.nome_tomador}")
    print(f"Chave de Acesso: {result.numero_nfse}")
    print(f"NSU: {result.protocolo}")
    print(f"Mensagem: {result.mensagem}")
    
    if result.status == "sucesso":
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print(f"\n❌ TESTE FALHOU: {result.mensagem}")

# Executar
asyncio.run(teste_completo())
```

---

**📚 Para mais exemplos, consulte:**
- `tests/test_api_adn_integration.py` - Testes automatizados
- `src/api/nfse_service.py` - Implementação completa
- `docs/MIGRATION_GUIDE_ADN.md` - Guia detalhado

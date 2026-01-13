"""
Script para emissão de NFS-e em PRODUÇÃO - Usando dados do PDF
URL: https://adn.nfse.gov.br/adn/DFe
Ambiente: PRODUCAO
"""
import asyncio
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.pdf.extractor import PDFDataExtractor
from src.models.schemas import (
    NFSeRequest, PrestadorServico, TomadorServico, 
    Servico, TipoAmbiente
)
from src.utils.xml_generator import NFSeXMLGenerator
from src.api.client import NFSeAPIClient
from src.utils.logger import app_logger


async def emitir_nota_do_pdf():
    """Emite uma nota fiscal para um cliente do PDF em PRODUÇÃO."""
    
    print("\n" + "="*80)
    print("🚀 EMISSÃO DE NFS-e EM PRODUÇÃO - USANDO DADOS DO PDF")
    print("="*80)
    print(f"🌐 URL: https://adn.nfse.gov.br/adn/DFe")
    print(f"🔐 Ambiente: PRODUCAO")
    print(f"📜 Certificado: GABRIEL SALEH SERVICOS MEDICOS LTDA")
    print("="*80 + "\n")
    
    # ========== CARREGAR PDF ==========
    pdf_path = r"c:\Users\Admin\Downloads\relatorio-bd59bfec-3ec0-4fc6-be09-b98e180ce176 (49).pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF não encontrado: {pdf_path}")
        print("\nPor favor, ajuste o caminho do PDF no script (linha 32)")
        return 1
    
    print(f"📄 Lendo PDF: {Path(pdf_path).name}")
    
    try:
        extractor = PDFDataExtractor()
        registros = extractor.extract_from_file(pdf_path)
        
        # Filtrar registros válidos
        registros_validos = [
            r for r in registros 
            if r.get('cpf') and r.get('nome') and r.get('hash')
        ]
        
        print(f"✅ {len(registros_validos)} registros válidos encontrados\n")
        
        if len(registros_validos) == 0:
            print("❌ Nenhum registro válido com CPF, Nome e Hash encontrado")
            return 1
            
    except Exception as e:
        print(f"❌ Erro ao ler PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # ========== LISTAR CLIENTES ==========
    print("=" * 80)
    print("📋 CLIENTES DISPONÍVEIS NO PDF")
    print("=" * 80 + "\n")
    
    for i, registro in enumerate(registros_validos[:20], 1):  # Mostra primeiros 20
        print(f"{i:3d}. {registro['nome'][:50]:<50} | CPF: {registro['cpf']}")
        print(f"      Hash: {registro.get('hash', 'N/A')[:30]}...")
        if i % 5 == 0:
            print()
    
    if len(registros_validos) > 20:
        print(f"\n... e mais {len(registros_validos) - 20} clientes")
    
    print("\n" + "=" * 80)
    
    # ========== SELECIONAR CLIENTE ==========
    while True:
        try:
            escolha = input(f"\nEscolha um cliente (1-{len(registros_validos)}) ou 'S' para sair: ").strip()
            
            if escolha.upper() == 'S':
                print("❌ Operação cancelada")
                return 0
            
            indice = int(escolha) - 1
            if 0 <= indice < len(registros_validos):
                cliente = registros_validos[indice]
                break
            else:
                print(f"⚠️  Digite um número entre 1 e {len(registros_validos)}")
        except ValueError:
            print("⚠️  Digite um número válido ou 'S' para sair")
    
    # ========== DADOS DO CLIENTE SELECIONADO ==========
    print("\n" + "=" * 80)
    print("👤 CLIENTE SELECIONADO")
    print("=" * 80)
    print(f"Nome: {cliente['nome']}")
    print(f"CPF: {cliente['cpf']}")
    print(f"Email: {cliente.get('email', 'Não informado')}")
    print(f"Telefone: {cliente.get('telefone', 'Não informado')}")
    print(f"Hash: {cliente['hash']}")
    print(f"Valor: R$ {cliente.get('valor', '0.00')}")
    print("=" * 80)
    
    # ========== CONFIGURAR SERVIÇO ==========
    print("\n📋 Configurando serviço...")
    
    # Valor padrão ou do PDF
    valor_servico = Decimal(str(cliente.get('valor', '150.00')))
    
    # Permitir editar
    print(f"\nValor atual: R$ {valor_servico:.2f}")
    novo_valor = input("Pressione ENTER para manter ou digite novo valor: ").strip()
    
    if novo_valor:
        try:
            valor_servico = Decimal(novo_valor)
        except:
            print("⚠️  Valor inválido, mantendo o original")
    
    print(f"\nDescrição do serviço:")
    descricao = input("Digite ou pressione ENTER para usar padrão: ").strip()
    if not descricao:
        descricao = "Serviços médicos especializados"
    
    # ========== CONFIGURAÇÃO DO PRESTADOR ==========
    prestador = PrestadorServico(
        cnpj="59418245000186",
        inscricao_municipal="8259069",  # Indicador Municipal correto
        razao_social="GABRIEL SALEH SERVICOS MEDICOS LTDA",
        nome_fantasia="GABRIEL SALEH",
        logradouro="RUA DR FLAVIO AUGUSTO TEIXEIRA FILHO",
        numero="40",
        bairro="CENTRO",
        municipio="FLORIANOPOLIS",  # Município correto
        uf="SC",  # Estado correto
        cep="88010000"  # CEP Florianópolis
    )
    
    # ========== DADOS DO TOMADOR ==========
    tomador = TomadorServico(
        cpf=cliente['cpf'],
        nome=cliente['nome'],
        email=cliente.get('email') if cliente.get('email') else None,
        telefone=cliente.get('telefone') if cliente.get('telefone') else None,
        logradouro="",
        numero="",
        municipio="FLORIANOPOLIS",
        uf="SC"
    )
    
    # ========== DADOS DO SERVIÇO ==========
    aliquota_iss = Decimal("2.00")  # 2% (conforme Florianópolis)
    valor_iss = valor_servico * (aliquota_iss / 100)
    
    servico = Servico(
        descricao=descricao,
        item_lista_servico="04.01",  # Serviços de saúde
        codigo_tributacao_municipio="040101",  # 04.01.01 - Medicina
        valor_servico=valor_servico,
        aliquota_iss=aliquota_iss,
        valor_iss=valor_iss
    )
    
    # ========== CRIAR REQUEST NFS-e ==========
    outras_info = f"Hash: {cliente['hash']} | Emitida em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    
    nfse_request = NFSeRequest(
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        outras_informacoes=outras_info
    )
    
    # ========== PREVIEW ==========
    print("\n" + "="*80)
    print("📄 PREVIEW DA NOTA FISCAL")
    print("="*80)
    print(f"\n👤 TOMADOR: {cliente['nome']}")
    print(f"📝 CPF: {cliente['cpf']}")
    print(f"📧 Email: {cliente.get('email', 'Não informado')}")
    print(f"📞 Telefone: {cliente.get('telefone', 'Não informado')}")
    print(f"🔑 Hash: {cliente['hash']}")
    print(f"\n💰 SERVIÇO: {descricao}")
    print(f"💵 Valor: R$ {valor_servico:.2f}")
    print(f"📊 ISS ({aliquota_iss}%): R$ {valor_iss:.2f}")
    print(f"💳 Total: R$ {valor_servico:.2f}")
    print("\n" + "="*80)
    
    # ========== CONFIRMAÇÃO ==========
    print("\n⚠️  ATENÇÃO: VOCÊ ESTÁ PRESTES A EMITIR UMA NOTA FISCAL REAL EM PRODUÇÃO ⚠️")
    confirmacao = input("\nDigite 'CONFIRMAR' para prosseguir: ").strip().upper()
    
    if confirmacao != "CONFIRMAR":
        print("\n❌ Operação cancelada pelo usuário")
        return 0
    
    # ========== GERAÇÃO DO XML ==========
    print("\n🔧 Gerando XML NFS-e...")
    try:
        cert_path = Path("certificados/cert.pem")
        key_path = Path("certificados/key.pem")
        
        if not cert_path.exists() or not key_path.exists():
            print(f"❌ Certificados não encontrados!")
            print(f"   Cert: {cert_path.absolute()}")
            print(f"   Key: {key_path.absolute()}")
            return 1
        
        generator = NFSeXMLGenerator(
            ambiente=TipoAmbiente.PRODUCAO,
            cert_path=str(cert_path.absolute()),
            key_path=str(key_path.absolute())
        )
        
        xml_assinado = generator.gerar_xml_assinado(nfse_request)
        print("✅ XML gerado e assinado digitalmente")
        
        # Salvar XML
        xml_file = Path(f"xml_producao_{cliente['cpf']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")
        xml_file.write_text(xml_assinado, encoding='utf-8')
        print(f"💾 XML salvo: {xml_file.name}")
        
        # Comprimir
        xml_comprimido = generator.comprimir_e_codificar(xml_assinado)
        print(f"📦 XML comprimido: {len(xml_comprimido)} caracteres")
        
    except Exception as e:
        print(f"❌ Erro ao gerar XML: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # ========== ENVIO PARA API ==========
    print("\n🚀 Enviando DPS para API Sefin Nacional em PRODUÇÃO...")
    print("📋 Endpoint: POST /nfse (geração síncrona de NFS-e)")
    try:
        # Inicializar cliente com certificados mTLS
        client = NFSeAPIClient(
            cert_path=str(cert_path.absolute()),
            key_path=str(key_path.absolute())
        )
        
        # Enviar DPS XML (SEM compressão) para gerar NFS-e
        response = await client.emitir_nfse(xml_assinado)
        
        print("\n" + "="*80)
        print("✅ RESPOSTA DA API")
        print("="*80)
        print(f"Status HTTP: {response.get('status', 'N/A')}")
        
        if "Lote" in response:
            lote = response["Lote"]
            if isinstance(lote, list) and len(lote) > 0:
                doc = lote[0]
                print(f"\n📋 Número do Lote: {doc.get('NumeroLote', 'N/A')}")
                print(f"🔑 Chave de Acesso: {doc.get('ChaveAcesso', 'N/A')}")
                print(f"📊 Status: {doc.get('Status', 'N/A')}")
                print(f"🔢 NSU: {doc.get('NSU', 'N/A')}")
                
                if "Mensagem" in doc:
                    print(f"📝 Mensagem: {doc['Mensagem']}")
        
        print("\n📄 Resposta completa:")
        import json
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Salvar resultado
        resultado_file = Path(f"resultado_producao_{cliente['cpf']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        resultado_file.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"\n💾 Resultado salvo: {resultado_file.name}")
        
        print("\n" + "="*80)
        print("✅ NOTA FISCAL EMITIDA COM SUCESSO!")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro ao enviar para API: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print("\n" + "⚠️ "*20)
    print("   AMBIENTE DE PRODUÇÃO - EMISSÕES REAIS")
    print("⚠️ "*20 + "\n")
    
    try:
        exit_code = asyncio.run(emitir_nota_do_pdf())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

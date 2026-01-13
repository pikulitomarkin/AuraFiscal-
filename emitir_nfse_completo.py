"""
Script integrado: Emite NFS-e e gera automaticamente XML + PDF (DANFSE).
"""

import asyncio
import base64
import gzip
import hashlib
from lxml import etree
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from pathlib import Path

from src.models.schemas import PrestadorServico, TomadorServico, Servico, NFSeRequest, TipoAmbiente
from src.utils.xml_generator import NFSeXMLGenerator
from src.api.client import NFSeAPIClient
from gerar_danfse_v2 import gerar_danfse
from config.settings import settings


def assinar_xml_exclusive_c14n(xml_string: str, cert_path: str, key_path: str) -> str:
    """Assina XML com Exclusive C14N (método que funciona)."""
    
    root = etree.fromstring(xml_string.encode('utf-8'))
    ns = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}
    inf_dps = root.find('.//nfse:infDPS', ns)
    id_dps = inf_dps.get('Id')
    
    with open(cert_path, 'rb') as f:
        cert_data = f.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    
    with open(key_path, 'rb') as f:
        key_data = f.read()
        private_key = serialization.load_pem_private_key(key_data, None, default_backend())
    
    # Canonicalizar com Exclusive C14N
    c14n_xml = etree.tostring(inf_dps, method='c14n', exclusive=True, inclusive_ns_prefixes=None)
    digest_value = hashlib.sha256(c14n_xml).digest()
    digest_b64 = base64.b64encode(digest_value).decode('utf-8')
    
    # Criar SignedInfo
    nsmap_sig = {None: 'http://www.w3.org/2000/09/xmldsig#'}
    signed_info = etree.Element('{http://www.w3.org/2000/09/xmldsig#}SignedInfo', nsmap=nsmap_sig)
    
    c14n_method = etree.SubElement(signed_info, '{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod')
    c14n_method.set('Algorithm', 'http://www.w3.org/2001/10/xml-exc-c14n#')
    
    sig_method = etree.SubElement(signed_info, '{http://www.w3.org/2000/09/xmldsig#}SignatureMethod')
    sig_method.set('Algorithm', 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256')
    
    reference = etree.SubElement(signed_info, '{http://www.w3.org/2000/09/xmldsig#}Reference')
    reference.set('URI', f'#{id_dps}')
    
    transforms = etree.SubElement(reference, '{http://www.w3.org/2000/09/xmldsig#}Transforms')
    
    transform1 = etree.SubElement(transforms, '{http://www.w3.org/2000/09/xmldsig#}Transform')
    transform1.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#enveloped-signature')
    
    transform2 = etree.SubElement(transforms, '{http://www.w3.org/2000/09/xmldsig#}Transform')
    transform2.set('Algorithm', 'http://www.w3.org/2001/10/xml-exc-c14n#')
    
    digest_method = etree.SubElement(reference, '{http://www.w3.org/2000/09/xmldsig#}DigestMethod')
    digest_method.set('Algorithm', 'http://www.w3.org/2001/04/xmlenc#sha256')
    
    digest_value_elem = etree.SubElement(reference, '{http://www.w3.org/2000/09/xmldsig#}DigestValue')
    digest_value_elem.text = digest_b64
    
    # Canonicalizar SignedInfo
    c14n_signed_info = etree.tostring(signed_info, method='c14n', exclusive=True, inclusive_ns_prefixes=None)
    
    # Assinar
    signature = private_key.sign(c14n_signed_info, padding.PKCS1v15(), hashes.SHA256())
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # Montar Signature
    signature_elem = etree.Element('{http://www.w3.org/2000/09/xmldsig#}Signature', nsmap=nsmap_sig)
    signature_elem.append(signed_info)
    
    signature_value = etree.SubElement(signature_elem, '{http://www.w3.org/2000/09/xmldsig#}SignatureValue')
    signature_value.text = signature_b64
    
    # KeyInfo
    key_info = etree.SubElement(signature_elem, '{http://www.w3.org/2000/09/xmldsig#}KeyInfo')
    x509_data = etree.SubElement(key_info, '{http://www.w3.org/2000/09/xmldsig#}X509Data')
    x509_cert = etree.SubElement(x509_data, '{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
    
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode('utf-8')
    cert_lines = '\n'.join([cert_b64[i:i+64] for i in range(0, len(cert_b64), 64)])
    x509_cert.text = '\n' + cert_lines + '\n'
    
    root.append(signature_elem)
    
    xml_assinado = etree.tostring(root, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_assinado}'


async def emitir_nfse_com_pdf(
    prestador: PrestadorServico,
    tomador: TomadorServico,
    servico: Servico,
    salvar_arquivos: bool = True
):
    """
    Emite NFS-e e gera automaticamente XML + PDF.
    
    Args:
        prestador: Dados do prestador
        tomador: Dados do tomador
        servico: Dados do serviço
        salvar_arquivos: Se True, salva arquivos com nomes automáticos
    
    Returns:
        dict com chave_acesso, xml_path, pdf_path
    """
    
    # Verificar certificados logo no início
    cert_dir = Path("certificados")
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    if not cert_dir.exists():
        raise FileNotFoundError(
            "❌ Pasta 'certificados' não encontrada. "
            "Verifique a configuração das variáveis de ambiente no Railway."
        )
    
    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError(
            f"❌ Certificados não encontrados:\n"
            f"   cert.pem existe: {cert_path.exists()}\n"
            f"   key.pem existe: {key_path.exists()}\n"
            f"   Certifique-se de que CERTIFICATE_CERT_PEM e CERTIFICATE_KEY_PEM "
            f"estão configurados no Railway."
        )
    
    print("\n" + "="*70)
    print("EMISSAO NFS-e COMPLETA (XML + PDF)")
    print("="*70)
    
    # Obter ambiente da configuração
    ambiente = TipoAmbiente(settings.NFSE_API_AMBIENTE)
    
    # 1. Preparar request
    nfse_request = NFSeRequest(
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        data_emissao=datetime.now(),
        ambiente=ambiente
    )
    
    print(f"\nPrestador: {prestador.razao_social}")
    print(f"Tomador: {tomador.nome}")
    print(f"Valor: R$ {servico.valor_servico}")
    print(f"Ambiente: {ambiente.value}")
    
    # 2. Gerar XML DPS
    print("\n[1] Gerando XML DPS...")
    generator = NFSeXMLGenerator(ambiente=ambiente)
    xml_dps = generator.gerar_xml_nfse(nfse_request)
    print(f"    OK {len(xml_dps)} bytes")
    
    # 3. Assinar
    print("[2] Assinando XML...")
    xml_assinado = assinar_xml_exclusive_c14n(xml_dps, str(cert_path), str(key_path))
    print(f"    OK {len(xml_assinado)} bytes")
    
    # 4. Comprimir
    print("[3] Comprimindo (GZIP + Base64)...")
    xml_bytes = xml_assinado.encode('utf-8')
    compressed = gzip.compress(xml_bytes)
    b64_encoded = base64.b64encode(compressed).decode('utf-8')
    print(f"    OK {len(compressed)} bytes comprimidos")
    
    # 5. Enviar
    print("[4] Enviando para Sefin Nacional...")
    client = NFSeAPIClient(cert_path=str(cert_path), key_path=str(key_path))
    
    try:
        resultado = await client.emitir_nfse(b64_encoded)
        
        # Extrair chave
        chave_acesso = resultado.get('chaveAcesso', '')
        
        print(f"    OK NFS-e AUTORIZADA!")
        print(f"    Chave: {chave_acesso}")
        
        # 6. Salvar XML
        print("[5] Salvando XML...")
        nfse_compressed = base64.b64decode(resultado['nfseXmlGZipB64'])
        nfse_xml = gzip.decompress(nfse_compressed).decode('utf-8')
        
        if salvar_arquivos:
            xml_path = Path(f"nfse_{chave_acesso[-10:]}.xml")
        else:
            xml_path = Path("nfse_temp.xml")
        
        xml_path.write_text(nfse_xml, encoding='utf-8')
        print(f"    OK {xml_path}")
        
        # 7. Gerar PDF
        print("[6] Gerando DANFSE (PDF)...")
        pdf_path = gerar_danfse(str(xml_path))
        pdf_size = Path(pdf_path).stat().st_size
        print(f"    OK {pdf_path} ({pdf_size} bytes)")
        
        print("\n" + "="*70)
        print("SUCESSO! NFS-e EMITIDA")
        print("="*70)
        print(f"\nChave de Acesso: {chave_acesso}")
        print(f"XML: {xml_path}")
        print(f"PDF: {pdf_path}")
        print("="*70 + "\n")
        
        return {
            'sucesso': True,
            'chave_acesso': chave_acesso,
            'xml_path': str(xml_path),
            'pdf_path': str(pdf_path),
            'resultado': resultado
        }
        
    except Exception as e:
        print(f"\n[ERRO] Falha: {e}")
        return {'sucesso': False, 'erro': str(e)}


async def exemplo_emissao():
    """Exemplo de emissão de NFS-e."""
    
    # Dados do prestador
    prestador = PrestadorServico(
        cnpj="59418245000186",
        razao_social="GABRIEL SALEH SERVICOS MEDICOS LTDA",
        nome_fantasia="Dr. Gabriel Saleh",
        logradouro="Rua Felipe Schmidt",
        numero="100",
        bairro="Centro",
        municipio="Florianopolis",
        uf="SC",
        cep="88010000"
    )
    
    # Dados do tomador
    tomador = TomadorServico(
        cpf="10463540948",
        nome="Cliente Teste"
    )
    
    # Dados do serviço
    servico = Servico(
        descricao="Consulta medica especializada",
        item_lista_servico="04.01.01",
        valor_servico=89.00,
        aliquota_iss=2.00,
        valor_iss=1.78,
        valor_deducoes=0.00
    )
    
    # Emitir NFS-e
    resultado = await emitir_nfse_com_pdf(prestador, tomador, servico)
    
    return resultado['sucesso']


if __name__ == "__main__":
    sucesso = asyncio.run(exemplo_emissao())
    exit(0 if sucesso else 1)

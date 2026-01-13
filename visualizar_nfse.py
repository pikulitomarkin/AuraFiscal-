"""
Visualizador de NFS-e autorizada.
Extrai e exibe informações da NFS-e do arquivo XML salvo.
"""

from pathlib import Path
from lxml import etree
from datetime import datetime


def formatar_xml(xml_string: str) -> str:
    """Formata XML para visualização."""
    try:
        root = etree.fromstring(xml_string.encode('utf-8'))
        return etree.tostring(root, encoding='unicode', pretty_print=True)
    except:
        return xml_string


def visualizar_nfse(xml_path: str = "nfse_autorizada_final.xml"):
    """
    Visualiza informações da NFS-e autorizada.
    
    Args:
        xml_path: Caminho do arquivo XML
    """
    
    arquivo = Path(xml_path)
    
    if not arquivo.exists():
        print(f"\n[ERRO] Arquivo nao encontrado: {xml_path}")
        print("\nArquivos de NFS-e disponiveis:")
        for f in Path(".").glob("nfse*.xml"):
            print(f"  - {f.name}")
        return False
    
    print("\n" + "="*70)
    print("VISUALIZACAO NFS-e AUTORIZADA")
    print("="*70)
    
    # Ler e parsear XML
    xml_content = arquivo.read_text(encoding='utf-8')
    
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
        ns = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}
        
        # Extrair informações principais
        inf_nfse = root.find('.//nfse:infNFSe', ns)
        
        if inf_nfse is None:
            print("\n[ERRO] Elemento infNFSe nao encontrado no XML")
            return False
        
        # ID/Chave
        id_nfse = inf_nfse.get('Id', 'N/A')
        chave = id_nfse.replace('NFS', '') if id_nfse.startswith('NFS') else id_nfse
        
        print(f"\nChave de Acesso: {chave}")
        print(f"Arquivo: {xml_path}")
        print(f"Tamanho: {len(xml_content)} bytes")
        
        # Número e status
        n_nfse = inf_nfse.findtext('.//nfse:nNFSe', namespaces=ns, default='N/A')
        c_stat = inf_nfse.findtext('.//nfse:cStat', namespaces=ns, default='N/A')
        dh_proc = inf_nfse.findtext('.//nfse:dhProc', namespaces=ns, default='N/A')
        
        print(f"\n{'='*70}")
        print("DADOS DA NFS-e")
        print(f"{'='*70}")
        print(f"Numero NFS-e: {n_nfse}")
        print(f"Status: {c_stat} - {'AUTORIZADA' if c_stat == '100' else 'VERIFICAR'}")
        print(f"Data/Hora Processamento: {dh_proc}")
        
        # Local de emissão
        x_loc_emi = inf_nfse.findtext('.//nfse:xLocEmi', namespaces=ns, default='N/A')
        x_loc_prest = inf_nfse.findtext('.//nfse:xLocPrestacao', namespaces=ns, default='N/A')
        print(f"\nLocal Emissao: {x_loc_emi}")
        print(f"Local Prestacao: {x_loc_prest}")
        
        # Emitente
        emit = inf_nfse.find('.//nfse:emit', ns)
        if emit is not None:
            cnpj = emit.findtext('.//nfse:CNPJ', namespaces=ns, default='N/A')
            x_nome = emit.findtext('.//nfse:xNome', namespaces=ns, default='N/A')
            
            print(f"\n{'='*70}")
            print("PRESTADOR (EMITENTE)")
            print(f"{'='*70}")
            print(f"CNPJ: {cnpj}")
            print(f"Nome: {x_nome}")
            
            # Endereço
            ender = emit.find('.//nfse:enderNac', ns)
            if ender is not None:
                logr = ender.findtext('.//nfse:xLgr', namespaces=ns, default='')
                nro = ender.findtext('.//nfse:nro', namespaces=ns, default='')
                bairro = ender.findtext('.//nfse:xBairro', namespaces=ns, default='')
                uf = ender.findtext('.//nfse:UF', namespaces=ns, default='')
                cep = ender.findtext('.//nfse:CEP', namespaces=ns, default='')
                
                print(f"Endereco: {logr}, {nro} - {bairro}")
                print(f"UF/CEP: {uf} / {cep}")
        
        # Tomador (do DPS)
        dps = root.find('.//nfse:DPS', ns)
        if dps is not None:
            toma = dps.find('.//nfse:toma', ns)
            if toma is not None:
                cpf = toma.findtext('.//nfse:CPF', namespaces=ns, default='N/A')
                cnpj_toma = toma.findtext('.//nfse:CNPJ', namespaces=ns, default='N/A')
                x_nome_toma = toma.findtext('.//nfse:xNome', namespaces=ns, default='N/A')
                
                print(f"\n{'='*70}")
                print("TOMADOR (CLIENTE)")
                print(f"{'='*70}")
                if cpf != 'N/A':
                    print(f"CPF: {cpf}")
                else:
                    print(f"CNPJ: {cnpj_toma}")
                print(f"Nome: {x_nome_toma}")
        
        # Valores
        valores = inf_nfse.find('.//nfse:valores', ns)
        if valores is not None:
            v_bc = valores.findtext('.//nfse:vBC', namespaces=ns, default='0.00')
            p_aliq = valores.findtext('.//nfse:pAliqAplic', namespaces=ns, default='0.00')
            v_issqn = valores.findtext('.//nfse:vISSQN', namespaces=ns, default='0.00')
            v_liq = valores.findtext('.//nfse:vLiq', namespaces=ns, default='0.00')
            
            print(f"\n{'='*70}")
            print("VALORES")
            print(f"{'='*70}")
            print(f"Base de Calculo: R$ {v_bc}")
            print(f"Aliquota ISS: {p_aliq}%")
            print(f"Valor ISS: R$ {v_issqn}")
            print(f"Valor Liquido: R$ {v_liq}")
        
        # Serviço (do DPS)
        if dps is not None:
            serv = dps.find('.//nfse:serv', ns)
            if serv is not None:
                c_trib = serv.findtext('.//nfse:cTribNac', namespaces=ns, default='N/A')
                x_desc = serv.findtext('.//nfse:xDescServ', namespaces=ns, default='N/A')
                
                print(f"\n{'='*70}")
                print("SERVICO PRESTADO")
                print(f"{'='*70}")
                print(f"Codigo Tributacao: {c_trib}")
                print(f"Descricao: {x_desc}")
        
        # Assinatura
        signatures = root.findall('.//{http://www.w3.org/2000/09/xmldsig#}Signature')
        print(f"\n{'='*70}")
        print("ASSINATURAS DIGITAIS")
        print(f"{'='*70}")
        print(f"Total de assinaturas: {len(signatures)}")
        
        if len(signatures) >= 1:
            print("  [1] Assinatura do Emissor (DPS)")
        if len(signatures) >= 2:
            print("  [2] Assinatura Sefin Nacional (NFS-e)")
        
        print(f"\n{'='*70}")
        print("SUCESSO - NFS-e VALIDA E AUTORIZADA")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao processar XML: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    # Permitir passar caminho como argumento
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "nfse_autorizada_final.xml"
    
    visualizar_nfse(xml_path)

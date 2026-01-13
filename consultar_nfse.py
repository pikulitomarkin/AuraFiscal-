"""
Script para consultar NFS-e pela chave de acesso.
"""

import asyncio
from pathlib import Path
from src.api.client import NFSeAPIClient


async def consultar_nfse_por_chave(chave_acesso: str):
    """
    Consulta NFS-e pela chave de acesso.
    
    Args:
        chave_acesso: Chave de acesso da NFS-e (50 dígitos)
    """
    
    print("\n" + "="*70)
    print("CONSULTA NFS-e - SEFIN NACIONAL")
    print("="*70)
    
    print(f"\nChave de Acesso: {chave_acesso}")
    print(f"Tamanho: {len(chave_acesso)} dígitos")
    
    # Validar chave
    if len(chave_acesso) != 50:
        print(f"\n[ERRO] Chave de acesso deve ter 50 dígitos. Recebido: {len(chave_acesso)}")
        return False
    
    # Cliente API com mTLS
    cert_path = "certificados/cert.pem"
    key_path = "certificados/key.pem"
    
    client = NFSeAPIClient(cert_path=cert_path, key_path=key_path)
    
    print("\n[1] Consultando na Sefin Nacional...")
    
    try:
        # Endpoint de consulta: GET /SefinNacional/nfse/{chaveAcesso}
        endpoint = f"/SefinNacional/nfse/{chave_acesso}"
        
        # Fazer requisição GET
        async with client._create_client() as http_client:
            response = await http_client.get(
                f"{client.base_url}{endpoint}",
                timeout=client.timeout
            )
            
            response.raise_for_status()
            resultado = response.json()
        
        print("\n" + "="*70)
        print("NFS-e ENCONTRADA")
        print("="*70)
        
        # Exibir informações
        if 'infNFSe' in resultado:
            info = resultado['infNFSe']
            print(f"\nNumero NFS-e: {info.get('nNFSe', 'N/A')}")
            print(f"Situacao: {info.get('cStat', 'N/A')} - {info.get('xMotivo', 'N/A')}")
            print(f"Data Processamento: {info.get('dhProc', 'N/A')}")
            
            if 'emit' in info:
                emit = info['emit']
                print(f"\nEmitente:")
                print(f"  CNPJ: {emit.get('CNPJ', 'N/A')}")
                print(f"  Nome: {emit.get('xNome', 'N/A')}")
            
            if 'valores' in info:
                valores = info['valores']
                print(f"\nValores:")
                print(f"  Base Calculo: R$ {valores.get('vBC', 'N/A')}")
                print(f"  Aliquota: {valores.get('pAliqAplic', 'N/A')}%")
                print(f"  ISSQN: R$ {valores.get('vISSQN', 'N/A')}")
                print(f"  Valor Liquido: R$ {valores.get('vLiq', 'N/A')}")
        
        # Salvar XML completo
        if 'nfseXml' in resultado:
            xml_path = Path(f"nfse_consultada_{chave_acesso[-10:]}.xml")
            xml_path.write_text(resultado['nfseXml'], encoding='utf-8')
            print(f"\nXML salvo em: {xml_path}")
        
        print("\n" + "="*70)
        return True
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print("\n[ERRO] NFS-e nao encontrada com essa chave de acesso")
        else:
            print(f"\n[ERRO] HTTP {e.response.status_code}: {e.response.text}")
        return False
        
    except Exception as e:
        print(f"\n[ERRO] Falha na consulta: {e}")
        return False


async def consultar_ultima_nfse():
    """Consulta a última NFS-e autorizada."""
    
    # Ler a última chave de acesso do arquivo de NFS-e autorizada
    nfse_path = Path("nfse_autorizada_final.xml")
    
    if not nfse_path.exists():
        print("\n[ERRO] Arquivo nfse_autorizada_final.xml nao encontrado")
        print("Execute test_emissao_final.py primeiro para emitir uma NFS-e")
        return False
    
    # Ler XML e extrair chave
    import re
    xml_content = nfse_path.read_text(encoding='utf-8')
    
    # Procurar chaveAcesso no XML ou no atributo Id
    match = re.search(r'Id="NFS(\d{50})"', xml_content)
    if match:
        chave_acesso = match.group(1)
    else:
        # Tentar extrair de outro padrão
        match = re.search(r'<chaveAcesso>(\d{50})</chaveAcesso>', xml_content)
        if match:
            chave_acesso = match.group(1)
        else:
            print("\n[ERRO] Nao foi possivel extrair chave de acesso do XML")
            return False
    
    await consultar_nfse_por_chave(chave_acesso)


async def main():
    """Menu de consulta."""
    
    import sys
    
    if len(sys.argv) > 1:
        # Chave fornecida como argumento
        chave = sys.argv[1].strip()
        await consultar_nfse_por_chave(chave)
    else:
        # Consultar última emitida
        print("\nConsultando ultima NFS-e autorizada...")
        await consultar_ultima_nfse()


if __name__ == "__main__":
    import httpx
    asyncio.run(main())

"""
Script de inicialização para Railway.
Carrega certificados de variáveis de ambiente Base64.
"""
import os
import base64
from pathlib import Path


def setup_certificates():
    """
    Configura certificados a partir de variáveis de ambiente Base64.
    Usado no Railway onde não podemos subir arquivos .pem diretamente.
    """
    cert_dir = Path("certificados")
    cert_dir.mkdir(exist_ok=True)
    
    # Verificar se certificados já existem
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    if cert_path.exists() and key_path.exists():
        print("✅ Certificados já existem localmente")
        return True
    
    # Tentar carregar de variáveis de ambiente
    cert_b64 = os.getenv("CERTIFICATE_CERT_PEM")
    key_b64 = os.getenv("CERTIFICATE_KEY_PEM")
    
    if cert_b64 and key_b64:
        try:
            # Decodificar e salvar cert.pem
            cert_content = base64.b64decode(cert_b64)
            cert_path.write_bytes(cert_content)
            print(f"✅ Certificado salvo em {cert_path}")
            
            # Decodificar e salvar key.pem
            key_content = base64.b64decode(key_b64)
            key_path.write_bytes(key_content)
            os.chmod(key_path, 0o600)  # Permissões restritas
            print(f"✅ Chave privada salva em {key_path}")
            
            return True
        except Exception as e:
            print(f"❌ Erro ao decodificar certificados: {e}")
            return False
    else:
        print("⚠️ Variáveis CERTIFICATE_CERT_PEM e CERTIFICATE_KEY_PEM não definidas")
        print("   Certifique-se de que os arquivos cert.pem e key.pem existem em ./certificados/")
        return cert_path.exists() and key_path.exists()


def main():
    """Ponto de entrada principal."""
    print("\n" + "="*60)
    print("🚀 NFS-e Automation System - Inicialização Railway")
    print("="*60 + "\n")
    
    # Configurar certificados
    if not setup_certificates():
        print("\n❌ Falha na configuração de certificados")
        print("   O sistema pode não funcionar corretamente para emissão de NFS-e")
    
    print("\n✅ Inicialização concluída!")
    print("   Iniciando Streamlit...\n")


if __name__ == "__main__":
    main()

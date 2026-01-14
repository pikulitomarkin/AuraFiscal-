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
    print(f"📁 Pasta certificados criada/verificada: {cert_dir.absolute()}")
    
    # Verificar se certificados já existem
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    if cert_path.exists() and key_path.exists():
        print("✅ Certificados já existem localmente")
        print(f"   - {cert_path} ({cert_path.stat().st_size} bytes)")
        print(f"   - {key_path} ({key_path.stat().st_size} bytes)")
        return True
    
    # Tentar carregar de variáveis de ambiente
    cert_b64 = os.getenv("CERTIFICATE_CERT_PEM")
    key_b64 = os.getenv("CERTIFICATE_KEY_PEM")
    
    print(f"\n🔍 Verificando variáveis de ambiente:")
    print(f"   CERTIFICATE_CERT_PEM: {'✅ Definida' if cert_b64 else '❌ NÃO DEFINIDA'} ({len(cert_b64) if cert_b64 else 0} chars)")
    print(f"   CERTIFICATE_KEY_PEM: {'✅ Definida' if key_b64 else '❌ NÃO DEFINIDA'} ({len(key_b64) if key_b64 else 0} chars)")
    
    if cert_b64 and key_b64:
        try:
            print("\n🔓 Decodificando certificados Base64...")
            # Decodificar e salvar cert.pem
            cert_content = base64.b64decode(cert_b64)
            cert_path.write_bytes(cert_content)
            print(f"✅ Certificado salvo: {cert_path} ({len(cert_content)} bytes)")
            
            # Decodificar e salvar key.pem
            key_content = base64.b64decode(key_b64)
            key_path.write_bytes(key_content)
            os.chmod(key_path, 0o600)  # Permissões restritas
            print(f"✅ Chave privada salva: {key_path} ({len(key_content)} bytes)")
            
            return True
        except Exception as e:
            print(f"❌ Erro ao decodificar certificados: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n❌ CERTIFICADOS NÃO CONFIGURADOS!")
        print("   Você precisa configurar no Railway:")
        print("   1. CERTIFICATE_CERT_PEM (Base64 do cert.pem)")
        print("   2. CERTIFICATE_KEY_PEM (Base64 do key.pem)")
        print("\n   Verifique o arquivo RAILWAY_VARIAVEIS.txt no repositório")
        return False


def main():
    """Ponto de entrada principal."""
    print("\n" + "="*60)
    print("🚀 NFS-e Automation System - Inicialização Railway")
    print("="*60 + "\n")
    
    # Configurar certificados
    cert_ok = setup_certificates()
    
    if cert_ok:
        # Recarrega o certificate_manager após criar os arquivos
        try:
            from src.utils.certificate import certificate_manager
            if certificate_manager.reload():
                print("✅ Certificate Manager recarregado com sucesso")
            else:
                print("⚠️ Certificate Manager não conseguiu recarregar certificado")
        except Exception as e:
            print(f"⚠️ Erro ao recarregar Certificate Manager: {e}")
    else:
        print("\n❌ Falha na configuração de certificados")
        print("   O sistema pode não funcionar corretamente para emissão de NFS-e")
    
    print("\n✅ Inicialização concluída!")
    print("   Iniciando Streamlit...\n")


if __name__ == "__main__":
    main()

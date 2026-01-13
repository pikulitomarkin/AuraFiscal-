"""
Gerenciamento de Certificado Digital A1 para assinatura de NFS-e.
"""
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from datetime import datetime, timezone

from config.settings import settings
from src.utils.logger import app_logger


class CertificateManager:
    """Gerencia certificado digital A1 para assinatura de documentos."""
    
    def __init__(self, cert_path: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializa o gerenciador de certificados.
        
        Args:
            cert_path: Caminho para o arquivo .pfx/.p12
            password: Senha do certificado
        """
        self.cert_path = Path(cert_path or settings.CERTIFICATE_PATH)
        self.password = password or settings.CERTIFICATE_PASSWORD
        self._certificate: Optional[x509.Certificate] = None
        self._private_key = None
        
        if self.cert_path.exists():
            self._load_certificate()
    
    def _load_certificate(self) -> None:
        """Carrega o certificado digital do arquivo."""
        try:
            with open(self.cert_path, 'rb') as f:
                pfx_data = f.read()
            
            # Carrega o certificado usando cryptography
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.password.encode(),
                backend=default_backend()
            )
            
            self._certificate = certificate
            self._private_key = private_key
            
            app_logger.info(f"Certificado carregado: {self.get_subject_name()}")
            
        except Exception as e:
            app_logger.error(f"Erro ao carregar certificado: {e}")
            raise ValueError(f"Falha ao carregar certificado: {e}")
    
    def is_valid(self) -> bool:
        """
        Verifica se o certificado está válido (dentro da validade).
        
        Returns:
            True se válido, False caso contrário
        """
        if not self._certificate:
            return False
        
        now = datetime.now(timezone.utc)
        not_before = self._certificate.not_valid_before_utc
        not_after = self._certificate.not_valid_after_utc
        
        is_valid = not_before <= now <= not_after
        
        if not is_valid:
            app_logger.warning(
                f"Certificado fora da validade. Válido de {not_before} até {not_after}"
            )
        
        return is_valid
    
    def get_subject_name(self) -> str:
        """
        Obtém o nome do titular do certificado.
        
        Returns:
            Nome do titular
        """
        if not self._certificate:
            return "Certificado não carregado"
        
        subject = self._certificate.subject
        cn = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        
        return cn[0].value if cn else "Nome não encontrado"
    
    def get_expiration_date(self) -> Optional[datetime]:
        """
        Obtém a data de expiração do certificado.
        
        Returns:
            Data de expiração ou None
        """
        if not self._certificate:
            return None
        
        return self._certificate.not_valid_after
    
    def get_certificate_info(self) -> dict:
        """
        Retorna informações completas do certificado.
        
        Returns:
            Dicionário com informações do certificado
        """
        if not self._certificate:
            return {"status": "Certificado não carregado"}
        
        subject = self._certificate.subject
        issuer = self._certificate.issuer
        
        return {
            "subject": self.get_subject_name(),
            "issuer": issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value,
            "serial_number": str(self._certificate.serial_number),
            "valid_from": self._certificate.not_valid_before_utc.isoformat(),
            "valid_until": self._certificate.not_valid_after_utc.isoformat(),
            "is_valid": self.is_valid(),
            "days_until_expiration": (self._certificate.not_valid_after_utc - datetime.now(timezone.utc)).days
        }
    
    def sign_data(self, data: bytes) -> bytes:
        """
        Assina dados usando a chave privada do certificado.
        
        Args:
            data: Dados a serem assinados
            
        Returns:
            Assinatura digital
        """
        if not self._private_key:
            raise ValueError("Chave privada não carregada")
        
        if not self.is_valid():
            raise ValueError("Certificado fora da validade")
        
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        
        signature = self._private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return signature
    
    def get_certificate_pem(self) -> str:
        """
        Retorna o certificado em formato PEM.
        
        Returns:
            Certificado em formato PEM (string)
        """
        if not self._certificate:
            raise ValueError("Certificado não carregado")
        
        pem_data = self._certificate.public_bytes(
            encoding=serialization.Encoding.PEM
        )
        
        return pem_data.decode('utf-8')
    
    def get_private_key_pem(self) -> str:
        """
        Retorna a chave privada em formato PEM.
        
        Returns:
            Chave privada em formato PEM (string)
        """
        if not self._private_key:
            raise ValueError("Chave privada não carregada")
        
        pem_data = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return pem_data.decode('utf-8')
    
    def get_cert_and_key_files(self) -> Tuple[str, str]:
        """
        Cria arquivos temporários com certificado e chave em formato PEM.
        
        Returns:
            Tupla com caminhos (cert_file, key_file)
        """
        import tempfile
        
        # Cria arquivos temporários
        cert_fd, cert_path = tempfile.mkstemp(suffix='.pem', text=True)
        key_fd, key_path = tempfile.mkstemp(suffix='.pem', text=True)
        
        try:
            # Escreve certificado
            with open(cert_path, 'w') as f:
                f.write(self.get_certificate_pem())
            
            # Escreve chave privada
            with open(key_path, 'w') as f:
                f.write(self.get_private_key_pem())
            
            return cert_path, key_path
            
        finally:
            # Fecha os file descriptors
            import os
            os.close(cert_fd)
            os.close(key_fd)


# Instância global (singleton)
certificate_manager = CertificateManager()

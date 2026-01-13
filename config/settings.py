"""
Configurações centralizadas da aplicação usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação com validação automática."""
    
    # Aplicação
    APP_NAME: str = "NFS-e Automation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"
    
    # Banco de Dados
    DATABASE_URL: str = "sqlite+aiosqlite:///./nfse.db"
    DB_ECHO: bool = False
    
    # API Nacional NFS-e (Sefin Nacional - Sistema Nacional NFS-e)
    # Ambiente de PRODUÇÃO
    # URL Base: https://sefin.nfse.gov.br
    # Endpoint: POST /SefinNacional/nfse para emissão (conforme Swagger Sefin Nacional)
    NFSE_API_BASE_URL: str = "https://sefin.nfse.gov.br"
    NFSE_API_AMBIENTE: str = "PRODUCAO"  # HOMOLOGACAO ou PRODUCAO
    NFSE_API_TIMEOUT: int = 30
    NFSE_API_MAX_RETRIES: int = 3
    
    # API ADN - Endpoint de recepção de lote (POST /adn/DFe)
    ADN_RECEPCAO_LOTE_ENDPOINT: str = "/adn/DFe"  # POST - Envio lote DPS/NFS-e comprimido
    ADN_DISTRIBUICAO_ENDPOINT: str = "/DFe"  # GET - Consulta por NSU
    
    # API Sefin Nacional - Endpoints (podem não estar disponíveis em prod restrita)
    SEFIN_EMISSAO_ENDPOINT: str = "/nfse"  # POST - Envio DPS para GERAR NFS-e
    SEFIN_CONSULTA_ENDPOINT: str = "/nfse/{chaveAcesso}"  # GET - Consulta NFS-e
    SEFIN_EVENTOS_ENDPOINT: str = "/nfse/{chaveAcesso}/eventos"  # POST - Eventos
    
    # API ADN - Configuração
    ADN_API_BASE_URL: str = "https://adn.nfse.gov.br"
    ADN_API_TIMEOUT: int = 30
    ADN_API_MAX_RETRIES: int = 3
    
    # Certificado Digital
    CERTIFICATE_PATH: str = "certificados/cert.pem"
    CERTIFICATE_PASSWORD: str = ""
    
    # Processamento em Lote
    MAX_BATCH_SIZE: int = 600
    MIN_BATCH_SIZE: int = 1
    CONCURRENT_REQUESTS: int = 10
    
    # Logs
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/nfse_automation.log"
    
    # Autenticação
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = "$2b$12$default_hash_change_in_production"
    
    # Streamlit
    STREAMLIT_SERVER_PORT: int = 8501
    STREAMLIT_SERVER_ADDRESS: str = "localhost"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator('DATABASE_URL')
    @classmethod
    def convert_postgres_url(cls, v: str) -> str:
        """Converte postgresql:// para postgresql+asyncpg:// para Railway."""
        if v.startswith('postgresql://'):
            return v.replace('postgresql://', 'postgresql+asyncpg://', 1)
        return v
    
    @property
    def base_dir(self) -> Path:
        """Retorna o diretório base do projeto."""
        return Path(__file__).parent.parent
    
    @property
    def log_dir(self) -> Path:
        """Retorna o diretório de logs."""
        log_path = self.base_dir / "logs"
        log_path.mkdir(exist_ok=True)
        return log_path


# Instância global de configurações
settings = Settings()

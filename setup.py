#!/usr/bin/env python
"""
Script de inicialização do projeto.
Configura ambiente, banco de dados e certificado.
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.database import init_database, engine
from config.settings import settings
from src.utils.logger import app_logger
from src.utils.certificate import get_certificate_manager


async def initialize_database():
    """Inicializa o banco de dados criando as tabelas."""
    try:
        app_logger.info("Inicializando banco de dados...")
        await init_database()
        app_logger.info("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        app_logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        raise


def check_certificate():
    """Verifica o certificado digital."""
    try:
        app_logger.info("Verificando certificado digital...")
        
        if certificate_manager.is_valid():
            info = certificate_manager.get_certificate_info()
            app_logger.info(f"✅ Certificado válido: {info['subject']}")
            app_logger.info(f"   Válido até: {info['valid_until'][:10]}")
            app_logger.info(f"   Dias restantes: {info['days_until_expiration']}")
            
            if info['days_until_expiration'] < 30:
                app_logger.warning(f"⚠️  Certificado próximo da expiração!")
        else:
            app_logger.warning("⚠️  Certificado não configurado ou inválido")
            app_logger.info("   Configure CERTIFICATE_PATH e CERTIFICATE_PASSWORD no .env")
    
    except Exception as e:
        app_logger.warning(f"⚠️  Erro ao verificar certificado: {e}")


def check_environment():
    """Verifica variáveis de ambiente."""
    app_logger.info("Verificando configurações do ambiente...")
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'NFSE_API_BASE_URL',
        'ADMIN_PASSWORD_HASH'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not hasattr(settings, var) or not getattr(settings, var):
            missing_vars.append(var)
    
    if missing_vars:
        app_logger.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        app_logger.info("   Copie .env.example para .env e configure os valores")
        sys.exit(1)
    
    app_logger.info("✅ Todas as variáveis de ambiente configuradas")


def create_directories():
    """Cria diretórios necessários."""
    directories = [
        settings.base_dir / 'logs',
        settings.base_dir / 'certs',
        settings.base_dir / 'uploads',
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        app_logger.debug(f"Diretório criado/verificado: {directory}")


async def main():
    """Função principal de inicialização."""
    app_logger.info("=" * 60)
    app_logger.info("🚀 Inicializando Sistema de Automação NFS-e")
    app_logger.info("=" * 60)
    
    try:
        # 1. Criar diretórios
        create_directories()
        
        # 2. Verificar ambiente
        check_environment()
        
        # 3. Inicializar banco de dados
        await initialize_database()
        
        # 4. Verificar certificado
        check_certificate()
        
        app_logger.info("=" * 60)
        app_logger.info("✅ Sistema inicializado com sucesso!")
        app_logger.info("=" * 60)
        app_logger.info("")
        app_logger.info("Para iniciar a aplicação, execute:")
        app_logger.info("  streamlit run app.py")
        app_logger.info("")
        
    except Exception as e:
        app_logger.error(f"❌ Erro durante inicialização: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

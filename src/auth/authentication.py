"""
Sistema de autenticação para a aplicação Streamlit.
"""
import bcrypt
from typing import Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt

from config.settings import settings
from src.utils.logger import app_logger


class AuthenticationManager:
    """Gerencia autenticação de usuários."""
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha corresponde ao hash armazenado.
        
        Args:
            plain_password: Senha em texto puro
            hashed_password: Hash bcrypt da senha
            
        Returns:
            True se corresponder, False caso contrário
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            app_logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """
        Gera hash bcrypt de uma senha.
        
        Args:
            password: Senha em texto puro
            
        Returns:
            Hash bcrypt da senha
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Autentica um usuário.
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            True se autenticado, False caso contrário
        """
        # Verifica credenciais (admin hardcoded - em produção, use BD)
        if username != settings.ADMIN_USERNAME:
            app_logger.warning(f"Tentativa de login com usuário inválido: {username}")
            return False
        
        is_valid = self.verify_password(password, settings.ADMIN_PASSWORD_HASH)
        
        if is_valid:
            app_logger.info(f"Usuário autenticado com sucesso: {username}")
        else:
            app_logger.warning(f"Senha incorreta para usuário: {username}")
        
        return is_valid
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria um token JWT.
        
        Args:
            data: Dados a serem incluídos no token
            expires_delta: Tempo de expiração customizado
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.ALGORITHM)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica e decodifica um token JWT.
        
        Args:
            token: Token JWT
            
        Returns:
            Dados do token ou None se inválido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])
            return payload
        except JWTError as e:
            app_logger.warning(f"Token inválido: {e}")
            return None
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        Realiza login e retorna token.
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            Token JWT ou None se falhar
        """
        if self.authenticate_user(username, password):
            token = self.create_access_token({"sub": username})
            return token
        
        return None


# Instância global
auth_manager = AuthenticationManager()

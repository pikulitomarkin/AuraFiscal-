"""
Validadores de documentos brasileiros e outros dados.
"""
import re
from typing import Optional
from validate_docbr import CPF, CNPJ


class DocumentValidator:
    """Classe para validação de documentos brasileiros."""
    
    def __init__(self):
        self.cpf_validator = CPF()
        self.cnpj_validator = CNPJ()
    
    def validate_cpf(self, cpf: str) -> bool:
        """
        Valida um CPF brasileiro.
        
        Args:
            cpf: CPF a ser validado (com ou sem formatação)
            
        Returns:
            True se válido, False caso contrário
        """
        if not cpf:
            return False
        
        # Remove formatação
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        
        return self.cpf_validator.validate(cpf_clean)
    
    def validate_cnpj(self, cnpj: str) -> bool:
        """
        Valida um CNPJ brasileiro.
        
        Args:
            cnpj: CNPJ a ser validado (com ou sem formatação)
            
        Returns:
            True se válido, False caso contrário
        """
        if not cnpj:
            return False
        
        # Remove formatação
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        
        return self.cnpj_validator.validate(cnpj_clean)
    
    def format_cpf(self, cpf: str) -> Optional[str]:
        """
        Formata um CPF (123.456.789-00).
        
        Args:
            cpf: CPF não formatado
            
        Returns:
            CPF formatado ou None se inválido
        """
        if not self.validate_cpf(cpf):
            return None
        
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        return self.cpf_validator.mask(cpf_clean)
    
    def format_cnpj(self, cnpj: str) -> Optional[str]:
        """
        Formata um CNPJ (12.345.678/0001-00).
        
        Args:
            cnpj: CNPJ não formatado
            
        Returns:
            CNPJ formatado ou None se inválido
        """
        if not self.validate_cnpj(cnpj):
            return None
        
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        return self.cnpj_validator.mask(cnpj_clean)
    
    @staticmethod
    def clean_document(document: str) -> str:
        """
        Remove formatação de um documento (CPF/CNPJ).
        
        Args:
            document: Documento formatado
            
        Returns:
            Documento apenas com números
        """
        return re.sub(r'[^0-9]', '', document)
    
    @staticmethod
    def validate_email(email: Optional[str]) -> bool:
        """
        Valida formato de email.
        
        Args:
            email: Email a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_hash(hash_value: str) -> bool:
        """
        Valida formato básico de hash (alfanumérico).
        
        Args:
            hash_value: Hash a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not hash_value or len(hash_value) < 8:
            return False
        
        # Hash deve conter apenas caracteres hexadecimais minúsculos
        return bool(re.match(r'^[a-f0-9]+$', hash_value))
    
    def normalize_cpf(self, cpf: str) -> str:
        """Remove formatação do CPF."""
        return self.clean_document(cpf)
    
    def normalize_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return self.clean_document(cnpj)
    
    def is_cpf_or_cnpj(self, document: str) -> str:
        """
        Identifica se documento é CPF ou CNPJ.
        
        Args:
            document: Documento a ser identificado
            
        Returns:
            "CPF", "CNPJ" ou "INVALID"
        """
        clean = self.clean_document(document)
        
        if len(clean) == 11 and self.validate_cpf(clean):
            return "CPF"
        elif len(clean) == 14 and self.validate_cnpj(clean):
            return "CNPJ"
        
        return "INVALID"


# Instância global
validator = DocumentValidator()

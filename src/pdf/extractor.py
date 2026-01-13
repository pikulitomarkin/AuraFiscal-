"""
Extrator de dados de PDFs para emissão de NFS-e.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber
from io import BytesIO

from src.utils.logger import app_logger
from src.utils.validators import validator


class PDFDataExtractor:
    """Extrai dados estruturados de PDFs para emissão de NFS-e."""
    
    # Patterns Regex para extração
    PATTERNS = {
        'cpf': r'\b\d{11}\b',  # CPF sem formatação (11 dígitos)
        'cnpj': r'\b\d{14}\b',  # CNPJ sem formatação (14 dígitos)
        'telefone': r'\b\d{10,11}\b',  # Telefone (10 ou 11 dígitos)
        'hash': r'PACIENTEBLIS\w+',  # Hash do paciente
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
        'valor': r'R\$\s*\d+[,.]?\d*',  # Valor monetário
        'data': r'\d{2}/\d{2}/\d{4}',  # Data formato DD/MM/YYYY
    }
    
    def __init__(self):
        self.errors: List[str] = []
    
    def extract_from_file(self, file_path: Path) -> List[Dict[str, str]]:
        """
        Extrai dados de um arquivo PDF local.
        
        Args:
            file_path: Caminho para o arquivo PDF
            
        Returns:
            Lista de dicionários com os dados extraídos
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return self._process_pdf(pdf)
        except Exception as e:
            error_msg = f"Erro ao processar arquivo {file_path}: {e}"
            app_logger.error(error_msg)
            self.errors.append(error_msg)
            return []
    
    def extract_from_bytes(self, file_bytes: bytes) -> List[Dict[str, str]]:
        """
        Extrai dados de bytes de um PDF (útil para uploads Streamlit).
        
        Args:
            file_bytes: Bytes do arquivo PDF
            
        Returns:
            Lista de dicionários com os dados extraídos
        """
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                return self._process_pdf(pdf)
        except Exception as e:
            error_msg = f"Erro ao processar PDF: {e}"
            app_logger.error(error_msg)
            self.errors.append(error_msg)
            return []
    
    def _process_pdf(self, pdf) -> List[Dict[str, str]]:
        """
        Processa todas as páginas do PDF e extrai dados.
        
        Args:
            pdf: Objeto pdfplumber PDF
            
        Returns:
            Lista de registros extraídos
        """
        all_records = []
        
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            
            if not text:
                app_logger.warning(f"Página {page_num} sem texto extraível")
                continue
            
            records = self._extract_records_from_text(text, page_num)
            all_records.extend(records)
        
        app_logger.info(f"Total de {len(all_records)} registros extraídos do PDF")
        return all_records
    
    def _extract_records_from_text(self, text: str, page_num: int) -> List[Dict[str, str]]:
        """
        Extrai registros de uma página de texto.
        Formato esperado: Hash | Nome do Paciente | CPF | Telefone | Email | Endereço | Data Consulta | Valor | Criação
        
        Args:
            text: Texto extraído da página
            page_num: Número da página
            
        Returns:
            Lista de registros
        """
        records = []
        lines = text.split('\n')
        
        for line in lines:
            # Pular linhas vazias e cabeçalhos
            if not line.strip() or 'Nome do Paciente' in line or ('Hash' in line and 'CPF' in line):
                continue
            
            # Verificar se linha contém hash de paciente
            if 'PACIENTEBLIS' not in line:
                continue
            
            try:
                # Extrair componentes usando regex
                hash_match = re.search(self.PATTERNS['hash'], line)
                email_match = re.search(self.PATTERNS['email'], line)
                cpf_matches = re.findall(self.PATTERNS['cpf'], line)
                telefone_matches = re.findall(self.PATTERNS['telefone'], line)
                data_matches = re.findall(self.PATTERNS['data'], line)
                
                if not hash_match or not cpf_matches:
                    continue
                
                hash_id = hash_match.group()
                cpf = cpf_matches[0]  # Primeiro CPF encontrado
                
                # Validar CPF - se inválido, tenta validar como CNPJ
                cpf_valido = False
                try:
                    cpf_valido = validator.validate_cpf(cpf)
                except Exception:
                    cpf_valido = False
                
                if not cpf_valido:
                    app_logger.warning(f"CPF inválido encontrado: {cpf}")
                    # Continua mesmo assim, pode ser CNPJ ou formato especial
                
                # Extrair nome (texto entre hash e CPF)
                hash_pos = line.find(hash_id)
                cpf_pos = line.find(cpf)
                
                nome = "Nome não encontrado"
                if hash_pos < cpf_pos:
                    nome_parte = line[hash_pos + len(hash_id):cpf_pos].strip()
                    # Limpar e extrair apenas palavras válidas (nomes)
                    nome_palavras = []
                    for palavra in nome_parte.split():
                        # Ignorar números e palavras muito curtas
                        if not palavra.isdigit() and len(palavra) > 2:
                            # Remover números das palavras
                            palavra_limpa = ''.join([c for c in palavra if not c.isdigit()])
                            if palavra_limpa:
                                nome_palavras.append(palavra_limpa)
                    
                    if nome_palavras:
                        nome = ' '.join(nome_palavras)
                
                # Telefone - pegar o que não for CPF e tiver 10-11 dígitos
                telefone = None
                for tel in telefone_matches:
                    if tel != cpf and len(tel) >= 10:
                        telefone = tel
                        break
                
                # Email
                email = email_match.group() if email_match else None
                
                # Data da consulta (primeira data encontrada)
                data_consulta = data_matches[0] if data_matches else None
                
                # NOTA: Valor do PDF é ignorado - será usado o valor configurado no formulário
                
                # Formatar CPF com tratamento de erro
                cpf_formatado = cpf
                try:
                    cpf_formatado = validator.format_cpf(cpf)
                except Exception:
                    cpf_formatado = cpf
                
                # Criar registro
                record = {
                    'hash': hash_id,
                    'nome': nome,
                    'cpf': cpf,
                    'cpf_formatado': cpf_formatado,
                    'email': email if email else None,
                    'telefone': telefone if telefone else None,
                    'data_consulta': data_consulta,
                    'page': page_num,
                    'valido': True,
                    # Valor será definido no formulário (não extrai do PDF)
                }
                
                records.append(record)
                app_logger.debug(f"Registro extraído: {nome} - CPF {cpf}")
                
            except Exception as e:
                app_logger.error(f"Erro ao processar linha '{line[:50]}...': {e}")
                continue
        
        return records
    
    def _extract_cpfs(self, text: str) -> List[str]:
        """Extrai todos os CPFs do texto."""
        matches = re.findall(self.PATTERNS['cpf'], text)
        # Remove formatação
        return [validator.clean_document(cpf) for cpf in matches]
    
    def _extract_hashes(self, text: str) -> List[str]:
        """Extrai todos os hashes do texto."""
        matches = re.findall(self.PATTERNS['hash'], text)
        return matches
    
    def _extract_names(self, text: str) -> List[str]:
        """Extrai nomes de clientes do texto."""
        matches = re.findall(self.PATTERNS['nome'], text, re.IGNORECASE)
        return [name.strip() for name in matches]
    
    def validate_extracted_data(self, records: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Valida os dados extraídos e retorna estatísticas.
        
        Args:
            records: Lista de registros extraídos
            
        Returns:
            Dicionário com estatísticas
        """
        total = len(records)
        validos = sum(1 for r in records if r['valido'])
        invalidos = total - validos
        sem_hash = sum(1 for r in records if r['hash'] == 'Hash não encontrado')
        sem_nome = sum(1 for r in records if r['nome'] == 'Nome não encontrado')
        
        stats = {
            'total_registros': total,
            'registros_validos': validos,
            'registros_invalidos': invalidos,
            'sem_hash': sem_hash,
            'sem_nome': sem_nome,
            'taxa_sucesso': (validos / total * 100) if total > 0 else 0
        }
        
        app_logger.info(f"Validação: {validos}/{total} registros válidos ({stats['taxa_sucesso']:.1f}%)")
        
        return stats
    
    def filter_valid_records(self, records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filtra apenas registros válidos e completos.
        
        Args:
            records: Lista de todos os registros
            
        Returns:
            Lista apenas com registros válidos
        """
        valid = [
            r for r in records 
            if r['valido'] 
            and r['hash'] != 'Hash não encontrado'
            and r['nome'] != 'Nome não encontrado'
        ]
        
        app_logger.info(f"{len(valid)}/{len(records)} registros passaram no filtro de validação")
        
        return valid


# Instância global
pdf_extractor = PDFDataExtractor()

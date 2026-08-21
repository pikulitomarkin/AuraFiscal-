"""
Extrator de dados de PDFs para emissão de NFS-e.
Suporta o formato de tabela: Hash | Nome | CPF | Telefone | Email | Endereço | Data Consulta | Valor | Criação
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
        'cpf': r'\b\d{11}\b',
        'cnpj': r'\b\d{14}\b',
        'telefone': r'\b\d{10,11}\b',
        'hash': r'PACIENTEBLIS\w+',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'valor': r'R\$\s*[\d.,]+',
        'data': r'\d{2}/\d{2}/\d{4}',
    }

    # Índices esperados das colunas na tabela
    COL_HASH = 0
    COL_NOME = 1
    COL_CPF = 2
    COL_TELEFONE = 3
    COL_EMAIL = 4
    COL_ENDERECO = 5
    COL_DATA_CONSULTA = 6
    COL_VALOR = 7

    def __init__(self):
        self.errors: List[str] = []

    def extract_from_file(self, file_path: Path) -> List[Dict[str, str]]:
        try:
            with pdfplumber.open(file_path) as pdf:
                return self._process_pdf(pdf)
        except Exception as e:
            error_msg = f"Erro ao processar arquivo {file_path}: {e}"
            app_logger.error(error_msg)
            self.errors.append(error_msg)
            return []

    def extract_from_bytes(self, file_bytes: bytes) -> List[Dict[str, str]]:
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                return self._process_pdf(pdf)
        except Exception as e:
            error_msg = f"Erro ao processar PDF: {e}"
            app_logger.error(error_msg)
            self.errors.append(error_msg)
            return []

    def _process_pdf(self, pdf) -> List[Dict[str, str]]:
        all_records = []
        for page_num, page in enumerate(pdf.pages, start=1):
            # Tenta extração por tabela primeiro (mais confiável para PDFs com colunas)
            records = self._extract_via_table(page, page_num)
            if not records:
                # Fallback: extração por texto
                text = page.extract_text()
                if text:
                    records = self._extract_via_text(text, page_num)
            all_records.extend(records)

        app_logger.info(f"Total de {len(all_records)} registros extraídos do PDF")
        return all_records

    def _extract_via_table(self, page, page_num: int) -> List[Dict[str, str]]:
        """Extrai dados usando detecção de tabela do pdfplumber."""
        records = []
        try:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                # Mescla linhas de continuação (nome quebrado em múltiplas linhas)
                merged = self._merge_continuation_rows(table)
                for row in merged:
                    record = self._parse_table_row(row, page_num)
                    if record:
                        records.append(record)
        except Exception as e:
            app_logger.debug(f"Extração por tabela falhou na página {page_num}: {e}")
        return records

    def _merge_continuation_rows(self, table: list) -> list:
        """
        Mescla linhas de continuação onde o nome do paciente quebra em mais de uma linha.
        Uma linha de continuação é aquela que NÃO contém hash na primeira célula nem no texto completo.
        """
        merged = []
        for row in table:
            if not row:
                continue
            cells = [str(c or '').strip() for c in row]
            row_text = ' '.join(cells)

            if re.search(self.PATTERNS['hash'], row_text):
                # Nova linha principal com hash
                merged.append(list(cells))
            elif merged:
                # Linha de continuação: mescla a célula do nome (COL_NOME) com a anterior
                prev = merged[-1]
                # Tenta encontrar qual célula tem conteúdo para mesclar
                for i, cell in enumerate(cells):
                    if cell and i < len(prev):
                        # Só mescla células de texto (não números/datas)
                        if not re.match(r'^[\d/\s.,R$]*$', cell):
                            prev[i] = (prev[i] + ' ' + cell).strip()
        return merged

    def _parse_table_row(self, row: list, page_num: int) -> Optional[Dict]:
        """Tenta extrair um registro de uma linha de tabela."""
        if not row or len(row) < 3:
            return None

        # Junta células None como string vazia e remove quebras de linha internas
        cells = [str(c or '').replace('\n', ' ').strip() for c in row]

        # Verifica se há hash na linha inteira ou na primeira célula
        row_text = ' '.join(cells)
        hash_match = re.search(self.PATTERNS['hash'], row_text)
        if not hash_match:
            return None

        hash_id = hash_match.group()

        # CPF: 11 dígitos
        cpf = None
        for cell in cells:
            m = re.search(self.PATTERNS['cpf'], cell.replace('.', '').replace('-', ''))
            if m:
                cpf = m.group()
                break
        if not cpf:
            return None

        # Nome: célula após o hash (ou a que contiver texto sem dígitos)
        nome = self._extrair_nome_das_celulas(cells, hash_id)

        # Telefone
        telefone = None
        for cell in cells:
            digits = re.sub(r'\D', '', cell)
            if len(digits) in (10, 11) and digits != cpf:
                telefone = digits
                break

        # Email
        email = None
        email_m = re.search(self.PATTERNS['email'], row_text)
        if email_m:
            email = email_m.group()

        # Datas
        datas = re.findall(self.PATTERNS['data'], row_text)
        data_consulta = datas[0] if datas else None

        # Valor
        valor = self._parse_valor(row_text)

        return self._build_record(hash_id, nome, cpf, telefone, email, data_consulta, valor, page_num)

    def _extrair_nome_das_celulas(self, cells: list, hash_id: str) -> str:
        """Extrai o nome do paciente das células da linha."""
        # Tenta célula COL_NOME primeiro
        if len(cells) > self.COL_NOME:
            nome_cell = cells[self.COL_NOME]
            # Célula do nome não deve ter só dígitos nem o hash
            if nome_cell and hash_id not in nome_cell and not nome_cell.isdigit():
                nome_limpo = re.sub(r'\d', '', nome_cell).strip()
                if len(nome_limpo) > 3:
                    return nome_limpo

        # Fallback: busca célula que parece nome (só letras e espaços, > 5 chars)
        for cell in cells:
            if hash_id in cell:
                continue
            if re.match(r'^[A-Za-zÀ-ÿ\s]{5,}$', cell.strip()):
                return cell.strip()

        return "Nome não encontrado"

    def _extract_via_text(self, text: str, page_num: int) -> List[Dict[str, str]]:
        """Fallback: extração linha a linha do texto bruto."""
        records = []
        lines = text.split('\n')

        # Agrupa linhas: linha principal (com hash) + continuações (nome quebrado)
        grupos = []   # lista de (linha_principal, [continuações_nome])
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if 'PACIENTEBLIS' in line:
                grupos.append([line, []])
            elif grupos:
                # Continuação de nome: linha com APENAS letras/espaços (sem dígitos, @, R$)
                if re.match(r'^[A-Za-zÀ-ÿ\s]{2,}$', stripped):
                    grupos[-1][1].append(stripped)

        for linha_principal, continuacoes in grupos:
            record = self._parse_text_group(linha_principal, continuacoes, page_num)
            if record:
                records.append(record)

        return records

    def _parse_text_group(self, text: str, continuacoes: list, page_num: int) -> Optional[Dict]:
        """Extrai um registro de uma linha principal + continuações de nome."""
        hash_match = re.search(self.PATTERNS['hash'], text)
        if not hash_match:
            return None

        hash_id = hash_match.group()

        cpf_matches = re.findall(self.PATTERNS['cpf'], text)
        if not cpf_matches:
            return None
        cpf = cpf_matches[0]

        # Nome: texto entre o hash e o CPF
        hash_pos = text.find(hash_id)
        cpf_pos = text.find(cpf)
        nome = "Nome não encontrado"
        if hash_pos >= 0 and cpf_pos > hash_pos:
            trecho = text[hash_pos + len(hash_id):cpf_pos].strip()
            nome_palavras = [p for p in trecho.split() if not p.isdigit() and len(p) > 1]
            if nome_palavras:
                nome = ' '.join(nome_palavras)

        # Adiciona continuações de nome (ex: "Oliveira", "da Cruz", "Carlos Luna")
        if continuacoes:
            nome = (nome + ' ' + ' '.join(continuacoes)).strip()

        # Telefone
        telefone = None
        tel_matches = re.findall(self.PATTERNS['telefone'], text)
        for tel in tel_matches:
            if tel != cpf and len(tel) >= 10:
                telefone = tel
                break

        # Email
        email_match = re.search(self.PATTERNS['email'], text)
        email = email_match.group() if email_match else None

        # Data
        datas = re.findall(self.PATTERNS['data'], text)
        data_consulta = datas[0] if datas else None

        # Valor
        valor = self._parse_valor(text)

        return self._build_record(hash_id, nome, cpf, telefone, email, data_consulta, valor, page_num)

    def _parse_valor(self, text: str) -> Optional[float]:
        """Extrai valor monetário do texto."""
        m = re.search(self.PATTERNS['valor'], text)
        if not m:
            return None
        valor_str = m.group().replace('R$', '').strip()
        if ',' in valor_str:
            valor_str = valor_str.replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except ValueError:
            return None

    def _build_record(self, hash_id, nome, cpf, telefone, email, data_consulta, valor, page_num) -> Optional[Dict]:
        """Constrói e valida o dicionário de registro."""
        cpf_formatado = cpf
        try:
            cpf_formatado = validator.format_cpf(cpf)
        except Exception:
            pass

        record = {
            'hash': hash_id,
            'nome': nome,
            'cpf': cpf,
            'cpf_formatado': cpf_formatado,
            'email': email,
            'telefone': telefone,
            'data_consulta': data_consulta,
            'valor': valor,
            'page': page_num,
            'valido': True,
        }
        app_logger.debug(f"Registro extraído: {nome} | CPF: {cpf} | Hash: {hash_id} | Valor: {valor}")
        return record

    def validate_extracted_data(self, records: List[Dict[str, str]]) -> Dict[str, any]:
        total = len(records)
        validos = sum(1 for r in records if r['valido'])
        invalidos = total - validos
        sem_hash = sum(1 for r in records if not r.get('hash'))
        sem_nome = sum(1 for r in records if r.get('nome') == 'Nome não encontrado')

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
        valid = [
            r for r in records
            if r['valido']
            and r.get('hash')
            and r.get('nome') != 'Nome não encontrado'
        ]
        app_logger.info(f"{len(valid)}/{len(records)} registros passaram no filtro de validação")
        return valid


# Instância global
pdf_extractor = PDFDataExtractor()

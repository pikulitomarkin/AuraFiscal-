"""
Schemas Pydantic para validação de dados da API NFS-e Nacional (ADN).
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ==================== Modelos API ADN Oficial ====================

class TipoAmbiente(str, Enum):
    """Tipo de ambiente para emissão."""
    PRODUCAO = "PRODUCAO"
    HOMOLOGACAO = "HOMOLOGACAO"


class MensagemProcessamento(BaseModel):
    """Mensagem de erro ou alerta retornada pela API."""
    Codigo: Optional[str] = None
    Descricao: Optional[str] = None
    Complemento: Optional[str] = None
    Parametros: Optional[List[str]] = None


class RecepcaoRequest(BaseModel):
    """Request para recepção de lote de documentos na API ADN."""
    LoteXmlGZipB64: List[str] = Field(
        ...,
        description="Array de XMLs NFS-e comprimidos em GZIP e codificados em Base64"
    )


class RecepcaoResponseDocumento(BaseModel):
    """Resposta individual de um documento processado."""
    ChaveAcesso: Optional[str] = Field(None, description="Chave de acesso da NFS-e")
    NsuRecepcao: Optional[str] = Field(None, description="NSU - Número Sequencial de Recepção")
    StatusProcessamento: Optional[str] = Field(None, description="Status do processamento")
    Alertas: Optional[List[MensagemProcessamento]] = Field(default_factory=list)
    Erros: Optional[List[MensagemProcessamento]] = Field(default_factory=list)


class RecepcaoResponseLote(BaseModel):
    """Resposta da recepção de lote de documentos."""
    Lote: Optional[List[RecepcaoResponseDocumento]] = Field(default_factory=list)
    TipoAmbiente: TipoAmbiente
    VersaoAplicativo: Optional[str] = None
    DataHoraProcessamento: datetime


class ProblemDetails(BaseModel):
    """Detalhes de erro HTTP retornado pela API."""
    type: Optional[str] = None
    title: Optional[str] = None
    status: Optional[int] = None
    detail: Optional[str] = None
    instance: Optional[str] = None
    errors: Optional[dict] = None


# ==================== Modelos Originais (para geração de XML) ====================


class TomadorServico(BaseModel):
    """Dados do tomador do serviço (cliente)."""
    
    cpf: Optional[str] = Field(None, description="CPF do tomador (sem formatação)")
    cnpj: Optional[str] = Field(None, description="CNPJ do tomador (sem formatação)")
    nome: str = Field(..., min_length=3, max_length=150, description="Nome/Razão Social")
    email: Optional[str] = Field(None, description="Email do tomador")
    telefone: Optional[str] = Field(None, description="Telefone do tomador")
    
    # Endereço
    logradouro: Optional[str] = Field(None, max_length=125)
    numero: Optional[str] = Field(None, max_length=10)
    complemento: Optional[str] = Field(None, max_length=60)
    bairro: Optional[str] = Field(None, max_length=60)
    municipio: Optional[str] = Field(None, max_length=60)
    uf: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=8, description="CEP sem formatação")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "12345678900",
                "nome": "João da Silva",
                "email": "joao@email.com",
                "logradouro": "Rua das Flores",
                "numero": "123",
                "bairro": "Centro",
                "municipio": "São Paulo",
                "uf": "SP",
                "cep": "01234567"
            }
        }
    )
    
    @field_validator('cpf', 'cnpj')
    @classmethod
    def validate_document(cls, v):
        """Valida que ao menos um documento foi fornecido."""
        if v:
            return v.replace('.', '').replace('-', '').replace('/', '')
        return v


class Servico(BaseModel):
    """Dados do serviço prestado."""
    
    descricao: str = Field(..., min_length=10, max_length=2000, description="Descrição do serviço")
    valor_servico: Decimal = Field(..., gt=0, description="Valor do serviço em reais")
    valor_deducoes: Optional[Decimal] = Field(Decimal(0), ge=0, description="Valor das deduções")
    
    # Tributação
    aliquota_iss: Decimal = Field(..., ge=0, le=5, description="Alíquota ISS em %")
    valor_iss: Optional[Decimal] = Field(None, ge=0, description="Valor do ISS (calculado)")
    
    # Retenções federais
    aliquota_pis: Optional[Decimal] = Field(Decimal(0), ge=0)
    aliquota_cofins: Optional[Decimal] = Field(Decimal(0), ge=0)
    aliquota_inss: Optional[Decimal] = Field(Decimal(0), ge=0)
    aliquota_ir: Optional[Decimal] = Field(Decimal(0), ge=0)
    aliquota_csll: Optional[Decimal] = Field(Decimal(0), ge=0)
    
    # Códigos de serviço
    item_lista_servico: str = Field(..., description="Item da lista de serviços (LC 116/2003)")
    codigo_cnae: Optional[str] = Field(None, description="Código CNAE")
    codigo_tributacao_municipio: Optional[str] = Field(None, description="Código tributação municipal")
    
    # Outras informações
    discriminacao: Optional[str] = Field(None, max_length=2000, description="Discriminação adicional")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descricao": "Serviços de consultoria em tecnologia",
                "valor_servico": "1000.00",
                "aliquota_iss": "2.5",
                "item_lista_servico": "1.09",
                "discriminacao": "Consultoria especializada em desenvolvimento de software"
            }
        }
    )
    
    @field_validator('valor_iss')
    @classmethod
    def calculate_iss(cls, v, info):
        """Calcula o valor do ISS se não fornecido."""
        if v is None:
            data = info.data
            if 'valor_servico' in data and 'aliquota_iss' in data:
                base_calculo = data['valor_servico'] - data.get('valor_deducoes', Decimal(0))
                return base_calculo * (data['aliquota_iss'] / 100)
        return v


class PrestadorServico(BaseModel):
    """Dados do prestador do serviço (emissor)."""
    
    cnpj: str = Field(..., description="CNPJ do prestador (sem formatação)")
    inscricao_municipal: Optional[str] = Field(None, description="Inscrição Municipal")
    razao_social: str = Field(..., min_length=3, max_length=150)
    nome_fantasia: Optional[str] = Field(None, max_length=60)
    
    # Endereço
    logradouro: str = Field(..., max_length=125)
    numero: str = Field(..., max_length=10)
    complemento: Optional[str] = Field(None, max_length=60)
    bairro: str = Field(..., max_length=60)
    municipio: str = Field(..., max_length=60)
    uf: str = Field(..., max_length=2)
    cep: str = Field(..., max_length=8)
    
    # Contato
    email: Optional[str] = None
    telefone: Optional[str] = None
    
    @field_validator('cnpj')
    @classmethod
    def clean_cnpj(cls, v):
        """Remove formatação do CNPJ."""
        return v.replace('.', '').replace('-', '').replace('/', '')


class NFSeRequest(BaseModel):
    """Payload completo para emissão de NFS-e."""
    
    # Identificação
    numero_nfse: Optional[str] = Field(None, description="Número da NFS-e (gerado pela API)")
    data_emissao: datetime = Field(default_factory=datetime.now, description="Data de emissão")
    competencia: date = Field(default_factory=date.today, description="Competência (mês/ano)")
    
    # Entidades
    prestador: PrestadorServico
    tomador: Optional[TomadorServico] = None
    servico: Servico
    
    # Informações adicionais
    natureza_operacao: int = Field(1, ge=1, le=6, description="1=Tributação no município")
    regime_especial_tributacao: Optional[int] = Field(None, description="Regime especial")
    optante_simples_nacional: bool = Field(False, description="Optante pelo Simples Nacional")
    incentivador_cultural: bool = Field(False, description="Incentivador cultural")
    
    # Controle interno
    hash_transacao: Optional[str] = Field(None, description="Hash da transação (rastreamento)")
    outras_informacoes: Optional[str] = Field(None, max_length=255)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prestador": {
                    "cnpj": "12345678000190",
                    "inscricao_municipal": "123456",
                    "razao_social": "Empresa Prestadora LTDA",
                    "logradouro": "Av. Principal",
                    "numero": "1000",
                    "bairro": "Centro",
                    "municipio": "São Paulo",
                    "uf": "SP",
                    "cep": "01310000"
                },
                "tomador": {
                    "cpf": "12345678900",
                    "nome": "João da Silva"
                },
                "servico": {
                    "descricao": "Consultoria em TI",
                    "valor_servico": "1500.00",
                    "aliquota_iss": "2.0",
                    "item_lista_servico": "1.09"
                },
                "hash_transacao": "abc123def456"
            }
        }
    )


class NFSeResponse(BaseModel):
    """Resposta da API após emissão de NFS-e."""
    
    sucesso: bool = Field(..., description="Indica se a emissão foi bem-sucedida")
    numero_nfse: Optional[str] = Field(None, description="Número da NFS-e emitida")
    codigo_verificacao: Optional[str] = Field(None, description="Código de verificação")
    protocolo: Optional[str] = Field(None, description="Protocolo de recepção")
    data_processamento: Optional[datetime] = Field(None, description="Data de processamento")
    
    # URL para consulta/visualização
    url_nfse: Optional[str] = Field(None, description="URL para visualizar a NFS-e")
    
    # Erros
    mensagem_erro: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    codigo_erro: Optional[str] = Field(None, description="Código do erro")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": True,
                "numero_nfse": "202301001",
                "codigo_verificacao": "A1B2C3D4",
                "protocolo": "PROT2023010112345",
                "url_nfse": "https://nfse.gov.br/consulta/202301001"
            }
        }
    )


class ProcessingResult(BaseModel):
    """Resultado do processamento em lote."""
    
    hash_transacao: str
    cpf_tomador: str
    nome_tomador: str
    status: str = Field(..., description="sucesso, erro, pendente")
    numero_nfse: Optional[str] = None
    protocolo: Optional[str] = None
    mensagem: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

"""
Configuração do cliente RoboFiscal — Matheus Costa Serviços Médicos (Tubarão-SC).

Canais: ClickCannabis e Bliss (mesmo CNPJ/prestador; descrição e prefixo de hash diferem).
"""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CanalEmissao:
    id: str
    label: str
    descricao_servico: str
    prefixo_hash: str


# Prestador
PRESTADOR_CNPJ = "53380857000140"
PRESTADOR_IM = "89944"
PRESTADOR_RAZAO_SOCIAL = "MATHEUS COSTA SERVICOS MEDICOS LTDA"
PRESTADOR_TELEFONE = "4899501819"
PRESTADOR_EMAIL = "KAROLINA@LOMAX.NET.BR"
PRESTADOR_LOGRADOURO = "RUA ALMIR DOS SANTOS MIRANDA"
PRESTADOR_NUMERO = "840"
PRESTADOR_BAIRRO = "DEHON"
PRESTADOR_MUNICIPIO = "Tubarao"
PRESTADOR_UF = "SC"
PRESTADOR_CEP = "88704261"
PRESTADOR_CODIGO_IBGE = "4218707"  # Tubarão-SC

# DPS / tributação
DPS_SERIE = "70000"  # 5 dígitos (conforme DANFSe emitidas)
ITEM_LISTA_SERVICO = "04.01.01"  # Medicina
CODIGO_NBS = "1.2301.21.00"  # NBS clínica médica → XML cNBS=123012100
# opSimpNac: 1=Não optante, 2=Optante SN (ME/EPP), 3=MEI
OP_SIMP_NAC = "2"
# regApTribSN: 1=Caixa, 2=Competência (tributos federais e municipal pelo SN)
REG_AP_TRIB_SN = "2"  # 2=Competência (padrão serviços; editável via settings se necessário)
ALIQUOTA_ISS_PADRAO = 2.0  # editável na UI; DANFSe de referência não exibia %

CANAIS: Dict[str, CanalEmissao] = {
    "clickcannabis": CanalEmissao(
        id="clickcannabis",
        label="ClickCannabis",
        descricao_servico="Ref. a consulta pela clickcannabis",
        prefixo_hash="PACIENTECLICK",
    ),
    "bliss": CanalEmissao(
        id="bliss",
        label="Bliss",
        descricao_servico="Ref. a consulta pela bliss",
        prefixo_hash="PACIENTEBLIS",
    ),
}


def nbs_para_xml(codigo_nbs: str = CODIGO_NBS) -> str:
    """Converte NBS com pontos para cNBS de 9 dígitos."""
    digits = "".join(ch for ch in codigo_nbs if ch.isdigit())
    return digits.zfill(9)[:9]

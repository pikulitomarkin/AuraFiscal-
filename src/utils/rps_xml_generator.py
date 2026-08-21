"""
Gerador de XML NFS-e no formato IPM/Atende.Net (NTE-35/2021).
Prefeitura de Santa Rosa-RS - REST multipart/form-data.
Estrutura validada contra o servidor da Prefeitura.

Blocos obrigatórios para nova emissão:
  <rps>  - dados do RPS (serie_recibo_provisorio deve ser inteiro)
  <nf>   - dados da NFS-e (SEM <situacao> para nova emissão; apenas para cancelamento usa <situacao>C</situacao>)
  <prestador>, <tomador>, <itens>
"""
from datetime import datetime
from typing import Optional


# TOM code para Santa Rosa-RS (código de município IPM, não IBGE)
CIDADE_SANTA_ROSA_TOM = "8847"


def _fmt(valor: float) -> str:
    """Formata valor decimal com vírgula (padrão IPM)."""
    return f"{valor:.2f}".replace(".", ",")


def _fmt4(valor: float) -> str:
    """Formata alíquota com 4 casas decimais e vírgula."""
    return f"{valor:.4f}".replace(".", ",")


class RPSXMLGenerator:
    """Gera XMLs de NFS-e no formato proprietário IPM/Atende.Net (NTE-35/2021)."""

    def __init__(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ambiente_teste: bool = True,
    ):
        # cert/key não são usados no IPM (autenticação via Basic Auth)
        self.cert_path = cert_path
        self.key_path = key_path
        self.ambiente_teste = ambiente_teste

    def gerar_enviar_lote_rps_sincrono(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        numero_lote: int,
        numero_rps: int,
        serie_rps: str,
        cpf_tomador: str,
        nome_tomador: str,
        descricao: str,
        valor: float,
        aliquota_iss: float,
        codigo_servico: str = "40303",
        codigo_municipio: str = "4318002",  # IBGE (não usado internamente, usa TOM)
        cidade_tomador: str = CIDADE_SANTA_ROSA_TOM,
        bairro_tomador: str = "NAO INFORMADO",
        cep_tomador: str = "00000000",
        logradouro_tomador: str = "NAO INFORMADO",
    ) -> str:
        """
        Gera o XML no formato IPM/Atende.Net pronto para envio via multipart/form-data.
        Estrutura validada contra o servidor: <rps> + <nf> (sem <situacao>) + <prestador> + <tomador> + <itens>.
        """
        nfse_teste = "1" if self.ambiente_teste else "0"
        agora = datetime.now()
        data_str = agora.strftime("%d/%m/%Y")
        hora_str = agora.strftime("%H:%M:%S")

        # série do RPS deve ser inteiro no IPM
        try:
            serie_int = int(serie_rps)
        except (ValueError, TypeError):
            # Converte letra para número (A=1, B=2, ...)
            serie_int = ord(str(serie_rps).upper()[0]) - ord('A') + 1

        # Tipo do tomador: F=pessoa física (CPF 11 dígitos), J=jurídica
        cpf_clean = cpf_tomador.replace(".", "").replace("-", "").replace("/", "")
        tipo_tomador = "F" if len(cpf_clean) == 11 else "J"

        # CEP apenas numérico
        cep_clean = cep_tomador.replace("-", "").replace(".", "")
        if not cep_clean:
            cep_clean = "00000000"

        valor_fmt = _fmt(valor)
        aliquota_fmt = _fmt4(aliquota_iss)

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<nfse>
  <nfse_teste>{nfse_teste}</nfse_teste>
  <rps>
    <nro_recibo_provisorio>{numero_rps}</nro_recibo_provisorio>
    <serie_recibo_provisorio>{serie_int}</serie_recibo_provisorio>
    <data_emissao_recibo_provisorio>{data_str}</data_emissao_recibo_provisorio>
    <hora_emissao_recibo_provisorio>{hora_str}</hora_emissao_recibo_provisorio>
  </rps>
  <nf>
    <data_fato_gerador>{data_str}</data_fato_gerador>
    <valor_total>{valor_fmt}</valor_total>
    <valor_desconto>0,00</valor_desconto>
    <valor_ir>0,00</valor_ir>
    <valor_inss>0,00</valor_inss>
    <valor_contribuicao_social>0,00</valor_contribuicao_social>
    <valor_rps>0,00</valor_rps>
    <valor_pis>0,00</valor_pis>
    <valor_cofins>0,00</valor_cofins>
  </nf>
  <prestador>
    <cpfcnpj>{cnpj_prestador}</cpfcnpj>
    <cidade>{CIDADE_SANTA_ROSA_TOM}</cidade>
  </prestador>
  <tomador>
    <tipo>{tipo_tomador}</tipo>
    <cpfcnpj>{cpf_clean}</cpfcnpj>
    <nome_razao_social>{nome_tomador}</nome_razao_social>
    <logradouro>{logradouro_tomador}</logradouro>
    <bairro>{bairro_tomador}</bairro>
    <cidade>{cidade_tomador}</cidade>
    <cep>{cep_clean}</cep>
  </tomador>
  <itens>
    <lista>
      <codigo_local_prestacao_servico>{CIDADE_SANTA_ROSA_TOM}</codigo_local_prestacao_servico>
      <codigo_item_lista_servico>{codigo_servico}</codigo_item_lista_servico>
      <descritivo>{descricao}</descritivo>
      <aliquota_item_lista_servico>{aliquota_fmt}</aliquota_item_lista_servico>
      <situacao_tributaria>00</situacao_tributaria>
      <valor_tributavel>{valor_fmt}</valor_tributavel>
      <valor_deducao>0,00</valor_deducao>
      <valor_issrf>0,00</valor_issrf>
      <tributa_municipio_prestador>S</tributa_municipio_prestador>
    </lista>
  </itens>
</nfse>"""
        return xml

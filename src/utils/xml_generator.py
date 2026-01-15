"""
Gerador de XMLs NFS-e no padrão ADN (Ambiente de Disponibilização Nacional).
"""
import gzip
import base64
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from src.models.schemas import (
    TomadorServico, Servico, PrestadorServico,
    NFSeRequest, TipoAmbiente
)

try:
    from lxml import etree
    from signxml import XMLSigner, methods
    SIGNXML_AVAILABLE = True
except ImportError:
    SIGNXML_AVAILABLE = False
    etree = None
    XMLSigner = None
    methods = None


class NFSeXMLGenerator:
    """Gerador de XML NFS-e no padrão ADN."""
    
    NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
    
    def __init__(
        self, 
        ambiente: TipoAmbiente = TipoAmbiente.HOMOLOGACAO,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None
    ):
        """
        Inicializa o gerador.
        
        Args:
            ambiente: Tipo de ambiente (PRODUCAO ou HOMOLOGACAO)
            cert_path: Caminho do certificado (cert.pem) para assinatura
            key_path: Caminho da chave privada (key.pem) para assinatura
        """
        self.ambiente = ambiente
        self.cert_path = cert_path
        self.key_path = key_path
        
        # Contador de DPS (inicia aleatório para evitar duplicação)
        import random
        self._dps_counter = random.randint(1000, 9999)
        
        # Verificar se assinatura está disponível
        if not SIGNXML_AVAILABLE:
            import warnings
            warnings.warn(
                "Biblioteca 'signxml' não encontrada. Assinatura digital não disponível. "
                "Instale com: pip install signxml lxml"
            )
    
    def gerar_xml_nfse(self, nfse_request: NFSeRequest) -> str:
        """
        Gera XML DPS (Declaração de Prestação de Serviço) conforme XSD v1.01.
        
        Args:
            nfse_request: Dados da NFS-e
            
        Returns:
            XML em formato string conforme padrão nacional v1.01
        """
        # IMPORTANTE: Sefin Nacional NÃO aceita prefixos de namespace (erro E6155)
        # Usar namespace DEFAULT sem prefixo
        
        # Elemento raiz DPS com namespace DEFAULT
        root = Element("DPS")
        root.set("xmlns", self.NAMESPACE)  # xmlns sem prefixo!
        root.set("versao", "1.01")  # XSD v1.01
        
        # Elemento infDPS (obrigatório)
        inf_dps = SubElement(root, "infDPS")
        
        # Gerar ID do DPS (formato: DPS + cMunEmissor(7) + tpInscr(1) + nrInscr(14) + serie(5) + nrDPS(15) = 45 chars)
        cnpj_prestador = nfse_request.prestador.cnpj.zfill(14)
        serie_dps = "00001"  # 5 dígitos
        
        # Incrementar contador a cada emissão
        self._dps_counter += 1
        numero_dps = str(self._dps_counter).zfill(15)  # 15 dígitos para o ID
        numero_dps_element = str(self._dps_counter)  # Número SEM zeros à esquerda para o elemento nDPS
        
        id_dps = f"DPS4205407{1 if len(cnpj_prestador) == 11 else 2}{cnpj_prestador}{serie_dps}{numero_dps}"
        inf_dps.set("Id", id_dps)
        
        # ORDEM CORRETA CONFORME XSD v1.01:
        # 1. tpAmb - Tipo de Ambiente (1=Produção, 2=Homologação)
        SubElement(inf_dps, "tpAmb").text = "2" if self.ambiente.value == "HOMOLOGACAO" else "1"
        
        # 2. dhEmi - Data/Hora de Emissão
        # SEMPRE usar horário de Brasília (UTC-3) para evitar problemas com fuso horário do servidor
        from datetime import timedelta, timezone
        tz_brasilia = timezone(timedelta(hours=-3))
        now = datetime.now(tz_brasilia) - timedelta(minutes=1)  # Subtrai 1 minuto de margem de segurança
        dh_emi = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        if len(dh_emi) > 19:
            dh_emi = dh_emi[:-2] + ':' + dh_emi[-2:]
        SubElement(inf_dps, "dhEmi").text = dh_emi
        
        # 3. verAplic - Versão do aplicativo emissor
        SubElement(inf_dps, "verAplic").text = "1.0.0"
        
        # 4. serie - Série do DPS
        SubElement(inf_dps, "serie").text = serie_dps
        
        # 5. nDPS - Número do DPS (SEM zeros à esquerda!)
        SubElement(inf_dps, "nDPS").text = numero_dps_element
        
        # 6. dCompet - Data de Competência (AAAA-MM-DD)
        # IMPORTANTE: Usar a mesma data base do dhEmi para evitar erro E0015
        # (competência não pode ser posterior à emissão)
        SubElement(inf_dps, "dCompet").text = now.strftime("%Y-%m-%d")
        
        # 7. tpEmit - Tipo de Emitente (1=Prestador)
        SubElement(inf_dps, "tpEmit").text = "1"
        
        # 8. cLocEmi - Código IBGE do município emissor
        SubElement(inf_dps, "cLocEmi").text = "4205407"  # Florianópolis-SC
        
        # 9. prest - Dados do Prestador
        prest_elem = SubElement(inf_dps, "prest")
        self._add_prestador_v101(prest_elem, nfse_request.prestador)
        
        # 10. toma - Dados do Tomador (opcional)
        if nfse_request.tomador:
            toma_elem = SubElement(inf_dps, "toma")
            self._add_tomador_v101(toma_elem, nfse_request.tomador)
        
        # 11. serv - Dados do Serviço
        serv_elem = SubElement(inf_dps, "serv")
        self._add_servico_v101(serv_elem, nfse_request.servico)
        
        # 12. valores - Valores e tributos
        valores_elem = SubElement(inf_dps, "valores")
        self._add_valores_v101(valores_elem, nfse_request.servico)
        
        # Convertendo para string XML
        xml_string = tostring(root, encoding="unicode", method="xml")
        
        # Adicionando declaração XML
        xml_declaracao = '<?xml version="1.0" encoding="UTF-8"?>\n'
        return xml_declaracao + xml_string
    
    def _add_prestador_v101(self, parent: Element, prestador: PrestadorServico):
        """Adiciona dados do prestador conforme XSD v1.01."""
        
        # 1. CNPJ
        SubElement(parent, "CNPJ").text = prestador.cnpj
        
        # 2. IM - Inscrição Municipal
        if prestador.inscricao_municipal:
            SubElement(parent, "IM").text = prestador.inscricao_municipal
        
        # 3. xNome - Razão Social - NÃO ENVIAR quando prestador é o emitente (E0121)
        # SubElement(parent, "xNome").text = prestador.razao_social
        
        # 4. end - Endereço - NÃO ENVIAR quando prestador é o emitente da DPS (E0128)
        # end_elem = SubElement(parent, "end")
        # end_nac = SubElement(end_elem, "endNac")
        # SubElement(end_nac, "cMun").text = "4205407"
        # SubElement(end_nac, "CEP").text = "88010000"
        # SubElement(end_elem, "xLgr").text = "Rua Felipe Schmidt"
        # SubElement(end_elem, "nro").text = "100"
        # SubElement(end_elem, "xBairro").text = "Centro"
        
        # 5. regTrib - Regimes Tributários (obrigatório)
        reg_trib = SubElement(parent, "regTrib")
        # opSimpNac: 1=Não optante, 2=Optante SN, 3=MEI
        SubElement(reg_trib, "opSimpNac").text = "3"  # 3=MEI
        # regApTribSN - Regime de Apuração dos Tributos do SN (obrigatório para optante SN)
        # 1=Caixa, 2=Competência
        SubElement(reg_trib, "regApTribSN").text = "2"  # 2=Competência
        SubElement(reg_trib, "regEspTrib").text = "0"  # 0=Nenhum
    
    def _add_tomador_v101(self, parent: Element, tomador: TomadorServico):
        """Adiciona dados do tomador conforme XSD v1.01."""
        
        # CPF ou CNPJ
        if tomador.cpf:
            SubElement(parent, "CPF").text = tomador.cpf
        elif tomador.cnpj:
            SubElement(parent, "CNPJ").text = tomador.cnpj
        
        # xNome - Nome
        SubElement(parent, "xNome").text = tomador.nome
    
    def _add_servico_v101(self, parent: Element, servico: Servico):
        """Adiciona dados do serviço conforme XSD v1.01."""
        
        # 1. locPrest - Local da Prestação
        loc_prest = SubElement(parent, "locPrest")
        SubElement(loc_prest, "cLocPrestacao").text = "4205407"  # Florianópolis
        
        # 2. cServ - Elemento container para códigos e descrição do serviço
        c_serv_elem = SubElement(parent, "cServ")
        
        # 3. cTribNac - Código de Tributação Nacional (dentro de cServ)
        # Formato esperado: NNSSXX onde NN=item, SS=subitem, XX=variação
        # Exemplo: 04.01.01 → 040101
        item_lista = servico.item_lista_servico.strip()
        if '.' in item_lista:
            partes = item_lista.split('.')
            if len(partes) >= 3:
                # Formato com 3 partes: 04.01.01 → 040101
                item = partes[0].zfill(2)
                subitem = partes[1].zfill(2)
                variacao = partes[2].zfill(2)
                c_trib_nac = f"{item}{subitem}{variacao}"
            elif len(partes) == 2:
                # Formato com 2 partes: 1.09 → 010900
                item = partes[0].zfill(2)
                subitem = partes[1].zfill(2)
                c_trib_nac = f"{item}{subitem}00"
            else:
                c_trib_nac = item_lista.replace('.', '').zfill(6)
        else:
            # Se não tem ponto, assume formato já correto ou ajusta
            c_trib_nac = item_lista.replace('.', '').zfill(6)
        
        SubElement(c_serv_elem, "cTribNac").text = c_trib_nac
        
        # 4. xDescServ - Descrição do Serviço (dentro de cServ)
        SubElement(c_serv_elem, "xDescServ").text = servico.descricao
    
    def _add_valores_v101(self, parent: Element, servico: Servico):
        """Adiciona valores conforme XSD v1.01."""
        
        # 1. vServPrest - Elemento container para valores do serviço
        v_serv_prest_elem = SubElement(parent, "vServPrest")
        
        # vReceb - Valor a Receber - NÃO informar quando prestador emite DPS (E0424)
        # valor_receber = servico.valor_servico - (servico.valor_deducoes or 0)
        # SubElement(v_serv_prest_elem, "vReceb").text = f"{valor_receber:.2f}"
        
        # vServ - Valor do Serviço
        SubElement(v_serv_prest_elem, "vServ").text = f"{servico.valor_servico:.2f}"
        
        # 2. vDescIncond - Desconto Incondicional (opcional)
        if servico.valor_deducoes and servico.valor_deducoes > 0:
            SubElement(parent, "vDescIncond").text = f"{servico.valor_deducoes:.2f}"
        
        # 3. trib - Elemento container para tributos
        trib_elem = SubElement(parent, "trib")
        
        # tribMun - Tributos Municipais
        trib_mun_elem = SubElement(trib_elem, "tribMun")
        
        # tribISSQN - Indicador de tributação ISS QN (valor: 1)
        SubElement(trib_mun_elem, "tribISSQN").text = "1"
        
        # tpRetISSQN - Tipo de Retenção ISSQN (campo de texto obrigatório após tribISSQN)
        # Valores possíveis: provavelmente código de tipo de retenção
        SubElement(trib_mun_elem, "tpRetISSQN").text = "1"
        
        # totTrib - Total de Tributos (obrigatório em trib após tribMun)
        tot_trib_elem = SubElement(trib_elem, "totTrib")
        
        # pTotTribSN - Percentual Total de Tributos Simples Nacional
        # Usa a alíquota de ISS como percentual
        SubElement(tot_trib_elem, "pTotTribSN").text = f"{servico.aliquota_iss:.2f}"
    
    def _add_prestador(self, parent: Element, prestador: PrestadorServico):
        """Adiciona dados do prestador ao XML (formato antigo - DEPRECATED)."""
        SubElement(parent, "CNPJ").text = prestador.cnpj
        SubElement(parent, "InscricaoMunicipal").text = prestador.inscricao_municipal or ""
        SubElement(parent, "RazaoSocial").text = prestador.razao_social
        
        if prestador.nome_fantasia:
            SubElement(parent, "NomeFantasia").text = prestador.nome_fantasia
    
    def _add_tomador(self, parent: Element, tomador: TomadorServico):
        """Adiciona dados do tomador ao XML."""
        if tomador.cpf:
            SubElement(parent, "CPF").text = tomador.cpf
        elif tomador.cnpj:
            SubElement(parent, "CNPJ").text = tomador.cnpj
        
        SubElement(parent, "Nome").text = tomador.nome
        
        # Endereço
        if tomador.logradouro:
            endereco = SubElement(parent, "Endereco")
            SubElement(endereco, "Logradouro").text = tomador.logradouro
            SubElement(endereco, "Numero").text = tomador.numero or "S/N"
            
            if tomador.complemento:
                SubElement(endereco, "Complemento").text = tomador.complemento
            if tomador.bairro:
                SubElement(endereco, "Bairro").text = tomador.bairro
            if tomador.municipio:
                SubElement(endereco, "Municipio").text = tomador.municipio
            if tomador.uf:
                SubElement(endereco, "UF").text = tomador.uf
            if tomador.cep:
                SubElement(endereco, "CEP").text = tomador.cep
        
        # Contato
        if tomador.email:
            SubElement(parent, "Email").text = tomador.email
        if tomador.telefone:
            SubElement(parent, "Telefone").text = tomador.telefone
    
    def _add_servico(self, parent: Element, servico: Servico):
        """Adiciona dados do serviço ao XML."""
        SubElement(parent, "Discriminacao").text = servico.descricao
        if servico.discriminacao:
            SubElement(parent, "DiscriminacaoComplementar").text = servico.discriminacao
        SubElement(parent, "ItemListaServico").text = servico.item_lista_servico
        if servico.codigo_tributacao_municipio:
            SubElement(parent, "CodigoTributacaoMunicipal").text = servico.codigo_tributacao_municipio
        
        # Valores
        valores = SubElement(parent, "Valores")
        SubElement(valores, "ValorServicos").text = f"{servico.valor_servico:.2f}"
        
        if servico.valor_deducoes and servico.valor_deducoes > 0:
            SubElement(valores, "ValorDeducoes").text = f"{servico.valor_deducoes:.2f}"
        
        # ISS - Calcula se não foi fornecido
        SubElement(valores, "AliquotaISS").text = f"{servico.aliquota_iss:.2f}"
        
        if servico.valor_iss is not None:
            SubElement(valores, "ValorISS").text = f"{servico.valor_iss:.2f}"
        else:
            # Calcula o ISS automaticamente
            base_calculo = servico.valor_servico - (servico.valor_deducoes or 0)
            valor_iss_calculado = base_calculo * (servico.aliquota_iss / 100)
            SubElement(valores, "ValorISS").text = f"{valor_iss_calculado:.2f}"
    
    def comprimir_e_codificar(self, xml: str) -> str:
        """
        Comprime o XML em GZIP e codifica em Base64.
        
        Args:
            xml: String XML
            
        Returns:
            XML comprimido e codificado em Base64
        """
        # Converter XML para bytes
        xml_bytes = xml.encode('utf-8')
        
        # Comprimir com GZIP
        compressed = gzip.compress(xml_bytes, compresslevel=9)
        
        # Codificar em Base64
        encoded = base64.b64encode(compressed).decode('utf-8')
        
        return encoded
    
    def gerar_lote_comprimido(self, nfse_requests: list[NFSeRequest]) -> list[str]:
        """
        Gera lote de XMLs comprimidos e codificados.
        
        Args:
            nfse_requests: Lista de requisições NFS-e
            
        Returns:
            Lista de XMLs comprimidos em Base64
        """
        lote_comprimido = []
        
        for nfse_req in nfse_requests:
            # Gerar XML
            xml = self.gerar_xml_nfse(nfse_req)
            
            # Comprimir e codificar
            xml_comprimido = self.comprimir_e_codificar(xml)
            
            lote_comprimido.append(xml_comprimido)
        
        return lote_comprimido
    
    @staticmethod
    def decodificar_e_descomprimir(xml_base64: str) -> str:
        """
        Decodifica Base64 e descomprime GZIP.
        
        Args:
            xml_base64: XML em Base64
            
        Returns:
            XML descomprimido
        """
        # Decodificar Base64
        compressed = base64.b64decode(xml_base64)
        
        # Descomprimir GZIP
        xml_bytes = gzip.decompress(compressed)
        
        # Converter para string
        return xml_bytes.decode('utf-8')
    
    def assinar_xml(self, xml_string: str) -> str:
        """
        Assina digitalmente o XML usando certificado A1 (padrão XMLDSig).
        
        Args:
            xml_string: XML em formato string
            
        Returns:
            XML assinado digitalmente
            
        Raises:
            RuntimeError: Se signxml não estiver instalado
            ValueError: Se certificado ou chave não configurados
        """
        if not SIGNXML_AVAILABLE:
            raise RuntimeError(
                "Biblioteca 'signxml' não instalada. "
                "Instale com: pip install signxml lxml"
            )
        
        if not self.cert_path or not self.key_path:
            raise ValueError(
                "Certificado e chave privada devem ser configurados para assinar XML. "
                "Passe cert_path e key_path no construtor."
            )
        
        # Verificar se arquivos existem
        cert_file = Path(self.cert_path)
        key_file = Path(self.key_path)
        
        if not cert_file.exists():
            raise FileNotFoundError(f"Certificado não encontrado: {self.cert_path}")
        
        if not key_file.exists():
            raise FileNotFoundError(f"Chave privada não encontrada: {self.key_path}")
        
        try:
            # Parse XML com lxml
            root = etree.fromstring(xml_string.encode('utf-8'))
            
            # Ler certificado e chave
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            # Configurar assinador XMLDSig
            signer = XMLSigner(
                method=methods.enveloped,  # Assinatura envelopada (dentro do XML)
                signature_algorithm='rsa-sha256',  # Algoritmo de assinatura
                digest_algorithm='sha256',  # Algoritmo de hash
                c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
            )
            
            # Assinar XML
            signed_root = signer.sign(
                root,
                key=key_data,
                cert=cert_data
            )
            
            # Converter de volta para string
            xml_assinado = etree.tostring(
                signed_root,
                encoding='unicode'
            )
            
            # Adicionar declaração XML manualmente
            xml_declaracao = '<?xml version="1.0" encoding="UTF-8"?>\n'
            return xml_declaracao + xml_assinado
            
        except Exception as e:
            raise RuntimeError(f"Erro ao assinar XML: {e}") from e
    
    def gerar_xml_assinado(self, nfse_request: NFSeRequest) -> str:
        """
        Gera e assina XML NFS-e.
        
        Args:
            nfse_request: Dados da NFS-e
            
        Returns:
            XML assinado digitalmente
        """
        # Gerar XML
        xml = self.gerar_xml_nfse(nfse_request)
        
        # Assinar se configurado
        if self.cert_path and self.key_path and SIGNXML_AVAILABLE:
            xml = self.assinar_xml(xml)
        
        return xml
    
    def gerar_lote_comprimido_assinado(self, nfse_requests: list[NFSeRequest]) -> list[str]:
        """
        Gera lote de XMLs assinados, comprimidos e codificados.
        
        Args:
            nfse_requests: Lista de requisições NFS-e
            
        Returns:
            Lista de XMLs assinados e comprimidos em Base64
        """
        lote_comprimido = []
        
        for nfse_req in nfse_requests:
            # Gerar XML assinado
            xml = self.gerar_xml_assinado(nfse_req)
            
            # Comprimir e codificar
            xml_comprimido = self.comprimir_e_codificar(xml)
            
            lote_comprimido.append(xml_comprimido)
        
        return lote_comprimido

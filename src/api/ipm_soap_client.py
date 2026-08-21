"""
Cliente REST para o sistema IPM/Atende.Net (Prefeitura de Santa Rosa-RS).
NTE-35/2021 - Layout IPM próprio via multipart/form-data.
"""
import httpx
from typing import Optional
from xml.etree import ElementTree as ET

from config.settings import settings
from src.utils.logger import app_logger


class IPMSoapClient:
    """Cliente REST para emissão de NFS-e via IPM/Atende.Net."""

    def __init__(self):
        self.base_url = settings.IPM_WEBSERVICE_URL.rstrip("/")
        # Login deve conter apenas números (error [144])
        import re
        self.usuario = re.sub(r"\D", "", settings.IPM_USUARIO)
        self.senha = settings.IPM_SENHA
        self.timeout = 60

    async def enviar_lote_rps_sincrono(self, xml_content: str) -> dict:
        """Envia XML de NFS-e via POST multipart/form-data e retorna resultado."""
        return await self._post_xml(xml_content)

    async def gerar_nfse(self, xml_content: str) -> dict:
        """Alias para enviar_lote_rps_sincrono (IPM usa o mesmo endpoint)."""
        return await self._post_xml(xml_content)

    async def _post_xml(self, xml_content: str) -> dict:
        """Envia XML como arquivo via multipart/form-data com Basic Auth."""
        app_logger.info(f"IPM REST: POST → {self.base_url}")

        auth = (self.usuario, self.senha)
        # XML enviado como arquivo no campo "teste" (key name conforme doc seção 4.14)
        files = {"teste": ("nfse.xml", xml_content.encode("utf-8"), "text/xml")}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                files=files,
                auth=auth,
            )

        # Decodifica com latin-1 (ISO-8859-1) pois o servidor IPM retorna nesse encoding
        raw_bytes = response.content
        try:
            raw_text = raw_bytes.decode("latin-1")
        except Exception:
            raw_text = response.text

        app_logger.debug(f"IPM REST response HTTP {response.status_code}: {raw_text[:500]}")

        if response.status_code not in (200, 201):
            app_logger.error(f"IPM REST erro HTTP {response.status_code}: {raw_text[:500]}")
            raise RuntimeError(f"IPM REST HTTP {response.status_code}: {raw_text[:500]}")

        return self._parse_resposta(raw_text)

    def _parse_resposta(self, xml_text: str) -> dict:
        """Extrai dados do XML de retorno IPM (encoding ISO-8859-1)."""
        # Remove a declaração XML de encoding para não conflitar com o parse
        import re as _re
        xml_clean = _re.sub(r'<\?xml[^>]+\?>', '', xml_text).strip()
        try:
            root = ET.fromstring(xml_clean)
        except ET.ParseError:
            try:
                root = ET.fromstring(xml_clean.encode("latin-1"))
            except Exception as e:
                return {"raw": xml_text, "parse_error": str(e)}

        result = {"raw": xml_text}

        # Verifica mensagens (erros ou sucesso)
        mensagens = []
        for msg_elem in root.findall(".//mensagem"):
            for cod in msg_elem.findall("codigo"):
                mensagens.append(cod.text or "")
        result["mensagens"] = mensagens

        # Sucesso: código começa com "00001 - Sucesso"
        sucesso = any("sucesso" in m.lower() or m.startswith("00001") for m in mensagens)
        # Teste válido: "NFS-e válida para emissão"
        valida_teste = any("válida" in m.lower() or "valida" in m.lower() for m in mensagens)

        if sucesso or valida_teste:
            numero = root.findtext(".//numero_nfse")
            chave = root.findtext(".//cod_verificador_autenticidade")
            link = root.findtext(".//link_nfse")
            result["numero_nfse"] = numero
            result["chave"] = chave
            result["link"] = link
            result["sucesso"] = True
        else:
            result["sucesso"] = False
            result["erros"] = [{"mensagem": m} for m in mensagens if mensagens]

        return result

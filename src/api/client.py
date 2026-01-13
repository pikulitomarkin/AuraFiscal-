"""
Cliente HTTP assíncrono para comunicação com APIs externas.
"""
import httpx
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import settings
from src.utils.logger import app_logger


class AsyncAPIClient:
    """Cliente HTTP assíncrono com retry e timeouts configuráveis."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None
    ):
        """
        Inicializa o cliente HTTP.
        
        Args:
            base_url: URL base da API
            timeout: Timeout em segundos
            max_retries: Número máximo de tentativas
            headers: Headers padrão
            cert_path: Caminho para o arquivo do certificado (.pem) para mTLS
            key_path: Caminho para o arquivo da chave privada (.pem) para mTLS
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = headers or {}
        self.default_headers.setdefault('Content-Type', 'application/json')
        self.default_headers.setdefault('Accept', 'application/json')
        self.cert_path = cert_path
        self.key_path = key_path
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Executa requisição HTTP com retry automático.
        
        Args:
            method: Método HTTP (GET, POST, etc)
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para httpx
            
        Returns:
            Resposta HTTP
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        headers = {**self.default_headers, **kwargs.pop('headers', {})}
        
        # Configura mTLS se certificados foram fornecidos
        client_kwargs = {'timeout': self.timeout}
        if self.cert_path and self.key_path:
            client_kwargs['cert'] = (self.cert_path, self.key_path)
            app_logger.debug(f"Usando mTLS com certificado: {self.cert_path}")
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            app_logger.debug(f"{method} {url}")
            
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            
            app_logger.debug(f"Response: {response.status_code}")
            
            return response
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Requisição GET."""
        return await self._request('GET', endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Requisição POST."""
        return await self._request('POST', endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """Requisição PUT."""
        return await self._request('PUT', endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Requisição DELETE."""
        return await self._request('DELETE', endpoint, **kwargs)
    
    async def post_json(self, endpoint: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        POST com payload JSON e retorno JSON.
        
        Args:
            endpoint: Endpoint da API
            data: Dados a serem enviados
            **kwargs: Argumentos adicionais
            
        Returns:
            Resposta JSON como dicionário
            
        Raises:
            httpx.HTTPStatusError: Se status não for 2xx
        """
        response = await self.post(endpoint, json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> bool:
        """
        Verifica se a API está disponível.
        
        Returns:
            True se disponível, False caso contrário
        """
        try:
            response = await self.get('/health', timeout=5)
            return response.status_code == 200
        except Exception as e:
            app_logger.warning(f"Health check falhou: {e}")
            return False


class NFSeAPIClient(AsyncAPIClient):
    """Cliente especializado para API Nacional de NFS-e (Sefin Nacional)."""
    
    def __init__(self, cert_path: Optional[str] = None, key_path: Optional[str] = None):
        """
        Inicializa o cliente da API NFS-e Sefin Nacional.
        
        Args:
            cert_path: Caminho para o arquivo do certificado (.pem) para mTLS
            key_path: Caminho para o arquivo da chave privada (.pem) para mTLS
        """
        super().__init__(
            base_url=settings.NFSE_API_BASE_URL,
            timeout=settings.NFSE_API_TIMEOUT,
            max_retries=settings.NFSE_API_MAX_RETRIES,
            cert_path=cert_path,
            key_path=key_path
        )
        
        if cert_path and key_path:
            app_logger.info(f"Cliente Sefin NFS-e inicializado com mTLS: {self.base_url}")
        else:
            app_logger.info(f"Cliente Sefin NFS-e inicializado: {self.base_url}")
    
    async def emitir_nfse(self, dps_xml_gzip_b64: str) -> Dict[str, Any]:
        """
        Emite NFS-e enviando DPS (Declaração de Prestação de Serviço) para Sefin Nacional.
        
        Endpoint: POST /SefinNacional/nfse
        Conforme Swagger Sefin: Geração síncrona de NFS-e a partir da DPS
        Payload: {"dpsXmlGZipB64": "string"} - DPS compactado GZIP e Base64
        
        Args:
            dps_xml_gzip_b64: DPS assinado, comprimido em GZIP e codificado em Base64
            
        Returns:
            Response com idDps, chaveAcesso, nfseXmlGZipB64 e alertas
            
        Raises:
            httpx.HTTPStatusError: Se status não for 201/2xx
        """
        try:
            app_logger.info(f"Enviando DPS para geração de NFS-e na Sefin Nacional")
            
            # Conforme Swagger Sefin Nacional: payload JSON com campo dpsXmlGZipB64
            payload = {
                "dpsXmlGZipB64": dps_xml_gzip_b64
            }
            
            # Envia para endpoint de emissão Sefin
            response = await self.post(
                "/SefinNacional/nfse",
                json=payload
            )
            response.raise_for_status()
            
            # Response 201 com JSON: NFSePostResponseSucesso
            # {idDps, chaveAcesso, nfseXmlGZipB64, alertas, tipoAmbiente, ...}
            resultado = response.json()
            
            app_logger.info(f"✅ NFS-e GERADA! Chave: {resultado.get('chaveAcesso', 'N/A')}")
            app_logger.info(f"ID DPS: {resultado.get('idDps', 'N/A')}")
            
            if resultado.get('alertas'):
                for alerta in resultado['alertas']:
                    app_logger.warning(f"⚠️ Alerta: {alerta.get('codigo')} - {alerta.get('descricao')}")
            
            return resultado
            
        except httpx.HTTPStatusError as e:
            app_logger.error(f"Erro HTTP ao emitir NFS-e: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                app_logger.error(f"Detalhes do erro: {error_detail}")
            except:
                app_logger.error(f"Resposta: {e.response.text[:500]}")
            raise
        except Exception as e:
            app_logger.error(f"Erro ao emitir NFS-e: {e}")
            raise
    
    async def recepcionar_lote(self, lote_xml_gzip_b64: list[str]) -> Dict[str, Any]:
        """
        Recepciona um lote de documentos NFS-e no ADN (Ambiente de Distribuição Nacional).
        
        Endpoint: POST /adn/DFe
        
        Args:
            lote_xml_gzip_b64: Lista de XMLs comprimidos em GZIP e codificados em Base64
            
        Returns:
            Resposta da API com status de processamento de cada documento
            
        Raises:
            httpx.HTTPStatusError: Se status não for 2xx
        """
        try:
            app_logger.info(f"Recepcionando lote de {len(lote_xml_gzip_b64)} documento(s) no ADN")
            
            # API ADN aceita múltiplos documentos em um único POST
            payload = {
                "LoteXmlGZipB64": lote_xml_gzip_b64
            }
            
            # Envia para endpoint de recepção ADN
            response = await self.post("/adn/DFe", json=payload)
            response.raise_for_status()
            
            resultado = response.json()
            
            app_logger.info(f"Lote ADN processado - Total: {len(resultado.get('Lote', []))}")
            
            return resultado
            
        except httpx.HTTPStatusError as e:
            app_logger.error(f"Erro HTTP ao recepcionar lote: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                app_logger.error(f"Detalhes do erro: {error_detail}")
            except:
                app_logger.error(f"Resposta: {e.response.text[:500]}")
            raise
        except Exception as e:
            app_logger.error(f"Erro ao recepcionar lote: {e}")
            raise

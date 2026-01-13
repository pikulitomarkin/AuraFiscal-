"""
Serviço de integração com API Nacional NFS-e (ADN).
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from src.api.client import NFSeAPIClient
from src.models.schemas import (
    NFSeRequest, NFSeResponse, ProcessingResult,
    PrestadorServico, TomadorServico, Servico,
    RecepcaoRequest, RecepcaoResponseLote, TipoAmbiente
)
from src.utils.logger import app_logger
from src.utils.xml_generator import NFSeXMLGenerator
from config.settings import settings


class NFSeService:
    """Serviço de alto nível para operações de NFS-e no ADN."""
    
    def __init__(self, prestador_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o serviço de NFS-e.
        
        Args:
            prestador_config: Configuração do prestador (emissor)
        """
        # Caminhos dos certificados para assinatura XML e mTLS
        cert_path = settings.CERTIFICATE_PATH.replace('.pfx', '_cert.pem') if hasattr(settings, 'CERTIFICATE_PATH') else 'certificados/cert.pem'
        key_path = settings.CERTIFICATE_PATH.replace('.pfx', '_key.pem') if hasattr(settings, 'CERTIFICATE_PATH') else 'certificados/key.pem'
        
        # Inicializa cliente API com mTLS
        self.client = NFSeAPIClient(cert_path=cert_path, key_path=key_path)
        
        # Inicializa gerador de XML com assinatura
        ambiente = TipoAmbiente(settings.NFSE_API_AMBIENTE)
        self.xml_generator = NFSeXMLGenerator(
            ambiente=ambiente,
            cert_path=cert_path,
            key_path=key_path
        )
        
        # Configuração do prestador
        self.prestador_config = prestador_config or self._load_default_prestador()
        
        app_logger.info(f"Serviço NFS-e inicializado - Ambiente: {ambiente.value}")
    
    def _load_default_prestador(self) -> Dict[str, Any]:
        """
        Carrega configuração padrão do prestador.
        Em produção, isso viria de um banco de dados ou arquivo de configuração.
        """
        return {
            "cnpj": "12345678000190",
            "inscricao_municipal": "123456",
            "razao_social": "Empresa Prestadora LTDA",
            "nome_fantasia": "Empresa",
            "logradouro": "Av. Principal",
            "numero": "1000",
            "bairro": "Centro",
            "municipio": "São Paulo",
            "uf": "SP",
            "cep": "01310000",
            "email": "contato@empresa.com.br",
            "telefone": "1140041234"
        }
    
    async def emitir_nfse_lote(
        self,
        registros: List[Dict[str, str]],
        config_servico: Dict[str, Any],
        callback_progress: Optional[callable] = None
    ) -> List[ProcessingResult]:
        """
        Emite NFS-e em lote usando a API ADN.
        
        Fluxo:
        1. Gera XMLs NFS-e para cada registro
        2. Comprime XMLs em GZIP e codifica em Base64
        3. Envia lote para API ADN (/adn/DFe)
        4. Processa resposta individual de cada documento
        
        Args:
            registros: Lista de registros extraídos do PDF
            config_servico: Configuração do serviço (valor, descrição, etc)
            callback_progress: Função callback para atualizar progresso
            
        Returns:
            Lista de resultados do processamento
        """
        total = len(registros)
        app_logger.info(f"Iniciando emissão em lote de {total} NFS-e via ADN")
        
        results: List[ProcessingResult] = []
        
        # Processa em lotes de até MAX_BATCH_SIZE (API ADN pode ter limite)
        max_batch = min(settings.MAX_BATCH_SIZE, 50)  # ADN recomenda lotes menores
        
        for i in range(0, total, max_batch):
            batch = registros[i:i + max_batch]
            batch_num = (i // max_batch) + 1
            
            app_logger.info(f"Processando lote {batch_num} com {len(batch)} documentos")
            
            try:
                # 1. Monta requisições NFS-e
                nfse_requests = [
                    self._build_nfse_request(reg, config_servico) 
                    for reg in batch
                ]
                
                # 2. Gera XMLs comprimidos e assinados digitalmente
                lote_xml_comprimido = self.xml_generator.gerar_lote_comprimido_assinado(nfse_requests)
                
                # 3. Envia para API ADN
                response_lote = await self.client.recepcionar_lote(lote_xml_comprimido)
                
                # 4. Processa resposta individual
                batch_results = self._processar_resposta_lote(
                    response_lote, 
                    batch, 
                    i
                )
                
                results.extend(batch_results)
                
            except Exception as e:
                app_logger.error(f"Erro ao processar lote {batch_num}: {e}")
                
                # Marca todos como erro
                for idx, reg in enumerate(batch):
                    results.append(ProcessingResult(
                        hash_transacao=reg.get('hash', 'N/A'),
                        cpf_tomador=reg.get('cpf', 'N/A'),
                        nome_tomador=reg.get('nome', 'N/A'),
                        status="erro",
                        mensagem=f"Erro no lote: {str(e)}"
                    ))
            
            # Callback de progresso
            if callback_progress:
                progress = min(i + max_batch, total)
                callback_progress(progress, total)
        
        # Estatísticas
        sucessos = sum(1 for r in results if r.status == "sucesso")
        erros = sum(1 for r in results if r.status == "erro")
        alertas = sum(1 for r in results if r.status == "alerta")
        
        app_logger.info(
            f"Lote ADN concluído: {sucessos} sucessos, {alertas} alertas, "
            f"{erros} erros de {total} total"
        )
        
        return results
    
    def _processar_resposta_lote(
        self,
        response: Dict[str, Any],
        registros: List[Dict[str, str]],
        offset: int
    ) -> List[ProcessingResult]:
        """
        Processa resposta do lote ADN e mapeia para resultados individuais.
        
        Args:
            response: Resposta da API ADN (RecepcaoResponseLote)
            registros: Registros originais
            offset: Offset do índice global
            
        Returns:
            Lista de resultados processados
        """
        results = []
        lote_docs = response.get('Lote', [])
        
        for idx, doc_response in enumerate(lote_docs):
            registro = registros[idx] if idx < len(registros) else {}
            
            # Extrai dados da resposta
            chave_acesso = doc_response.get('ChaveAcesso')
            nsu = doc_response.get('NsuRecepcao')
            status_proc = doc_response.get('StatusProcessamento', '').upper()
            alertas = doc_response.get('Alertas', [])
            erros = doc_response.get('Erros', [])
            
            # Determina status final
            if erros:
                status = "erro"
                mensagens_erro = [f"{e.get('Codigo', '')}: {e.get('Descricao', '')}" for e in erros]
                mensagem = "; ".join(mensagens_erro)
            elif status_proc in ["PROCESSADO", "AUTORIZADO"]:
                status = "sucesso"
                mensagem = f"Autorizado - NSU: {nsu}"
            elif alertas:
                status = "alerta"
                mensagens_alerta = [f"{a.get('Codigo', '')}: {a.get('Descricao', '')}" for a in alertas]
                mensagem = "; ".join(mensagens_alerta)
            else:
                status = "processando"
                mensagem = f"Status: {status_proc}"
            
            result = ProcessingResult(
                hash_transacao=registro.get('hash', 'N/A'),
                cpf_tomador=registro.get('cpf', 'N/A'),
                nome_tomador=registro.get('nome', 'N/A'),
                status=status,
                numero_nfse=chave_acesso,  # Chave de acesso é o identificador único
                protocolo=nsu,
                mensagem=mensagem,
                data_processamento=datetime.now()
            )
            
            results.append(result)
            
            app_logger.debug(
                f"[{offset + idx}] {registro.get('nome', 'N/A')}: {status} - {mensagem}"
            )
        
        return results
    
    def _build_nfse_request(
        self,
        registro: Dict[str, str],
        config_servico: Dict[str, Any]
    ) -> NFSeRequest:
        """
        Constrói objeto NFSeRequest a partir dos dados.
        
        Args:
            registro: Dados extraídos do PDF
            config_servico: Configuração do serviço
            
        Returns:
            Objeto NFSeRequest validado
        """
        # Prestador
        prestador = PrestadorServico(**self.prestador_config)
        
        # Tomador (cliente)
        tomador = TomadorServico(
            cpf=registro['cpf'],
            nome=registro['nome']
        )
        
        # Serviço
        servico = Servico(
            descricao=config_servico.get('descricao', 'Prestação de serviços'),
            valor_servico=Decimal(str(config_servico.get('valor', 100.00))),
            aliquota_iss=Decimal(str(config_servico.get('aliquota_iss', 2.0))),
            item_lista_servico=config_servico.get('item_lista', '1.09'),
            discriminacao=config_servico.get('discriminacao', None)
        )
        
        # Monta a requisição completa
        nfse = NFSeRequest(
            data_emissao=datetime.now(),
            competencia=date.today(),
            prestador=prestador,
            tomador=tomador,
            servico=servico,
            hash_transacao=registro['hash'],
            natureza_operacao=1,
            optante_simples_nacional=config_servico.get('simples_nacional', False)
        )
        
        return nfse
    
    async def consultar_status_api(self) -> bool:
        """
        Verifica se a API está disponível.
        
        Returns:
            True se disponível, False caso contrário
        """
        try:
            is_available = await self.client.health_check()
            
            if is_available:
                app_logger.info("API Nacional NFS-e está disponível")
            else:
                app_logger.warning("API Nacional NFS-e não está respondendo")
            
            return is_available
            
        except Exception as e:
            app_logger.error(f"Erro ao verificar status da API: {e}")
            return False


# Instância global (lazy initialization no Streamlit)
_nfse_service: Optional[NFSeService] = None


def get_nfse_service() -> NFSeService:
    """Retorna instância singleton do serviço NFS-e."""
    global _nfse_service
    
    if _nfse_service is None:
        _nfse_service = NFSeService()
    
    return _nfse_service

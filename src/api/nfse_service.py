"""
Serviço de integração com API Nacional NFS-e (ADN).
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

import httpx

from src.api.client import NFSeAPIClient
from src.models.schemas import (
    NFSeRequest, NFSeResponse, ProcessingResult,
    PrestadorServico, TomadorServico, Servico,
    RecepcaoRequest, RecepcaoResponseLote, TipoAmbiente
)
from src.utils.logger import app_logger
from src.utils.xml_generator import NFSeXMLGenerator
from config.settings import settings

# Tratamento E0014 (DPS já existente)
CODIGO_E0014 = "E0014"
DELAY_ENTRE_EMISSOES_SEG = 2
DELAY_RETRY_E0014_SEG = 5
MAX_TENTATIVAS_POR_NOTA = 3
REGEX_ID_DPS = re.compile(r"DPS\d{44}")


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
            "cnpj": "05863340000160",
            "inscricao_municipal": "40865",
            "razao_social": "NEUROCLIN SERVICOS MEDICOS LTDA",
            "nome_fantasia": "NEUROCLIN",
            "logradouro": "RUA FERNANDO FERRARI",
            "numero": "310",
            "complemento": "SALA 201",
            "bairro": "CENTRO",
            "municipio": "SANTA ROSA",
            "uf": "RS",
            "cep": "98780001",
            "email": "cadastro@dominiocontabil.com.br",
            "telefone": "4836327480"
        }
    
    def _extrair_id_dps_do_erro(self, response_body: Any) -> Optional[str]:
        """Extrai idDPS do corpo de resposta de erro (E0014)."""
        if response_body is None:
            return None
        if isinstance(response_body, dict):
            for key in ("idDps", "idDPS", "id_dps"):
                if key in response_body and response_body[key]:
                    return str(response_body[key]).strip()
            for key in ("detail", "mensagem", "message", "descricao"):
                if key in response_body and response_body[key]:
                    match = REGEX_ID_DPS.search(str(response_body[key]))
                    if match:
                        return match.group(0)
            if "errors" in response_body and isinstance(response_body["errors"], list):
                for err in response_body["errors"]:
                    if isinstance(err, dict):
                        found = self._extrair_id_dps_do_erro(err)
                        if found:
                            return found
            if "erros" in response_body and isinstance(response_body["erros"], list):
                for err in response_body["erros"]:
                    if isinstance(err, dict):
                        found = self._extrair_id_dps_do_erro(err)
                        if found:
                            return found
        if isinstance(response_body, str):
            match = REGEX_ID_DPS.search(response_body)
            if match:
                return match.group(0)
        return None

    def _erro_e0014(self, response_body: Any) -> bool:
        """Verifica se o erro é E0014 (DPS já existente)."""
        if response_body is None:
            return False
        if isinstance(response_body, dict):
            cod = response_body.get("codigo") or response_body.get("Codigo") or response_body.get("code")
            if cod and str(cod).strip().upper() == CODIGO_E0014:
                return True
            for lst in ("errors", "erros", "Erros"):
                if lst in response_body and isinstance(response_body[lst], list):
                    for item in response_body[lst]:
                        if isinstance(item, dict) and (item.get("Codigo") or item.get("codigo")) == CODIGO_E0014:
                            return True
        return False

    async def _emitir_uma_nfse_com_retry_e0014(
        self,
        registro: Dict[str, str],
        config_servico: Dict[str, Any],
        callback_progress: Optional[callable],
        total: int,
        progress_offset: int,
    ) -> ProcessingResult:
        """
        Emite uma NFS-e com throttling, tratamento E0014 (consulta por idDPS e retry) e log detalhado.
        """
        nfse_request = self._build_nfse_request(registro, config_servico)
        xml_comprimido = self.xml_generator.gerar_lote_comprimido_assinado([nfse_request])
        dps_b64 = xml_comprimido[0]
        id_dps_log: Optional[str] = None
        ultimo_erro: Optional[str] = None
        resultado_consulta: Optional[str] = None
        desfecho: Optional[str] = None

        for tentativa in range(1, MAX_TENTATIVAS_POR_NOTA + 1):
            try:
                resultado = await self.client.emitir_nfse(dps_b64)
                chave = resultado.get("chaveAcesso") or resultado.get("chave_acesso")
                id_dps_log = resultado.get("idDps") or resultado.get("id_dps")
                desfecho = "emitida com sucesso"
                app_logger.info(
                    f"[idDPS={id_dps_log or 'N/A'}] Emitida com sucesso (tentativa {tentativa}). Chave: {chave}"
                )
                if callback_progress:
                    callback_progress(progress_offset + 1, total)
                return ProcessingResult(
                    hash_transacao=registro.get("hash", "N/A"),
                    cpf_tomador=registro.get("cpf", "N/A"),
                    nome_tomador=registro.get("nome", "N/A"),
                    status="sucesso",
                    numero_nfse=chave,
                    protocolo=resultado.get("idDps"),
                    mensagem=f"Autorizado - Chave: {chave}",
                    timestamp=datetime.now(),
                )
            except httpx.HTTPStatusError as e:
                ultimo_erro = f"HTTP {e.response.status_code}"
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text
                if isinstance(body, str):
                    try:
                        import json
                        body = json.loads(body) if body.strip() else {}
                    except Exception:
                        pass
                ultimo_erro = f"HTTP {e.response.status_code}: {body}"
                if not self._erro_e0014(body):
                    desfecho = "erro real (não E0014)"
                    app_logger.error(
                        f"[hash={registro.get('hash')}] idDPS={id_dps_log or 'N/A'} | erro={ultimo_erro} | desfecho={desfecho}"
                    )
                    if callback_progress:
                        callback_progress(progress_offset + 1, total)
                    return ProcessingResult(
                        hash_transacao=registro.get("hash", "N/A"),
                        cpf_tomador=registro.get("cpf", "N/A"),
                        nome_tomador=registro.get("nome", "N/A"),
                        status="erro",
                        mensagem=str(body) if isinstance(body, dict) else (body or str(e)),
                        timestamp=datetime.now(),
                    )
                id_dps_log = self._extrair_id_dps_do_erro(body) or id_dps_log
                if not id_dps_log:
                    m = REGEX_ID_DPS.search(str(body))
                    id_dps_log = m.group(0) if m else None
                app_logger.warning(
                    f"[idDPS={id_dps_log or 'N/A'}] Erro E0014 recebido (tentativa {tentativa}). Consultando se NFS-e existe..."
                )
                consulta = None
                if id_dps_log and id_dps_log.strip():
                    consulta = await self.client.consultar_nfse_por_id_dps(id_dps_log.strip())
                if consulta:
                    resultado_consulta = "NFS-e encontrada"
                    chave = consulta.get("chaveAcesso") or consulta.get("chave_acesso")
                    desfecho = "já existia (considerado sucesso)"
                    app_logger.info(
                        f"[idDPS={id_dps_log}] Consulta: {resultado_consulta} | desfecho: {desfecho} | chave: {chave}"
                    )
                    if callback_progress:
                        callback_progress(progress_offset + 1, total)
                    return ProcessingResult(
                        hash_transacao=registro.get("hash", "N/A"),
                        cpf_tomador=registro.get("cpf", "N/A"),
                        nome_tomador=registro.get("nome", "N/A"),
                        status="sucesso",
                        numero_nfse=chave,
                        protocolo=id_dps_log,
                        mensagem=f"NFS-e já existia (E0014) - Chave: {chave}",
                        timestamp=datetime.now(),
                    )
                resultado_consulta = "NFS-e não encontrada"
                desfecho = f"reenvio após 5s (tentativa {tentativa}/{MAX_TENTATIVAS_POR_NOTA})"
                app_logger.info(
                    f"[idDPS={id_dps_log}] Consulta: {resultado_consulta} | desfecho: {desfecho}"
                )
                if tentativa < MAX_TENTATIVAS_POR_NOTA:
                    await asyncio.sleep(DELAY_RETRY_E0014_SEG)
                    # Regerar XML para nova tentativa (evita cache)
                    xml_comprimido = self.xml_generator.gerar_lote_comprimido_assinado([nfse_request])
                    dps_b64 = xml_comprimido[0]
            except Exception as e:
                ultimo_erro = str(e)
                desfecho = "exceção"
                app_logger.exception(f"[hash={registro.get('hash')}] idDPS={id_dps_log or 'N/A'} | erro: {e}")
                if callback_progress:
                    callback_progress(progress_offset + 1, total)
                return ProcessingResult(
                    hash_transacao=registro.get("hash", "N/A"),
                    cpf_tomador=registro.get("cpf", "N/A"),
                    nome_tomador=registro.get("nome", "N/A"),
                    status="erro",
                    mensagem=ultimo_erro or str(e),
                    timestamp=datetime.now(),
                )

        desfecho = "erro após 3 tentativas (E0014 mas NFS-e não encontrada)"
        app_logger.error(
            f"[idDPS={id_dps_log or 'N/A'}] Erro recebido: E0014 | Resultado consulta: {resultado_consulta} | Desfecho: {desfecho}"
        )
        if callback_progress:
            callback_progress(progress_offset + 1, total)
        return ProcessingResult(
            hash_transacao=registro.get("hash", "N/A"),
            cpf_tomador=registro.get("cpf", "N/A"),
            nome_tomador=registro.get("nome", "N/A"),
            status="erro",
            mensagem=f"E0014 - NFS-e não encontrada após {MAX_TENTATIVAS_POR_NOTA} tentativas. Requer atenção manual.",
            timestamp=datetime.now(),
        )

    async def emitir_nfse_lote(
        self,
        registros: List[Dict[str, str]],
        config_servico: Dict[str, Any],
        callback_progress: Optional[callable] = None
    ) -> List[ProcessingResult]:
        """
        Emite NFS-e em lote via API Sefin Nacional (emissão unitária com throttling).

        Para cada registro: delay 2s entre emissões; em caso de E0014, consulta por idDPS;
        se não existir, aguarda 5s e reenvia (máx 3 tentativas). Log detalhado e relatório final.
        """
        total = len(registros)
        app_logger.info(f"Iniciando emissão em lote de {total} NFS-e (Sefin Nacional, throttling {DELAY_ENTRE_EMISSOES_SEG}s)")
        
        results: List[ProcessingResult] = []
        
        for idx, registro in enumerate(registros):
            if idx > 0:
                await asyncio.sleep(DELAY_ENTRE_EMISSOES_SEG)
            result = await self._emitir_uma_nfse_com_retry_e0014(
                registro, config_servico, callback_progress, total, idx
            )
            results.append(result)
        
        # Relatório final
        sucessos = sum(1 for r in results if r.status == "sucesso")
        erros = sum(1 for r in results if r.status == "erro")
        alertas = sum(1 for r in results if r.status == "alerta")
        requer_atencao = [
            {"hash": r.hash_transacao, "cpf": r.cpf_tomador, "nome": r.nome_tomador, "mensagem": r.mensagem}
            for r in results
            if r.status == "erro" or (r.status == "alerta" and r.mensagem)
        ]
        app_logger.info(
            f"RELATÓRIO FINAL LOTE: Total processado={total} | Sucesso={sucessos} | Erro real={erros} | Alertas={alertas}"
        )
        app_logger.info(
            f"Notas que precisam de atenção manual ({len(requer_atencao)}): {requer_atencao}"
        )
        
        return results
    
    async def emitir_nfse_lote_ipm(
        self,
        registros: List[Dict[str, str]],
        config_servico: Dict[str, Any],
        callback_progress: Optional[callable] = None,
    ) -> List[ProcessingResult]:
        """
        Emite NFS-e em lote via IPM/Atende.Net (Prefeitura de Santa Rosa-RS, ABRASF 2.04).
        """
        from src.api.ipm_soap_client import IPMSoapClient
        from src.utils.rps_xml_generator import RPSXMLGenerator

        cert_path = settings.CERTIFICATE_PATH.replace(".pfx", "_cert.pem")
        key_path = settings.CERTIFICATE_PATH.replace(".pfx", "_key.pem")

        ipm_client = IPMSoapClient()
        rps_gen = RPSXMLGenerator(
            cert_path=cert_path,
            key_path=key_path,
            ambiente_teste=settings.IPM_AMBIENTE_TESTE,
        )

        prestador = self.prestador_config
        total = len(registros)
        results: List[ProcessingResult] = []

        app_logger.info(f"IPM: Iniciando emissão de {total} NFS-e via Atende.Net")

        for idx, registro in enumerate(registros):
            if idx > 0:
                await asyncio.sleep(2)

            numero_rps = idx + 1
            try:
                rps_xml = rps_gen.gerar_enviar_lote_rps_sincrono(
                    cnpj_prestador=prestador["cnpj"],
                    inscricao_municipal=prestador["inscricao_municipal"],
                    numero_lote=numero_rps,
                    numero_rps=numero_rps,
                    serie_rps="A",
                    cpf_tomador=re.sub(r"\D", "", registro.get("cpf", "")),
                    nome_tomador=registro.get("nome", ""),
                    descricao=config_servico.get("descricao", "CONSULTA MEDICA"),
                    valor=float(config_servico.get("valor", 0)),
                    aliquota_iss=float(config_servico.get("aliquota_iss", 2.6011)),
                    codigo_servico=config_servico.get("item_lista", "40303"),
                    codigo_municipio="4318002",
                    bairro_tomador=registro.get("bairro", "NAO INFORMADO"),
                    cep_tomador=registro.get("cep", "00000000"),
                    logradouro_tomador=registro.get("logradouro", "NAO INFORMADO"),
                )

                resposta = await ipm_client.enviar_lote_rps_sincrono(rps_xml)

                erros = resposta.get("erros", [])
                if erros:
                    msgs = "; ".join(f"[{e.get('codigo')}] {e.get('mensagem')}" for e in erros)
                    app_logger.error(f"IPM erro [{registro.get('hash')}]: {msgs}")
                    results.append(ProcessingResult(
                        hash_transacao=registro.get("hash", "N/A"),
                        cpf_tomador=registro.get("cpf", "N/A"),
                        nome_tomador=registro.get("nome", "N/A"),
                        status="erro",
                        mensagem=msgs,
                        timestamp=datetime.now(),
                    ))
                else:
                    numero = resposta.get("numero_nfse")
                    chave = resposta.get("chave")
                    app_logger.info(f"IPM sucesso [{registro.get('hash')}]: NFS-e {numero} | Chave: {chave}")
                    results.append(ProcessingResult(
                        hash_transacao=registro.get("hash", "N/A"),
                        cpf_tomador=registro.get("cpf", "N/A"),
                        nome_tomador=registro.get("nome", "N/A"),
                        status="sucesso",
                        numero_nfse=numero,
                        protocolo=chave,
                        mensagem=f"Emitida - NFS-e {numero}",
                        timestamp=datetime.now(),
                    ))

            except Exception as exc:
                app_logger.error(f"IPM exceção [{registro.get('hash')}]: {exc}")
                results.append(ProcessingResult(
                    hash_transacao=registro.get("hash", "N/A"),
                    cpf_tomador=registro.get("cpf", "N/A"),
                    nome_tomador=registro.get("nome", "N/A"),
                    status="erro",
                    mensagem=str(exc),
                    timestamp=datetime.now(),
                ))

            if callback_progress:
                callback_progress(idx + 1, total)

        sucessos = sum(1 for r in results if r.status == "sucesso")
        erros_total = sum(1 for r in results if r.status == "erro")
        app_logger.info(f"IPM RELATÓRIO: Total={total} | Sucesso={sucessos} | Erro={erros_total}")
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

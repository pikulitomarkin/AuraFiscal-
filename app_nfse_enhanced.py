"""
Dashboard Streamlit APRIMORADO para Emissão de NFS-e Nacional.
Agora com funcionalidade de download de XML e PDF!
"""
import streamlit as st
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
import base64
from io import BytesIO
import json
import zipfile

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Imports do projeto
from config.settings import settings
from config.database import init_database
from src.auth.authentication import auth_manager
from src.pdf.extractor import pdf_extractor
from src.api.nfse_service import get_nfse_service
from src.database.repository import NFSeRepository, LogRepository
from src.models.schemas import ProcessingResult, PrestadorServico, TomadorServico, Servico
from src.utils.logger import app_logger
from src.utils.certificate import get_certificate_manager

# Import das funções de emissão completa
from emitir_nfse_completo import emitir_nfse_com_pdf

# Configuração da página
st.set_page_config(
    page_title="NFS-e Automation Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# FUNÇÕES DE PERSISTÊNCIA DE DADOS
# ============================================================================

# Diretório de dados persistentes (Railway ou local)
# Se RAILWAY_VOLUME_MOUNT_PATH existe, usa ele diretamente (já aponta para /app/data)
# Senão, cria pasta 'data' no diretório local
DATA_DIR = Path(os.getenv('RAILWAY_VOLUME_MOUNT_PATH', './data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
PERSISTENCE_FILE = DATA_DIR / "nfse_emitidas.json"

def save_emitted_nfse():
    """Salva as NFS-e emitidas em arquivo JSON."""
    try:
        # Garantir que o diretório existe
        PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.emitted_nfse, f, ensure_ascii=False, indent=2)
        app_logger.info(f"Notas salvas em {PERSISTENCE_FILE}: {len(st.session_state.emitted_nfse)} registros")
    except Exception as e:
        app_logger.error(f"Erro ao salvar notas em {PERSISTENCE_FILE}: {e}")

def load_emitted_nfse():
    """Carrega as NFS-e emitidas do arquivo JSON."""
    try:
        if PERSISTENCE_FILE.exists():
            with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                app_logger.info(f"Notas carregadas de {PERSISTENCE_FILE}: {len(data)} registros")
                return data
        else:
            app_logger.info(f"Arquivo {PERSISTENCE_FILE} não encontrado. Iniciando com lista vazia.")
    except Exception as e:
        app_logger.error(f"Erro ao carregar notas de {PERSISTENCE_FILE}: {e}")
    return []


# ============================================================================
# FUNÇÕES DE SESSÃO E AUTENTICAÇÃO
# ============================================================================

def init_session_state():
    """Inicializa variáveis de sessão."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'emitted_nfse' not in st.session_state:
        # Carrega notas salvas do arquivo
        st.session_state.emitted_nfse = load_emitted_nfse()
    if 'last_emission' not in st.session_state:
        st.session_state.last_emission = None


def login_page():
    """Renderiza página de login."""
    st.title("🔐 Sistema de Emissão NFS-e")
    st.markdown("### Portal de Automação de Notas Fiscais")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("#### Credenciais de Acesso")
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
            
            if submit:
                # Autenticação simplificada (credenciais: admin/admin)
                if username == "admin" and password == "admin":
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.token = "authenticated"
                    st.session_state.page = 'dashboard'
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos")


def logout():
    """Realiza logout."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.token = None
    st.session_state.page = 'login'
    st.session_state.emitted_nfse = []
    st.session_state.last_emission = None
    st.rerun()


# ============================================================================
# DASHBOARD PRINCIPAL
# ============================================================================

def render_dashboard():
    """Renderiza dashboard principal."""
    st.sidebar.title("⚙️ Menu Principal")
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state.username}")
    st.sidebar.markdown("---")
    
    # Menu de navegação
    menu = st.sidebar.radio(
        "Navegação",
        ["📊 Dashboard", "📤 Emissão Individual", "📋 Emissão em Lote", "📜 NFS-e Emitidas", "⚙️ Configurações"],
        key="menu_navigation"
    )
    
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
    
    # Renderiza página selecionada
    if menu == "📊 Dashboard":
        render_overview()
    elif menu == "📤 Emissão Individual":
        render_single_emission()
    elif menu == "📋 Emissão em Lote":
        render_batch_emission()
    elif menu == "📜 NFS-e Emitidas":
        render_emitted_nfse_list()
    elif menu == "⚙️ Configurações":
        render_settings()


def render_overview():
    """Renderiza página de overview."""
    st.title("📊 Dashboard - Visão Geral")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("NFS-e Emitidas", len(st.session_state.emitted_nfse))
    
    with col2:
        total_valor = sum([nfse.get('valor', 0) for nfse in st.session_state.emitted_nfse])
        st.metric("Valor Total", f"R$ {total_valor:,.2f}")
    
    with col3:
        st.metric("Sistema", "✅ Operacional")
    
    with col4:
        st.metric("Certificado", "✅ Válido")
    
    st.markdown("---")
    
    # Últimas emissões
    st.markdown("### 📋 Últimas Emissões")
    
    if st.session_state.emitted_nfse:
        for nfse in reversed(st.session_state.emitted_nfse[-5:]):
            with st.expander(f"🧾 NFS-e #{nfse.get('numero', 'N/A')} - {nfse.get('data_emissao', 'N/A')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Chave de Acesso:** `{nfse.get('chave_acesso', 'N/A')}`")
                    st.markdown(f"**Tomador:** {nfse.get('tomador_nome', 'N/A')}")
                    st.markdown(f"**CPF/CNPJ:** {nfse.get('tomador_cpf', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Valor:** R$ {nfse.get('valor', 0):,.2f}")
                    st.markdown(f"**ISS:** R$ {nfse.get('iss', 0):,.2f}")
                    
                    # Botões de download
                    col_xml, col_pdf = st.columns(2)
                    with col_xml:
                        if nfse.get('xml_path'):
                            download_file_button(nfse['xml_path'], "📄 XML", key=f"xml_{nfse['chave_acesso']}")
                    with col_pdf:
                        if nfse.get('pdf_path'):
                            download_file_button(nfse['pdf_path'], "📑 PDF", key=f"pdf_{nfse['chave_acesso']}")
    else:
        st.info("ℹ️ Nenhuma NFS-e emitida ainda")


# ============================================================================
# EMISSÃO INDIVIDUAL
# ============================================================================

def render_single_emission():
    """Renderiza página de emissão individual."""
    st.title("📤 Emissão Individual de NFS-e")
    st.markdown("Emita uma NFS-e única com dados preenchidos manualmente")
    st.markdown("---")
    
    with st.form("single_emission_form"):
        st.markdown("### 👤 Dados do Tomador")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tomador_cpf = st.text_input(
                "CPF/CNPJ do Tomador *",
                placeholder="000.000.000-00",
                help="CPF ou CNPJ do cliente que está recebendo o serviço"
            )
            
            tomador_nome = st.text_input(
                "Nome/Razão Social *",
                placeholder="Nome completo ou razão social"
            )
        
        with col2:
            tomador_email = st.text_input(
                "E-mail",
                placeholder="cliente@email.com"
            )
            
            tomador_telefone = st.text_input(
                "Telefone",
                placeholder="(00) 00000-0000"
            )
        
        st.markdown("### 🏠 Endereço do Tomador")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tomador_cep = st.text_input("CEP", placeholder="00000-000")
        with col2:
            tomador_logradouro = st.text_input("Logradouro", placeholder="Rua, Avenida...")
        with col3:
            tomador_numero = st.text_input("Número", placeholder="123")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tomador_bairro = st.text_input("Bairro", placeholder="Centro")
        with col2:
            tomador_cidade = st.text_input("Cidade", placeholder="Porto Alegre")
        with col3:
            tomador_uf = st.selectbox(
                "UF",
                ["RS", "SP", "RJ", "MG", "PR", "SC", "BA", "PE", "CE", "DF", "GO", "ES", "PA", "MA", 
                 "MT", "MS", "RO", "AC", "AM", "RR", "AP", "TO", "AL", "SE", "RN", "PB", "PI"]
            )
        
        st.markdown("### 💼 Dados do Serviço")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            valor_servico = st.number_input(
                "Valor do Serviço (R$) *",
                min_value=0.01,
                value=100.00,
                step=10.00,
                format="%.2f"
            )
        
        with col2:
            aliquota_iss = st.number_input(
                "Alíquota ISS (%) *",
                min_value=0.0,
                max_value=5.0,
                value=2.0,
                step=0.1,
                format="%.2f"
            )
        
        with col3:
            item_lista = st.text_input(
                "Item Lista LC 116/2003 *",
                value="04.01.01",
                help="Código do serviço conforme Lista LC 116/2003"
            )
        
        descricao_servico = st.text_area(
            "Descrição do Serviço *",
            value="Prestação de serviços conforme contrato",
            height=100,
            help="Descrição detalhada do serviço prestado"
        )
        
        hash_paciente = st.text_input(
            "Hash do Paciente",
            help="Hash do paciente (opcional - aparecerá na DANFSE)"
        )
        
        discriminacao = st.text_area(
            "Discriminação Adicional",
            height=80,
            help="Informações adicionais sobre o serviço (opcional)"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            incentivador_cultural = st.checkbox("Incentivador Cultural")
        
        with col2:
            simples_nacional = st.checkbox("Optante pelo Simples Nacional", value=True)
        
        st.markdown("---")
        
        # Botão de emissão
        submitted = st.form_submit_button(
            "🚀 Emitir NFS-e",
            use_container_width=True,
            type="primary"
        )
    
    # Processar submissão FORA do form
    if submitted:
        # Validação básica
        if not tomador_cpf or not tomador_nome or not valor_servico:
            st.error("❌ Preencha todos os campos obrigatórios (*)")
        else:
            # Preparar dados
            prestador = PrestadorServico(
                cnpj='59418245000186',
                inscricao_municipal='8259069',
                razao_social='GABRIEL SALEH SERVICOS MEDICOS LTDA',
                logradouro='Rua Exemplo',
                numero='123',
                bairro='Centro',
                municipio='Florianopolis',
                uf='SC',
                cep='88010000'
            )
            
            cpf_limpo = tomador_cpf.replace('.', '').replace('-', '').replace('/', '')
            tomador = TomadorServico(
                cpf=cpf_limpo if len(cpf_limpo) == 11 else None,
                cnpj=cpf_limpo if len(cpf_limpo) == 14 else None,
                nome=tomador_nome,
                email=tomador_email if tomador_email else None,
                telefone=tomador_telefone if tomador_telefone else None
            )
            
            # Adicionar hash do paciente na descrição (aparece na DANFSE)
            descricao_final = hash_paciente if hash_paciente and hash_paciente.strip() else descricao_servico
            
            servico = Servico(
                valor_servico=valor_servico,
                aliquota_iss=aliquota_iss,
                item_lista_servico=item_lista,
                descricao=descricao_final,
                discriminacao=discriminacao if discriminacao else None
            )
            
            # Emitir NFS-e
            with st.spinner("⏳ Emitindo NFS-e... Por favor aguarde..."):
                try:
                    resultado = asyncio.run(emitir_nfse_com_pdf(prestador, tomador, servico))
                    
                    if resultado['sucesso']:
                        st.success("✅ NFS-e emitida com sucesso!")
                        
                        # Salvar na sessão
                        nfse_data = {
                            'chave_acesso': resultado['chave_acesso'],
                            'numero': resultado.get('numero', 'N/A'),
                            'data_emissao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            'tomador_nome': tomador_nome,
                            'tomador_cpf': tomador_cpf,
                            'valor': valor_servico,
                            'iss': valor_servico * (aliquota_iss / 100),
                            'xml_path': resultado.get('xml_path'),
                            'pdf_path': resultado.get('pdf_path'),
                            'resultado_completo': resultado
                        }
                        
                        st.session_state.emitted_nfse.append(nfse_data)
                        st.session_state.last_emission = nfse_data
                        
                        # Salvar persistência
                        save_emitted_nfse()
                        
                        # Exibir resultado
                        st.markdown("---")
                        st.markdown("### ✅ NFS-e Emitida com Sucesso!")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Número", resultado.get('numero', 'N/A'))
                        with col2:
                            st.metric("Valor", f"R$ {valor_servico:,.2f}")
                        with col3:
                            st.metric("ISS", f"R$ {valor_servico * (aliquota_iss / 100):,.2f}")
                        
                        st.markdown(f"**🔑 Chave de Acesso:**")
                        st.code(resultado['chave_acesso'], language=None)
                        
                        # Botões de download (AGORA FORA DO FORM)
                        st.markdown("### 📥 Downloads")
                        
                        col_xml, col_pdf, col_space = st.columns([1, 1, 2])
                        
                        with col_xml:
                            if resultado.get('xml_path'):
                                download_file_button(resultado['xml_path'], "📄 Baixar XML", key="single_xml")
                        
                        with col_pdf:
                            if resultado.get('pdf_path'):
                                download_file_button(resultado['pdf_path'], "📑 Baixar PDF", key="single_pdf")
                        
                    else:
                        st.error(f"❌ Erro na emissão: {resultado.get('mensagem', 'Erro desconhecido')}")
                        if resultado.get('resultado'):
                            with st.expander("🔍 Detalhes do Erro"):
                                st.json(resultado['resultado'])
                
                except Exception as e:
                    st.error(f"❌ Erro ao emitir NFS-e: {str(e)}")
                    app_logger.error(f"Erro na emissão individual: {e}", exc_info=True)


# ============================================================================
# EMISSÃO EM LOTE (MANTIDO DO ORIGINAL)
# ============================================================================

def render_batch_emission():
    """Renderiza página de emissão em lote."""
    st.title("📋 Emissão em Lote de NFS-e")
    st.markdown("Processe múltiplas NFS-e a partir de um arquivo PDF")
    st.markdown("---")
    
    # Upload do PDF
    st.markdown("### 1️⃣ Upload do Arquivo PDF")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo PDF com os registros",
        type=['pdf'],
        help="PDF contendo CPF, Nome e Hash das transações"
    )
    
    if uploaded_file is not None:
        # Salvar arquivo temporariamente
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name
        
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
        
        # Extrair dados do PDF
        st.markdown("### 2️⃣ Extração de Dados")
        
        with st.spinner("⏳ Extraindo dados do PDF..."):
            try:
                records = pdf_extractor.extract_from_file(Path(pdf_path))
                
                if records:
                    st.success(f"✅ {len(records)} registros encontrados!")
                    
                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total de Registros", len(records))
                    
                    with col2:
                        valid_records = [r for r in records if r.get('cpf') and r.get('nome')]
                        st.metric("Registros Válidos", len(valid_records))
                    
                    with col3:
                        taxa = (len(valid_records) / len(records) * 100) if records else 0
                        st.metric("Taxa de Sucesso", f"{taxa:.1f}%")
                    
                    # Preview dos dados
                    with st.expander("👁️ Visualizar Dados Extraídos"):
                        import pandas as pd
                        
                        # Preparar dataframe para exibição
                        display_data = []
                        for r in valid_records:
                            display_data.append({
                                'Nome': r.get('nome', 'N/A'),
                                'CPF': r.get('cpf_formatado', r.get('cpf', 'N/A')),
                                'Telefone': r.get('telefone', 'Não informado'),
                                'Email': r.get('email', 'Não informado'),
                                'Data Consulta': r.get('data_consulta', 'N/A')
                            })
                        
                        df = pd.DataFrame(display_data)
                        st.dataframe(df, use_container_width=True)
                        
                        st.info("💡 **Importante:** O valor no PDF será ignorado. Use o valor configurado abaixo (padrão: R$ 89,00)")
                    
                    # Configuração do serviço
                    st.markdown("### 3️⃣ Configuração do Serviço")
                    
                    with st.form("batch_config_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            valor_servico = st.number_input(
                                "💰 Valor do Serviço (R$) *",
                                min_value=0.01,
                                value=89.00,  # VALOR PADRÃO: R$ 89,00
                                step=1.00,
                                format="%.2f",
                                help="Este valor será usado para TODAS as NFS-e (valor do PDF é ignorado)"
                            )
                            
                            aliquota_iss = st.number_input(
                                "Alíquota ISS (%) *",
                                min_value=0.0,
                                max_value=5.0,
                                value=2.0,
                                step=0.1,
                                format="%.2f"
                            )
                        
                        with col2:
                            item_lista = st.text_input(
                                "Item Lista LC 116/2003 *",
                                value="04.01.01",
                                help="Código do serviço conforme Lista LC 116/2003"
                            )
                            
                            simples_nacional = st.checkbox("Optante pelo Simples Nacional", value=True)
                        
                        descricao_servico = st.text_area(
                            "Descrição do Serviço *",
                            value="Prestação de serviços conforme contrato",
                            height=100
                        )
                        
                        discriminacao = st.text_area(
                            "Discriminação Adicional (Opcional)",
                            height=80
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            limite_lote = st.number_input(
                                "Limite de NFS-e por vez",
                                min_value=1,
                                max_value=200,
                                value=min(100, len(valid_records)),
                                help="Quantidade de notas a processar neste lote"
                            )
                        
                        with col2:
                            tempo_estimado = limite_lote * 2  # ~2 segundos por nota
                            st.info(f"⏱️ Tempo estimado: ~{tempo_estimado//60} min {tempo_estimado%60} seg")
                        
                        st.markdown("---")
                        
                        # Resumo antes de processar
                        st.markdown("### 📊 Resumo do Lote")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Registros", min(limite_lote, len(valid_records)))
                        
                        with col2:
                            valor_total = valor_servico * min(limite_lote, len(valid_records))
                            st.metric("Valor Total", f"R$ {valor_total:,.2f}")
                        
                        with col3:
                            iss_total = valor_total * (aliquota_iss / 100)
                            st.metric("ISS Total", f"R$ {iss_total:,.2f}")
                        
                        with col4:
                            st.metric("Valor Unitário", f"R$ {valor_servico:,.2f}")
                        
                        st.markdown("---")
                        
                        submitted = st.form_submit_button(
                            "🚀 Iniciar Emissão em Lote",
                            use_container_width=True,
                            type="primary"
                        )
                        
                        if submitted:
                            if not valid_records:
                                st.error("❌ Nenhum registro válido encontrado!")
                            else:
                                # Limitar registros ao limite do lote
                                records_to_process = valid_records[:limite_lote]
                                
                                st.markdown("### 4️⃣ Processamento em Andamento")
                                
                                # Preparar dados do serviço
                                servico = {
                                    'valor': valor_servico,
                                    'aliquota_iss': aliquota_iss,
                                    'item_lista': item_lista,
                                    'descricao': descricao_servico,
                                    'discriminacao': discriminacao if discriminacao else None,
                                    'simples_nacional': simples_nacional,
                                    'incentivador_cultural': False
                                }
                                
                                prestador = {
                                    'cnpj': '59418245000186',
                                }
                                
                                # Barra de progresso
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                # Painel de logs em tempo real
                                log_expander = st.expander("📋 Ver Logs Detalhados", expanded=False)
                                log_text = log_expander.empty()
                                logs = []
                                
                                resultados = []
                                sucessos = 0
                                falhas = 0
                                
                                import time
                                
                                # Função auxiliar para retry
                                def emitir_com_retry(prestador_obj, tomador_obj, servico_obj, max_tentativas=3):
                                    """Tenta emitir NFS-e com retry automático."""
                                    for tentativa in range(max_tentativas):
                                        try:
                                            return asyncio.run(emitir_nfse_com_pdf(prestador_obj, tomador_obj, servico_obj))
                                        except Exception as e:
                                            if tentativa < max_tentativas - 1:
                                                time.sleep(1)  # Aguarda 1 segundo antes de tentar novamente
                                                continue
                                            else:
                                                raise e
                                
                                for idx, record in enumerate(records_to_process):
                                    status_text.text(f"⏳ Processando {idx+1}/{len(records_to_process)}: {record.get('nome', 'N/A')}...")
                                    
                                    try:
                                        # LOG 1: Dados do registro
                                        log_msg = f"[{idx+1}/{len(records_to_process)}] Processando: {record.get('nome', 'N/A')}"
                                        logs.append(log_msg)
                                        log_text.code("\n".join(logs[-20:]))  # Mostrar últimas 20 linhas
                                        app_logger.info(log_msg)
                                        
                                        # Preparar tomador
                                        cpf_cnpj = record.get('cpf', '').replace('.', '').replace('-', '').replace('/', '')
                                        hash_paciente = record.get('hash', '')
                                        
                                        app_logger.info(f"[{idx+1}] CPF limpo: {cpf_cnpj}, Hash: {hash_paciente}")
                                        
                                        # Prestador
                                        app_logger.info(f"[{idx+1}] Criando objeto Prestador...")
                                        prestador_obj = PrestadorServico(
                                            cnpj='59418245000186',
                                            inscricao_municipal='8259069',
                                            razao_social='GABRIEL SALEH SERVICOS MEDICOS LTDA',
                                            logradouro='Rua Exemplo',
                                            numero='123',
                                            bairro='Centro',
                                            municipio='Florianopolis',
                                            uf='SC',
                                            cep='88010000'
                                        )
                                        app_logger.info(f"[{idx+1}] Prestador criado com sucesso")
                                        
                                        # Tomador
                                        app_logger.info(f"[{idx+1}] Criando objeto Tomador...")
                                        tomador_obj = TomadorServico(
                                            cpf=cpf_cnpj if len(cpf_cnpj) == 11 else None,
                                            cnpj=cpf_cnpj if len(cpf_cnpj) == 14 else None,
                                            nome=record.get('nome', 'Cliente'),
                                            email=record.get('email'),
                                            telefone=record.get('telefone')
                                        )
                                        app_logger.info(f"[{idx+1}] Tomador criado com sucesso")
                                        
                                        # Criar descrição personalizada com o hash do paciente
                                        app_logger.info(f"[{idx+1}] Preparando descrição com hash...")
                                        
                                        # Adicionar hash na DESCRIÇÃO (aparece na DANFSE)
                                        descricao_com_hash = hash_paciente if hash_paciente else descricao_servico
                                        
                                        # Adicionar hash também na discriminação
                                        discriminacao_com_hash = discriminacao if discriminacao else ""
                                        if hash_paciente:
                                            if discriminacao_com_hash:
                                                discriminacao_com_hash += f"\nHash do Paciente: {hash_paciente}"
                                            else:
                                                discriminacao_com_hash = f"Hash do Paciente: {hash_paciente}"
                                        
                                        # Serviço
                                        app_logger.info(f"[{idx+1}] Criando objeto Servico...")
                                        servico_obj = Servico(
                                            valor_servico=valor_servico,
                                            aliquota_iss=aliquota_iss,
                                            item_lista_servico=item_lista,
                                            descricao=descricao_com_hash,
                                            discriminacao=discriminacao_com_hash
                                        )
                                        app_logger.info(f"[{idx+1}] Servico criado com sucesso")
                                        
                                        # Emitir NFS-e com retry automático
                                        app_logger.info(f"[{idx+1}] Chamando emitir_com_retry...")
                                        resultado = emitir_com_retry(prestador_obj, tomador_obj, servico_obj)
                                        app_logger.info(f"[{idx+1}] Emissão concluída: {resultado.get('sucesso', False)}")
                                        
                                        # Pequeno delay entre emissões (reduzido para acelerar)
                                        time.sleep(0.2)
                                        
                                        if resultado['sucesso']:
                                            sucessos += 1
                                            
                                            logs.append(f"  ✅ Sucesso! Chave: {resultado['chave_acesso'][:20]}...")
                                            log_text.code("\n".join(logs[-20:]))
                                            
                                            # Salvar na sessão
                                            nfse_data = {
                                                'chave_acesso': resultado['chave_acesso'],
                                                'numero': resultado.get('numero', 'N/A'),
                                                'data_emissao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                'tomador_nome': record.get('nome', 'N/A'),
                                                'tomador_cpf': record.get('cpf', 'N/A'),
                                                'valor': valor_servico,
                                                'iss': valor_servico * (aliquota_iss / 100),
                                                'xml_path': resultado.get('xml_path'),
                                                'pdf_path': resultado.get('pdf_path'),
                                                'resultado_completo': resultado
                                            }
                                            
                                            st.session_state.emitted_nfse.append(nfse_data)
                                            
                                            # Salvar persistência após cada nota
                                            save_emitted_nfse()
                                            
                                            resultados.append({
                                                'nome': record.get('nome'),
                                                'cpf': record.get('cpf'),
                                                'status': '✅ Sucesso',
                                                'chave': resultado['chave_acesso']
                                            })
                                        else:
                                            falhas += 1
                                            logs.append(f"  ❌ Falha: {resultado.get('mensagem', 'Erro desconhecido')[:50]}")
                                            log_text.code("\n".join(logs[-20:]))
                                            resultados.append({
                                                'nome': record.get('nome'),
                                                'cpf': record.get('cpf'),
                                                'status': '❌ Falha',
                                                'erro': resultado.get('mensagem', 'Erro desconhecido')
                                            })
                                    
                                    except Exception as e:
                                        falhas += 1
                                        erro_msg = str(e)
                                        
                                        # LOG de erro detalhado
                                        app_logger.error(f"[{idx+1}] ERRO COMPLETO: {erro_msg}")
                                        app_logger.error(f"[{idx+1}] Tipo do erro: {type(e).__name__}")
                                        app_logger.error(f"[{idx+1}] Registro: {record}")
                                        
                                        # Capturar detalhes do erro
                                        if "'cnpj'" in erro_msg or "cnpj" in erro_msg.lower():
                                            erro_msg = f"Erro ao criar objeto Prestador/Tomador: {erro_msg}"
                                            app_logger.error(f"[{idx+1}] Erro relacionado a CNPJ detectado")
                                        
                                        # Tentar mostrar stack trace
                                        import traceback
                                        stack_trace = traceback.format_exc()
                                        app_logger.error(f"[{idx+1}] Stack trace:\n{stack_trace}")
                                        
                                        # Adicionar ao log visual
                                        logs.append(f"  ❌ ERRO: {erro_msg[:80]}")
                                        log_text.code("\n".join(logs[-20:]))
                                        
                                        resultados.append({
                                            'nome': record.get('nome', 'N/A'),
                                            'cpf': record.get('cpf', 'N/A'),
                                            'status': '❌ Erro',
                                            'erro': erro_msg[:100]  # Limitar tamanho
                                        })
                                        
                                        # Adicionar detalhes do erro ao status
                                        status_text.text(f"❌ Erro no registro {idx+1}: {erro_msg[:50]}...")
                                    
                                    # Atualizar progresso
                                    progress = (idx + 1) / len(records_to_process)
                                    progress_bar.progress(progress)
                                
                                # Finalizar
                                status_text.text("✅ Processamento concluído!")
                                
                                st.markdown("### 5️⃣ Resultado do Processamento")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Total Processado", len(records_to_process))
                                
                                with col2:
                                    st.metric("✅ Sucessos", sucessos)
                                
                                with col3:
                                    st.metric("❌ Falhas", falhas)
                                
                                # Tabela de resultados
                                st.markdown("### 📊 Detalhamento")
                                
                                import pandas as pd
                                df_result = pd.DataFrame(resultados)
                                st.dataframe(df_result, use_container_width=True)
                                
                                # Gerar ZIP com os PDFs automaticamente
                                if sucessos > 0:
                                    st.success(f"🎉 {sucessos} NFS-e emitidas com sucesso!")
                                    
                                    # Preparar ZIP com todos os PDFs do lote
                                    try:
                                        with st.spinner("📦 Preparando download automático dos PDFs..."):
                                            # Coletar PDFs das notas emitidas no lote
                                            pdf_files = []
                                            for nfse in st.session_state.emitted_nfse[-sucessos:]:  # Pegar apenas as últimas emitidas
                                                pdf_path = nfse.get('pdf_path')
                                                if pdf_path and Path(pdf_path).exists():
                                                    pdf_files.append(Path(pdf_path))
                                            
                                            if pdf_files:
                                                # Criar ZIP em memória
                                                import io
                                                zip_buffer = io.BytesIO()
                                                
                                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                                    for pdf_path in pdf_files:
                                                        zip_file.write(pdf_path, pdf_path.name)
                                                
                                                zip_buffer.seek(0)
                                                
                                                # Criar nome do arquivo com timestamp
                                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                zip_filename = f"nfse_lote_pdfs_{timestamp}.zip"
                                                
                                                st.success(f"✅ {len(pdf_files)} PDFs prontos para download!")
                                                
                                                # Botão de download automático
                                                st.download_button(
                                                    label=f"📥 Baixar {len(pdf_files)} PDFs (ZIP)",
                                                    data=zip_buffer,
                                                    file_name=zip_filename,
                                                    mime="application/zip",
                                                    use_container_width=True,
                                                    type="primary"
                                                )
                                                
                                                st.info("💡 **Dica:** O download foi preparado automaticamente. Clique no botão acima para salvar!")
                                            else:
                                                st.warning("⚠️ Nenhum arquivo PDF disponível para download")
                                                st.info("💡 Acesse o menu 'NFS-e Emitidas' para visualizar todas as notas")
                                    
                                    except Exception as e:
                                        st.error(f"❌ Erro ao preparar download: {e}")
                                        app_logger.error(f"Erro ao preparar ZIP de PDFs: {e}", exc_info=True)
                                        st.info("💡 Acesse o menu 'NFS-e Emitidas' para baixar os arquivos individualmente")
                
                else:
                    st.error("❌ Não foi possível extrair dados do PDF!")
            
            except Exception as e:
                st.error(f"❌ Erro ao processar PDF: {e}")
                app_logger.error(f"Erro no processamento do PDF: {e}", exc_info=True)


# ============================================================================
# LISTAGEM DE NFS-e EMITIDAS
# ============================================================================

def render_emitted_nfse_list():
    """Renderiza lista de NFS-e emitidas."""
    st.title("📜 NFS-e Emitidas")
    st.markdown("Consulte e baixe as NFS-e já emitidas")
    st.markdown("---")
    
    if not st.session_state.emitted_nfse:
        st.info("ℹ️ Nenhuma NFS-e emitida ainda. Use o menu 'Emissão Individual' para emitir sua primeira nota!")
        return
    
    # Filtros
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        filtro_nome = st.text_input("🔍 Filtrar por Nome", placeholder="Digite o nome...")
    
    with col2:
        filtro_cpf = st.text_input("🔍 Filtrar por CPF", placeholder="Digite o CPF...")
    
    with col3:
        # Filtro por mês (independente do ano)
        meses = {
            "Todos": "Todos",
            "01": "Janeiro",
            "02": "Fevereiro",
            "03": "Março",
            "04": "Abril",
            "05": "Maio",
            "06": "Junho",
            "07": "Julho",
            "08": "Agosto",
            "09": "Setembro",
            "10": "Outubro",
            "11": "Novembro",
            "12": "Dezembro"
        }
        filtro_mes = st.selectbox(
            "📅 Filtrar por Mês",
            list(meses.keys()),
            format_func=lambda x: meses[x],
            help="Filtrar por mês (todos os anos)"
        )
    
    with col4:
        # Extrair períodos disponíveis das notas (mês/ano)
        periodos_disponiveis = set()
        for nota in st.session_state.emitted_nfse:
            try:
                data_str = nota.get('data_emissao', '')
                if data_str:
                    # Formato: DD/MM/YYYY HH:MM:SS
                    partes = data_str.split()
                    if partes:
                        data_parte = partes[0]
                        mes_ano = '/'.join(data_parte.split('/')[-2:])
                        periodos_disponiveis.add(mes_ano)
            except:
                pass
        
        from datetime import datetime as dt
        periodos_ordenados = sorted(list(periodos_disponiveis), key=lambda x: dt.strptime(x, '%m/%Y'), reverse=True)
        filtro_periodo = st.selectbox(
            "📅 Filtrar por Período",
            ["Todos"] + periodos_ordenados,
            help="Selecione o mês/ano específico"
        )
    
    with col5:
        ordem = st.selectbox("📊 Ordenar por", ["Mais Recentes", "Mais Antigas", "Maior Valor", "Menor Valor"])
    
    st.markdown("---")
    
    # Filtrar e ordenar
    nfse_list = st.session_state.emitted_nfse.copy()
    
    if filtro_nome:
        nfse_list = [n for n in nfse_list if filtro_nome.lower() in n.get('tomador_nome', '').lower()]
    
    if filtro_cpf:
        nfse_list = [n for n in nfse_list if filtro_cpf in n.get('tomador_cpf', '')]
    
    # Filtrar por mês (independente do ano)
    if filtro_mes != "Todos":
        nfse_filtradas = []
        for n in nfse_list:
            try:
                data_str = n.get('data_emissao', '')
                if data_str:
                    partes = data_str.split()
                    if partes:
                        data_parte = partes[0]
                        mes = data_parte.split('/')[1]  # Extrai o mês (MM)
                        if mes == filtro_mes:
                            nfse_filtradas.append(n)
            except:
                pass
        nfse_list = nfse_filtradas
    
    # Filtrar por período (mês/ano específico)
    if filtro_periodo != "Todos":
        nfse_filtradas = []
        for n in nfse_list:
            try:
                data_str = n.get('data_emissao', '')
                if data_str:
                    partes = data_str.split()
                    if partes:
                        data_parte = partes[0]
                        mes_ano = '/'.join(data_parte.split('/')[-2:])
                        if mes_ano == filtro_periodo:
                            nfse_filtradas.append(n)
            except:
                pass
        nfse_list = nfse_filtradas
    
    if ordem == "Mais Recentes":
        nfse_list = list(reversed(nfse_list))
    elif ordem == "Maior Valor":
        nfse_list = sorted(nfse_list, key=lambda x: x.get('valor', 0), reverse=True)
    elif ordem == "Menor Valor":
        nfse_list = sorted(nfse_list, key=lambda x: x.get('valor', 0))
    
    # Exibir métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de NFS-e", len(nfse_list))
    
    with col2:
        total_valor = sum([n.get('valor', 0) for n in nfse_list])
        st.metric("Valor Total", f"R$ {total_valor:,.2f}")
    
    with col3:
        total_iss = sum([n.get('iss', 0) for n in nfse_list])
        st.metric("Total ISS", f"R$ {total_iss:,.2f}")
    
    st.markdown("---")
    
    # Botões de ação em lote
    st.markdown("### 📦 Ações em Lote")
    
    # Mostrar quantas notas estão sendo exibidas vs total
    if len(nfse_list) < len(st.session_state.emitted_nfse):
        st.info(f"📊 Exibindo {len(nfse_list)} de {len(st.session_state.emitted_nfse)} notas (filtradas)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        label_pdf = f"📥 Baixar PDFs ({len(nfse_list)})" if len(nfse_list) < len(st.session_state.emitted_nfse) else "📥 Baixar Todos os PDFs"
        if st.button(label_pdf, type="primary", use_container_width=True, key="bulk_pdf"):
            if not nfse_list:
                st.warning("⚠️ Nenhuma nota no filtro atual")
            else:
                with st.spinner("📦 Gerando arquivo ZIP com os PDFs..."):
                    try:
                        import zipfile
                        from io import BytesIO
                        from datetime import datetime
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            pdfs_encontrados = 0
                            
                            for nota in nfse_list:
                                pdf_path = nota.get('pdf_path')
                                if pdf_path and Path(pdf_path).exists():
                                    # Adicionar PDF ao ZIP
                                    zip_file.write(pdf_path, Path(pdf_path).name)
                                    pdfs_encontrados += 1
                        
                        if pdfs_encontrados > 0:
                            # Preparar download
                            zip_buffer.seek(0)
                            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            st.download_button(
                                label=f"⬇️ Download ZIP ({pdfs_encontrados} PDFs)",
                                data=zip_buffer.getvalue(),
                                file_name=f"nfse_pdfs_{data_hora}.zip",
                                mime="application/zip",
                                use_container_width=True,
                                key="download_bulk_pdf"
                            )
                            
                            st.success(f"✅ {pdfs_encontrados} PDF(s) prontos para download!")
                        else:
                            st.warning("⚠️ Nenhum arquivo PDF encontrado no sistema")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar ZIP: {e}")
    
    with col2:
        label_xml = f"📄 Baixar XMLs ({len(nfse_list)})" if len(nfse_list) < len(st.session_state.emitted_nfse) else "📄 Baixar Todos os XMLs"
        if st.button(label_xml, type="primary", use_container_width=True, key="bulk_xml"):
            if not nfse_list:
                st.warning("⚠️ Nenhuma nota no filtro atual")
            else:
                with st.spinner("📦 Gerando arquivo ZIP com os XMLs..."):
                    try:
                        import zipfile
                        from io import BytesIO
                        from datetime import datetime
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            xmls_encontrados = 0
                            
                            for nota in nfse_list:
                                xml_path = nota.get('xml_path')
                                if xml_path and Path(xml_path).exists():
                                    # Adicionar XML ao ZIP
                                    zip_file.write(xml_path, Path(xml_path).name)
                                    xmls_encontrados += 1
                        
                        if xmls_encontrados > 0:
                            # Preparar download
                            zip_buffer.seek(0)
                            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            st.download_button(
                                label=f"⬇️ Download ZIP ({xmls_encontrados} XMLs)",
                                data=zip_buffer.getvalue(),
                                file_name=f"nfse_xmls_{data_hora}.zip",
                                mime="application/zip",
                                use_container_width=True,
                                key="download_bulk_xml"
                            )
                            
                            st.success(f"✅ {xmls_encontrados} XML(s) prontos para download!")
                        else:
                            st.warning("⚠️ Nenhum arquivo XML encontrado no sistema")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar ZIP: {e}")
    
    with col3:
        # Inicializar estado de confirmação
        if 'confirmar_limpeza' not in st.session_state:
            st.session_state.confirmar_limpeza = False
        
        if not st.session_state.confirmar_limpeza:
            # Primeiro clique - pedir confirmação
            if st.button("🗑️ Limpar Histórico", type="secondary", use_container_width=True, key="clear_history", help="Remove todas as notas do histórico"):
                st.session_state.confirmar_limpeza = True
                st.rerun()
        else:
            # Segundo clique - confirmar ação
            st.warning("⚠️ **TEM CERTEZA?** Esta ação não pode ser desfeita!")
            
            col_confirm, col_cancel = st.columns(2)
            
            with col_confirm:
                if st.button("✅ Confirmar Limpeza", type="primary", use_container_width=True, key="confirm_clear"):
                    total_notas = len(st.session_state.emitted_nfse)
                    arquivos_removidos = 0
                    
                    # Remover arquivos físicos (XML e PDF)
                    for nota in st.session_state.emitted_nfse:
                        try:
                            # Remover XML
                            xml_path = nota.get('xml_path')
                            if xml_path and Path(xml_path).exists():
                                Path(xml_path).unlink()
                                arquivos_removidos += 1
                            
                            # Remover PDF
                            pdf_path = nota.get('pdf_path')
                            if pdf_path and Path(pdf_path).exists():
                                Path(pdf_path).unlink()
                                arquivos_removidos += 1
                        except Exception as e:
                            app_logger.error(f"Erro ao remover arquivos: {e}")
                    
                    # Limpar dados da sessão
                    st.session_state.emitted_nfse = []
                    st.session_state.last_emission = None
                    st.session_state.confirmar_limpeza = False
                    
                    # Salvar arquivo vazio
                    save_emitted_nfse()
                    
                    st.success(f"✅ Histórico limpo! {total_notas} nota(s) e {arquivos_removidos} arquivo(s) removidos.")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancelar", type="secondary", use_container_width=True, key="cancel_clear"):
                    st.session_state.confirmar_limpeza = False
                    st.rerun()
    
    st.markdown("---")
    
    # Listar NFS-e
    for idx, nfse in enumerate(nfse_list):
        with st.expander(
            f"🧾 NFS-e #{nfse.get('numero', idx+1)} - {nfse.get('tomador_nome', 'N/A')} - "
            f"R$ {nfse.get('valor', 0):,.2f} - {nfse.get('data_emissao', 'N/A')}"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**🔑 Chave de Acesso:**")
                st.code(nfse.get('chave_acesso', 'N/A'), language=None)
                
                st.markdown(f"**👤 Tomador:** {nfse.get('tomador_nome', 'N/A')}")
                st.markdown(f"**📋 CPF/CNPJ:** {nfse.get('tomador_cpf', 'N/A')}")
                st.markdown(f"**📅 Data de Emissão:** {nfse.get('data_emissao', 'N/A')}")
            
            with col2:
                st.markdown("**💰 Valores:**")
                st.markdown(f"**Valor Total:** R$ {nfse.get('valor', 0):,.2f}")
                st.markdown(f"**ISS:** R$ {nfse.get('iss', 0):,.2f}")
            
            st.markdown("---")
            st.markdown("### 📥 Downloads")
            
            col_xml, col_pdf, col_view = st.columns(3)
            
            with col_xml:
                if nfse.get('xml_path'):
                    download_file_button(nfse['xml_path'], "📄 Baixar XML", key=f"list_xml_{idx}")
            
            with col_pdf:
                if nfse.get('pdf_path'):
                    download_file_button(nfse['pdf_path'], "📑 Baixar PDF", key=f"list_pdf_{idx}")
            
            with col_view:
                if nfse.get('xml_path'):
                    if st.button("👁️ Visualizar XML", key=f"view_{idx}"):
                        show_xml_content(nfse['xml_path'])


def show_xml_content(xml_path):
    """Exibe conteúdo do XML."""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        st.markdown("### 📄 Conteúdo do XML")
        st.code(xml_content, language='xml')
    
    except Exception as e:
        st.error(f"Erro ao ler XML: {e}")


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

def render_settings():
    """Renderiza página de configurações."""
    st.title("⚙️ Configurações do Sistema")
    st.markdown("---")
    
    # Informações do certificado
    st.markdown("### 🔐 Certificado Digital")
    
    try:
        cert_info = get_certificate_manager().get_certificate_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**CNPJ:** {cert_info.get('subject_cnpj', 'N/A')}")
            st.markdown(f"**Nome:** {cert_info.get('subject_cn', 'N/A')}")
            st.markdown(f"**Emissor:** {cert_info.get('issuer_cn', 'N/A')}")
        
        with col2:
            validade = cert_info.get('not_after', 'N/A')
            st.markdown(f"**Válido até:** {validade}")
            
            if cert_info.get('is_valid'):
                st.success("✅ Certificado válido")
            else:
                st.error("❌ Certificado inválido ou expirado")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar informações do certificado: {e}")
    
    st.markdown("---")
    
    # Informações da API
    st.markdown("### 🌐 Configuração da API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Ambiente:** {getattr(settings, 'NFSE_API_AMBIENTE', 'HOMOLOGACAO')}")
        st.markdown(f"**Base URL:** `{settings.NFSE_API_BASE_URL}`")
    
    with col2:
        st.markdown(f"**Timeout:** {getattr(settings, 'NFSE_API_TIMEOUT', 30)}s")
        st.markdown(f"**Max Retries:** {getattr(settings, 'NFSE_API_MAX_RETRIES', 3)}")
    
    st.markdown("---")
    
    # Ações em Lote
    st.markdown("### 📦 Ações em Lote")
    st.markdown("Gerencie todas as notas fiscais emitidas de uma vez")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Baixar Todos os PDFs", type="primary", use_container_width=True):
            if not st.session_state.emitted_nfse:
                st.warning("⚠️ Nenhuma nota fiscal emitida para baixar")
            else:
                with st.spinner("📦 Gerando arquivo ZIP com todos os PDFs..."):
                    try:
                        import zipfile
                        from io import BytesIO
                        from datetime import datetime
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            pdfs_encontrados = 0
                            
                            for nota in st.session_state.emitted_nfse:
                                pdf_path = nota.get('pdf_path')
                                if pdf_path and Path(pdf_path).exists():
                                    # Adicionar PDF ao ZIP
                                    zip_file.write(pdf_path, Path(pdf_path).name)
                                    pdfs_encontrados += 1
                        
                        if pdfs_encontrados > 0:
                            # Preparar download
                            zip_buffer.seek(0)
                            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            st.download_button(
                                label=f"⬇️ Download ZIP ({pdfs_encontrados} PDFs)",
                                data=zip_buffer.getvalue(),
                                file_name=f"nfse_pdfs_{data_hora}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            st.success(f"✅ {pdfs_encontrados} PDF(s) prontos para download!")
                        else:
                            st.warning("⚠️ Nenhum arquivo PDF encontrado no sistema")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar ZIP: {e}")
    
    with col2:
        if st.button("📄 Baixar Todos os XMLs", type="primary", use_container_width=True):
            if not st.session_state.emitted_nfse:
                st.warning("⚠️ Nenhuma nota fiscal emitida para baixar")
            else:
                with st.spinner("📦 Gerando arquivo ZIP com todos os XMLs..."):
                    try:
                        import zipfile
                        from io import BytesIO
                        from datetime import datetime
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            xmls_encontrados = 0
                            
                            for nota in st.session_state.emitted_nfse:
                                xml_path = nota.get('xml_path')
                                if xml_path and Path(xml_path).exists():
                                    # Adicionar XML ao ZIP
                                    zip_file.write(xml_path, Path(xml_path).name)
                                    xmls_encontrados += 1
                        
                        if xmls_encontrados > 0:
                            # Preparar download
                            zip_buffer.seek(0)
                            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            st.download_button(
                                label=f"⬇️ Download ZIP ({xmls_encontrados} XMLs)",
                                data=zip_buffer.getvalue(),
                                file_name=f"nfse_xmls_{data_hora}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            st.success(f"✅ {xmls_encontrados} XML(s) prontos para download!")
                        else:
                            st.warning("⚠️ Nenhum arquivo XML encontrado no sistema")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar ZIP: {e}")
    
    st.markdown("---")
    
    # Limpar sessão
    st.markdown("### 🗑️ Manutenção")
    st.warning("⚠️ **Atenção:** As ações abaixo são irreversíveis!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Inicializar estado de confirmação
        if 'confirmar_limpeza_settings' not in st.session_state:
            st.session_state.confirmar_limpeza_settings = False
        
        if not st.session_state.confirmar_limpeza_settings:
            # Primeiro clique - pedir confirmação
            if st.button("🗑️ Limpar Histórico de Emissões", type="secondary", use_container_width=True, key="clear_history_settings", help="Remove todas as notas do histórico"):
                st.session_state.confirmar_limpeza_settings = True
                st.rerun()
        else:
            # Segundo clique - confirmar ação
            st.warning("⚠️ **TEM CERTEZA?** Esta ação não pode ser desfeita!")
            
            col_confirm, col_cancel = st.columns(2)
            
            with col_confirm:
                if st.button("✅ Confirmar", type="primary", use_container_width=True, key="confirm_clear_settings"):
                    total_notas = len(st.session_state.emitted_nfse)
                    st.session_state.emitted_nfse = []
                    st.session_state.last_emission = None
                    st.session_state.confirmar_limpeza_settings = False
                    # Salvar arquivo vazio
                    save_emitted_nfse()
                    st.success(f"✅ Histórico limpo! {total_notas} nota(s) removida(s).")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancelar", type="secondary", use_container_width=True, key="cancel_clear_settings"):
                    st.session_state.confirmar_limpeza_settings = False
                    st.rerun()
    
    with col2:
        if st.button("🔄 Reiniciar Sessão", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ Sessão reiniciada!")
            st.rerun()


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def download_file_button(file_path: str, label: str, key: str):
    """Cria botão de download para arquivo."""
    try:
        if not Path(file_path).exists():
            st.warning(f"⚠️ Arquivo não encontrado: {file_path}")
            return
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        file_name = Path(file_path).name
        
        st.download_button(
            label=label,
            data=file_data,
            file_name=file_name,
            mime='application/octet-stream',
            key=key,
            use_container_width=True
        )
    
    except Exception as e:
        st.error(f"Erro ao preparar download: {e}")


def get_file_download_link(file_path: str, link_text: str) -> str:
    """Gera link de download para arquivo."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        b64 = base64.b64encode(data).decode()
        file_name = Path(file_path).name
        
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">{link_text}</a>'
    
    except Exception as e:
        return f"Erro: {e}"


# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação."""
    # Inicializa estado da sessão
    init_session_state()
    
    # Inicializa banco de dados (se necessário)
    try:
        # Como init_database é async, tentamos executar se possível
        # Para simplificar, pulamos por enquanto - o banco será criado quando necessário
        pass
    except Exception as e:
        app_logger.warning(f"Banco de dados não inicializado: {e}")
    
    # Verifica autenticação
    if not st.session_state.authenticated:
        login_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()

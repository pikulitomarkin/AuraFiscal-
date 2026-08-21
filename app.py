"""
Dashboard Streamlit para Automação de Emissão de NFS-e Nacional.

Sistema de processamento em lote de Notas Fiscais de Serviço Eletrônica
através da API oficial do Gov.br.
"""
import streamlit as st
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Imports do projeto
from config.settings import settings
from config.database import init_database
from src.auth.authentication import auth_manager
from src.pdf.extractor import pdf_extractor
from src.api.nfse_service import get_nfse_service
from src.database.repository import NFSeRepository, LogRepository
from src.models.schemas import ProcessingResult
from src.utils.logger import app_logger
from src.utils.certificate import get_certificate_manager


# Configuração da página
st.set_page_config(
    page_title="NFS-e Automation",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


def login_page():
    """Tela de login."""
    st.title("🔐 Sistema de Automação NFS-e")
    st.markdown("### Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                if username and password:
                    token = auth_manager.login(username, password)
                    
                    if token:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.token = token
                        st.session_state.page = 'dashboard'
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        st.markdown("---")
        st.info("**Demo**: Use as credenciais do arquivo `.env`")


def logout():
    """Realiza logout."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.token = None
    st.session_state.page = 'login'
    st.rerun()


# ============================================================================
# DASHBOARD PRINCIPAL
# ============================================================================

def main_dashboard():
    """Dashboard principal do sistema."""
    
    # Sidebar
    with st.sidebar:
        st.title("📄 NFS-e Automation")
        st.markdown(f"**Usuário:** {st.session_state.username}")
        st.markdown("---")
        
        # Menu de navegação
        page = st.radio(
            "Navegação",
            ["🏠 Início", "📤 Emissão em Lote", "📊 Relatórios", "⚙️ Configurações"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Informações do certificado
        cert_mgr = get_certificate_manager()
        if cert_mgr.is_valid():
            st.success("✅ Certificado Digital Válido")
            info = cert_mgr.get_certificate_info()
            st.caption(f"Válido até: {info['valid_until'][:10]}")
        else:
            st.error("❌ Certificado Inválido ou Ausente")
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            logout()
    
    # Conteúdo principal
    if page == "🏠 Início":
        render_home()
    elif page == "📤 Emissão em Lote":
        render_batch_emission()
    elif page == "📊 Relatórios":
        render_reports()
    elif page == "⚙️ Configurações":
        render_settings()


def render_home():
    """Página inicial com resumo."""
    st.title("🏠 Dashboard - Sistema de Automação NFS-e")
    
    st.markdown("""
    ### Bem-vindo ao Sistema de Automação de NFS-e Nacional
    
    Este sistema permite a emissão automatizada de Notas Fiscais de Serviço Eletrônica
    através da **API Nacional do Gov.br**, processando grandes volumes de registros
    extraídos de arquivos PDF.
    """)
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    # Busca estatísticas do banco (assíncrono)
    repo = NFSeRepository()
    
    try:
        stats = asyncio.run(repo.get_estatisticas(dias=30))
        
        with col1:
            st.metric("Total de Emissões (30d)", stats['total_emissoes'])
        
        with col2:
            st.metric("Sucessos", stats['sucessos'], delta=f"{stats['taxa_sucesso']:.1f}%")
        
        with col3:
            st.metric("Erros", stats['erros'])
        
        with col4:
            st.metric("Taxa de Sucesso", f"{stats['taxa_sucesso']:.1f}%")
    
    except Exception as e:
        st.warning("⚠️ Banco de dados não configurado. Execute as migrações primeiro.")
        app_logger.warning(f"Erro ao buscar estatísticas: {e}")
    
    st.markdown("---")
    
    # Status da API
    st.subheader("🔗 Status da API Nacional")
    
    with st.spinner("Verificando disponibilidade da API..."):
        service = get_nfse_service()
        api_available = asyncio.run(service.consultar_status_api())
        
        if api_available:
            st.success("✅ API Nacional NFS-e está **ONLINE** e disponível")
        else:
            st.error("❌ API Nacional NFS-e está **OFFLINE** ou inacessível")
    
    st.markdown("---")
    
    # Guia rápido
    with st.expander("📖 Guia Rápido de Uso"):
        st.markdown("""
        **Como usar o sistema:**
        
        1. **Preparar PDF**: Certifique-se de que o PDF contém CPF, Nome e Hash de cada transação
        2. **Ir para "Emissão em Lote"**: Navegue pelo menu lateral
        3. **Upload do PDF**: Faça upload do arquivo
        4. **Configurar Serviço**: Preencha os dados do serviço (valor, descrição, etc)
        5. **Iniciar Processamento**: Clique em processar e acompanhe o progresso
        6. **Verificar Resultados**: Consulte os relatórios após conclusão
        
        **Limites:**
        - Mínimo: 1 registro
        - Máximo: 600 registros por lote
        - Formatos aceitos: PDF
        """)


def render_batch_emission():
    """Página de emissão em lote."""
    st.title("📤 Emissão de NFS-e em Lote")
    
    # Abas de navegação
    tab1, tab2, tab3 = st.tabs(["📤 Nova Emissão", "📋 NFS-e Emitidas", "📊 Relatórios"])
    
    with tab1:
        render_new_emission()
    
    with tab2:
        render_emitted_nfse()
    
    with tab3:
        render_reports()


def render_new_emission():
    """Renderiza aba de nova emissão."""
    st.markdown("### 1️⃣ Upload do Arquivo PDF")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo PDF com os registros",
        type=['pdf'],
        help="PDF contendo CPF, Nome e Hash das transações"
    )
    
    if uploaded_file:
        st.success(f"✅ Arquivo carregado: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        # Extração de dados
        st.markdown("### 2️⃣ Extração de Dados")
        
        with st.spinner("Processando PDF..."):
            file_bytes = uploaded_file.read()
            records = pdf_extractor.extract_from_bytes(file_bytes)
            
            if records:
                stats = pdf_extractor.validate_extracted_data(records)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Registros Encontrados", stats['total_registros'])
                with col2:
                    st.metric("Válidos", stats['registros_validos'])
                with col3:
                    st.metric("Taxa de Sucesso", f"{stats['taxa_sucesso']:.1f}%")
                
                # Filtrar apenas válidos
                valid_records = pdf_extractor.filter_valid_records(records)
                
                if valid_records:
                    st.success(f"✅ {len(valid_records)} registros prontos para emissão")
                    
                    # Preview dos dados
                    with st.expander("👁️ Visualizar Dados Extraídos"):
                        import pandas as pd
                        df = pd.DataFrame(valid_records)
                        st.dataframe(df[['nome', 'cpf', 'hash']], use_container_width=True)
                    
                    # Configuração do serviço
                    st.markdown("### 3️⃣ Configuração do Serviço")
                    
                    with st.form("config_servico"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            valor = st.number_input(
                                "Valor de emissão do lote (R$)",
                                min_value=0.01,
                                value=float(getattr(settings, 'VALOR_EMISSAO_LOTE', 50.00)),
                                step=1.00,
                                format="%.2f",
                                help="Valor fixo aplicado a todas as NFS-e deste lote. Altere quando precisar."
                            )
                            
                            aliquota_iss = st.number_input(
                                "Alíquota ISS (%)",
                                min_value=0.0,
                                max_value=5.0,
                                value=2.0,
                                step=0.1
                            )
                        
                        with col2:
                            item_lista = st.text_input(
                                "Item Lista de Serviços (LC 116/2003)",
                                value="1.09",
                                help="Código do serviço conforme Lista LC 116/2003"
                            )
                            
                            simples_nacional = st.checkbox("Optante pelo Simples Nacional")
                        
                        descricao = st.text_area(
                            "Descrição do Serviço",
                            value="Prestação de serviços conforme contrato",
                            height=100
                        )
                        
                        discriminacao = st.text_area(
                            "Discriminação Adicional (Opcional)",
                            height=80
                        )
                        
                        processar = st.form_submit_button(
                            "🚀 Iniciar Processamento",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    # Processamento
                    if processar:
                        if len(valid_records) > settings.MAX_BATCH_SIZE:
                            st.error(f"❌ Limite máximo de {settings.MAX_BATCH_SIZE} registros excedido!")
                        else:
                            process_batch(
                                valid_records,
                                {
                                    'valor': valor,
                                    'aliquota_iss': aliquota_iss,
                                    'item_lista': item_lista,
                                    'descricao': descricao,
                                    'discriminacao': discriminacao,
                                    'simples_nacional': simples_nacional
                                },
                                uploaded_file.name
                            )
                else:
                    st.error("❌ Nenhum registro válido encontrado após filtragem!")
            else:
                st.error("❌ Não foi possível extrair dados do PDF!")


def process_batch(records: List[Dict], config: Dict, filename: str):
    """Processa lote de NFS-e."""
    st.markdown("### 4️⃣ Processamento em Andamento")
    
    # Cria log
    log_repo = LogRepository()
    batch_id = asyncio.run(log_repo.create_log(len(records), filename, st.session_state.username))
    
    # Barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(current, total):
        """Callback para atualizar progresso."""
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(f"Processando: {current}/{total} ({progress*100:.1f}%)")
    
    # Processa
    service = get_nfse_service()
    
    with st.spinner("Emitindo NFS-e..."):
        results = asyncio.run(
            service.emitir_nfse_lote(
                records,
                config,
                callback_progress=update_progress
            )
        )
    
    # Salva resultados
    nfse_repo = NFSeRepository()
    asyncio.run(nfse_repo.save_batch_results(results, st.session_state.username))
    
    # Atualiza log
    sucessos = sum(1 for r in results if r.status == 'sucesso')
    erros = len(results) - sucessos
    asyncio.run(log_repo.update_log(batch_id, sucessos, erros))
    
    # Exibe resultados
    st.markdown("### ✅ Processamento Concluído")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Processado", len(results))
    with col2:
        st.metric("Sucessos", sucessos, delta=f"{sucessos/len(results)*100:.1f}%" if results else "0%")
    with col3:
        st.metric("Erros (requerem atenção)", erros)
    
    # Relatório final: notas que precisam de atenção manual
    import pandas as pd
    requer_atencao = [r for r in results if r.status == "erro"]
    if requer_atencao:
        st.markdown("#### ⚠️ Notas que precisam de atenção manual")
        df_atencao = pd.DataFrame([
            {"Hash": r.hash_transacao, "CPF": r.cpf_tomador, "Nome": r.nome_tomador, "Motivo": r.mensagem or ""}
            for r in requer_atencao
        ])
        st.dataframe(df_atencao, use_container_width=True)
        st.caption("Detalhes destes itens também estão no log da aplicação (idDPS, consulta, desfecho).")
    
    # Tabela de resultados
    df = pd.DataFrame([r.model_dump() for r in results])
    
    st.dataframe(df, use_container_width=True)
    
    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download Resultados (CSV)",
        csv,
        f"nfse_resultados_{batch_id}.csv",
        "text/csv",
        use_container_width=True
    )


def render_reports():
    """Página de relatórios."""
    st.title("📊 Relatórios e Consultas")
    
    st.info("🚧 Funcionalidade em desenvolvimento")
    
    # Placeholder para futuras funcionalidades
    st.markdown("""
    **Relatórios Disponíveis (em breve):**
    - Consulta de NFS-e por CPF
    - Histórico de emissões
    - Relatório de erros
    - Exportação de dados
    """)


def render_settings():
    """Página de configurações."""
    st.title("⚙️ Configurações do Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Certificado", "🏢 Prestador", "📡 API"])
    
    with tab1:
        st.subheader("Certificado Digital A1")
        
        cert_mgr = get_certificate_manager()
        if cert_mgr.is_valid():
            info = cert_mgr.get_certificate_info()
            
            st.success("✅ Certificado Digital Válido")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Titular", info['subject'], disabled=True)
                st.text_input("Emissor", info['issuer'], disabled=True)
                st.text_input("Serial", info['serial_number'], disabled=True)
            
            with col2:
                st.text_input("Válido de", info['valid_from'][:10], disabled=True)
                st.text_input("Válido até", info['valid_until'][:10], disabled=True)
                
                days = info['days_until_expiration']
                if days < 30:
                    st.warning(f"⚠️ Certificado expira em {days} dias!")
                else:
                    st.info(f"ℹ️ {days} dias até expiração")
        else:
            st.error("❌ Certificado não configurado ou inválido")
            st.info("Configure o caminho e senha do certificado no arquivo `.env`")
    
    with tab2:
        st.subheader("Dados do Prestador (Emissor)")
        st.info("🚧 Configuração via interface em desenvolvimento. Use o arquivo de configuração.")
    
    with tab3:
        st.subheader("Configurações da API")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("URL Base", settings.NFSE_API_BASE_URL, disabled=True)
            st.text_input("Timeout (s)", str(settings.NFSE_API_TIMEOUT), disabled=True)
        
        with col2:
            st.text_input("Max Retries", str(settings.NFSE_API_MAX_RETRIES), disabled=True)
            st.text_input("Batch Size", str(settings.CONCURRENT_REQUESTS), disabled=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal."""
    
    # Inicializa sessão
    init_session_state()
    
    # Inicializa banco de dados (primeira vez)
    try:
        asyncio.run(init_database())
    except Exception as e:
        app_logger.warning(f"Aviso ao inicializar BD: {e}")
    
    # Roteamento de páginas
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()

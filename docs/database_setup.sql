-- Script de Criação do Banco de Dados PostgreSQL
-- Execute como superuser (postgres)

-- 1. Criar usuário
CREATE USER nfse_user WITH PASSWORD 'senha_segura_aqui';

-- 2. Criar banco de dados
CREATE DATABASE nfse_db
    WITH 
    OWNER = nfse_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;

-- 3. Conectar ao banco
\c nfse_db

-- 4. Conceder privilégios
GRANT ALL PRIVILEGES ON DATABASE nfse_db TO nfse_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO nfse_user;

-- 5. Criar extensões úteis (opcional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para busca de texto

-- 6. Criar schema de auditoria (opcional)
CREATE SCHEMA IF NOT EXISTS audit;
GRANT ALL ON SCHEMA audit TO nfse_user;

-- ============================================================
-- As tabelas serão criadas automaticamente pelo SQLAlchemy
-- quando você executar: python setup.py
-- ============================================================

-- Estrutura das tabelas (para referência):

/*
-- Tabela: nfse_emissoes
CREATE TABLE nfse_emissoes (
    id SERIAL PRIMARY KEY,
    hash_transacao VARCHAR(64) UNIQUE NOT NULL,
    numero_nfse VARCHAR(20),
    protocolo VARCHAR(50),
    codigo_verificacao VARCHAR(20),
    cpf_tomador VARCHAR(11) NOT NULL,
    nome_tomador VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL,
    mensagem TEXT,
    valor_servico NUMERIC(10, 2),
    valor_iss NUMERIC(10, 2),
    descricao_servico TEXT,
    data_emissao TIMESTAMP,
    data_processamento TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url_nfse VARCHAR(255),
    usuario VARCHAR(50)
);

CREATE INDEX idx_nfse_hash ON nfse_emissoes(hash_transacao);
CREATE INDEX idx_nfse_cpf ON nfse_emissoes(cpf_tomador);
CREATE INDEX idx_nfse_status ON nfse_emissoes(status);
CREATE INDEX idx_nfse_created ON nfse_emissoes(created_at);

-- Tabela: logs_processamento
CREATE TABLE logs_processamento (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(36) UNIQUE NOT NULL,
    total_registros INTEGER NOT NULL,
    sucessos INTEGER DEFAULT 0,
    erros INTEGER DEFAULT 0,
    nome_arquivo VARCHAR(255),
    tamanho_arquivo INTEGER,
    inicio_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fim_processamento TIMESTAMP,
    duracao_segundos INTEGER,
    usuario VARCHAR(50),
    status VARCHAR(20) DEFAULT 'processando',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_batch ON logs_processamento(batch_id);
CREATE INDEX idx_logs_usuario ON logs_processamento(usuario);

-- Tabela: usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(150),
    email VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_usuarios_username ON usuarios(username);
*/

-- ============================================================
-- Views Úteis
-- ============================================================

-- View: Estatísticas Diárias
CREATE OR REPLACE VIEW v_estatisticas_diarias AS
SELECT 
    DATE(created_at) as data,
    COUNT(*) as total_emissoes,
    COUNT(*) FILTER (WHERE status = 'sucesso') as sucessos,
    COUNT(*) FILTER (WHERE status = 'erro') as erros,
    ROUND(COUNT(*) FILTER (WHERE status = 'sucesso')::NUMERIC / COUNT(*) * 100, 2) as taxa_sucesso,
    SUM(valor_servico) as valor_total,
    SUM(valor_iss) as iss_total
FROM nfse_emissoes
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- View: Processamentos Recentes
CREATE OR REPLACE VIEW v_processamentos_recentes AS
SELECT 
    batch_id,
    nome_arquivo,
    total_registros,
    sucessos,
    erros,
    ROUND(sucessos::NUMERIC / total_registros * 100, 2) as taxa_sucesso,
    duracao_segundos,
    inicio_processamento,
    status,
    usuario
FROM logs_processamento
ORDER BY inicio_processamento DESC
LIMIT 50;

-- ============================================================
-- Funções Úteis
-- ============================================================

-- Função: Limpar registros antigos (retenção de 1 ano)
CREATE OR REPLACE FUNCTION limpar_dados_antigos(dias_retencao INTEGER DEFAULT 365)
RETURNS TABLE(tabela TEXT, registros_deletados BIGINT) AS $$
BEGIN
    -- Emissões antigas
    DELETE FROM nfse_emissoes 
    WHERE created_at < CURRENT_DATE - dias_retencao;
    
    GET DIAGNOSTICS registros_deletados = ROW_COUNT;
    tabela := 'nfse_emissoes';
    RETURN NEXT;
    
    -- Logs antigos
    DELETE FROM logs_processamento 
    WHERE created_at < CURRENT_DATE - dias_retencao;
    
    GET DIAGNOSTICS registros_deletados = ROW_COUNT;
    tabela := 'logs_processamento';
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Uso: SELECT * FROM limpar_dados_antigos(365);

-- ============================================================
-- Triggers (opcional)
-- ============================================================

-- Trigger: Atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
CREATE TRIGGER trigger_nfse_updated
BEFORE UPDATE ON nfse_emissoes
FOR EACH ROW
EXECUTE FUNCTION atualizar_updated_at();
*/

-- ============================================================
-- Backup Recomendado
-- ============================================================

-- Comando para backup (executar no terminal):
-- pg_dump -U nfse_user -d nfse_db -F c -b -v -f backup_nfse_$(date +%Y%m%d).dump

-- Comando para restore:
-- pg_restore -U nfse_user -d nfse_db -v backup_nfse_20260111.dump

GRANT SELECT ON ALL TABLES IN SCHEMA public TO nfse_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nfse_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO nfse_user;

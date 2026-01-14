"""
Script para recuperar NFS-e emitidas a partir dos logs do Railway.
Extrai informações das notas dos arquivos de log ou resultado JSON.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

PERSISTENCE_FILE = Path("nfse_emitidas.json")

def extrair_de_json_resultado():
    """Extrai notas dos arquivos resultado_*.json."""
    notas_recuperadas = []
    
    # Buscar todos os arquivos resultado_*.json
    arquivos_resultado = list(Path(".").glob("resultado_*.json"))
    
    print(f"📁 Encontrados {len(arquivos_resultado)} arquivos de resultado")
    
    for arquivo in arquivos_resultado:
        print(f"\n📄 Processando: {arquivo.name}")
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrair informações da nota
            if data.get('sucesso'):
                nota = {
                    'chave_acesso': data.get('chave_acesso', 'N/A'),
                    'numero': data.get('numero', 'N/A'),
                    'data_emissao': data.get('data_emissao', datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                    'tomador_nome': 'Recuperado dos logs',
                    'tomador_cpf': 'N/A',
                    'valor': 0.0,
                    'iss': 0.0,
                    'xml_path': data.get('xml_path', ''),
                    'pdf_path': data.get('pdf_path', ''),
                    'resultado_completo': data,
                    'recuperado_de': str(arquivo.name)
                }
                
                notas_recuperadas.append(nota)
                print(f"  ✅ Nota {nota['numero']} recuperada")
                print(f"  🔑 Chave: {nota['chave_acesso'][:30]}...")
        
        except Exception as e:
            print(f"  ❌ Erro ao processar {arquivo.name}: {e}")
    
    return notas_recuperadas

def extrair_de_xml():
    """Extrai informações básicas dos arquivos XML gerados."""
    notas_recuperadas = []
    
    # Buscar todos os arquivos nfse_*.xml (exceto debug)
    arquivos_xml = [f for f in Path(".").glob("nfse_*.xml") if 'debug' not in f.name]
    
    print(f"\n📁 Encontrados {len(arquivos_xml)} arquivos XML")
    
    for arquivo in arquivos_xml:
        print(f"\n📄 Processando: {arquivo.name}")
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Extrair número da nota do nome do arquivo
            match_numero = re.search(r'nfse_(\d+)\.xml', arquivo.name)
            numero = match_numero.group(1) if match_numero else 'N/A'
            
            # Tentar extrair chave de acesso do XML
            match_chave = re.search(r'<chaveAcesso[^>]*>([^<]+)</chaveAcesso>', conteudo, re.IGNORECASE)
            chave = match_chave.group(1) if match_chave else f"XML_{numero}"
            
            # Tentar extrair valor
            match_valor = re.search(r'<valorServico[^>]*>([^<]+)</valorServico>', conteudo, re.IGNORECASE)
            valor = float(match_valor.group(1)) if match_valor else 0.0
            
            # Tentar extrair nome do tomador
            match_nome = re.search(r'<razaoSocial[^>]*>([^<]+)</razaoSocial>', conteudo, re.IGNORECASE)
            if not match_nome:
                match_nome = re.search(r'<nome[^>]*>([^<]+)</nome>', conteudo, re.IGNORECASE)
            nome_tomador = match_nome.group(1) if match_nome else 'N/A'
            
            # Tentar extrair CPF/CNPJ
            match_cpf = re.search(r'<cpf[^>]*>([^<]+)</cpf>', conteudo, re.IGNORECASE)
            if not match_cpf:
                match_cpf = re.search(r'<cnpj[^>]*>([^<]+)</cnpj>', conteudo, re.IGNORECASE)
            cpf_cnpj = match_cpf.group(1) if match_cpf else 'N/A'
            
            nota = {
                'chave_acesso': chave,
                'numero': numero,
                'data_emissao': datetime.fromtimestamp(arquivo.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                'tomador_nome': nome_tomador,
                'tomador_cpf': cpf_cnpj,
                'valor': valor,
                'iss': valor * 0.05,  # Estimativa 5%
                'xml_path': str(arquivo),
                'pdf_path': '',
                'recuperado_de': str(arquivo.name)
            }
            
            notas_recuperadas.append(nota)
            print(f"  ✅ Nota {nota['numero']} recuperada")
            print(f"  👤 Tomador: {nome_tomador}")
            print(f"  💰 Valor: R$ {valor:.2f}")
        
        except Exception as e:
            print(f"  ❌ Erro ao processar {arquivo.name}: {e}")
    
    return notas_recuperadas

def extrair_de_logs_railway():
    """Guia para extrair informações dos logs do Railway."""
    print("\n" + "="*70)
    print("📋 COMO RECUPERAR NOTAS DOS LOGS DO RAILWAY")
    print("="*70)
    print("""
1. Acesse o painel do Railway: https://railway.app
2. Selecione seu projeto
3. Vá em "Deployments" > "Logs"
4. Procure por linhas que contenham:
   - "NFS-e emitida com sucesso"
   - "Chave de Acesso"
   - "chave_acesso"
   
5. Copie as informações e cole abaixo no formato JSON:

FORMATO ESPERADO:
[
  {
    "chave_acesso": "CHAVE_DA_NOTA",
    "numero": "00001",
    "tomador_nome": "Nome do Cliente",
    "tomador_cpf": "123.456.789-00",
    "valor": 100.00
  }
]

6. Salve em um arquivo chamado: notas_railway.json
7. Execute este script novamente
""")

def carregar_de_arquivo_manual():
    """Carrega notas de um arquivo JSON manual (notas_railway.json)."""
    arquivo = Path("notas_railway.json")
    
    if not arquivo.exists():
        return []
    
    print(f"\n📁 Carregando arquivo manual: {arquivo.name}")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            notas = json.load(f)
        
        # Processar e padronizar notas
        notas_processadas = []
        for nota in notas:
            nota_padrao = {
                'chave_acesso': nota.get('chave_acesso', 'N/A'),
                'numero': nota.get('numero', 'N/A'),
                'data_emissao': nota.get('data_emissao', datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                'tomador_nome': nota.get('tomador_nome', 'N/A'),
                'tomador_cpf': nota.get('tomador_cpf', 'N/A'),
                'valor': nota.get('valor', 0.0),
                'iss': nota.get('iss', nota.get('valor', 0.0) * 0.05),
                'xml_path': nota.get('xml_path', ''),
                'pdf_path': nota.get('pdf_path', ''),
                'recuperado_de': 'notas_railway.json'
            }
            notas_processadas.append(nota_padrao)
            print(f"  ✅ Nota {nota_padrao['numero']} carregada")
        
        return notas_processadas
    
    except Exception as e:
        print(f"  ❌ Erro ao carregar arquivo manual: {e}")
        return []

def mesclar_notas(notas_existentes: List[Dict], notas_novas: List[Dict]) -> List[Dict]:
    """Mescla notas novas com as existentes, evitando duplicatas."""
    chaves_existentes = {nota.get('chave_acesso') for nota in notas_existentes}
    
    notas_adicionadas = 0
    for nota in notas_novas:
        chave = nota.get('chave_acesso')
        if chave not in chaves_existentes and chave != 'N/A':
            notas_existentes.append(nota)
            notas_adicionadas += 1
            chaves_existentes.add(chave)
    
    return notas_existentes, notas_adicionadas

def main():
    """Função principal."""
    print("="*70)
    print("🔄 RECUPERAÇÃO DE NFS-e EMITIDAS")
    print("="*70)
    
    # Carregar notas existentes
    notas_existentes = []
    if PERSISTENCE_FILE.exists():
        try:
            with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
                notas_existentes = json.load(f)
            print(f"\n📊 Notas existentes no sistema: {len(notas_existentes)}")
        except Exception as e:
            print(f"\n⚠️ Erro ao carregar notas existentes: {e}")
    
    # Recuperar notas de diferentes fontes
    print("\n" + "="*70)
    print("🔍 BUSCANDO NOTAS...")
    print("="*70)
    
    todas_notas_recuperadas = []
    
    # 1. Arquivos resultado_*.json
    print("\n1️⃣ Buscando em arquivos resultado_*.json...")
    notas_json = extrair_de_json_resultado()
    todas_notas_recuperadas.extend(notas_json)
    
    # 2. Arquivos XML
    print("\n2️⃣ Buscando em arquivos XML...")
    notas_xml = extrair_de_xml()
    todas_notas_recuperadas.extend(notas_xml)
    
    # 3. Arquivo manual
    print("\n3️⃣ Buscando arquivo manual (notas_railway.json)...")
    notas_manual = carregar_de_arquivo_manual()
    todas_notas_recuperadas.extend(notas_manual)
    
    # Mesclar com notas existentes
    if todas_notas_recuperadas:
        print("\n" + "="*70)
        print("💾 SALVANDO NOTAS RECUPERADAS...")
        print("="*70)
        
        notas_finais, novas_adicionadas = mesclar_notas(notas_existentes, todas_notas_recuperadas)
        
        # Salvar
        try:
            with open(PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
                json.dump(notas_finais, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Salvo com sucesso!")
            print(f"📊 Total de notas recuperadas: {len(todas_notas_recuperadas)}")
            print(f"➕ Novas notas adicionadas: {novas_adicionadas}")
            print(f"📈 Total no sistema agora: {len(notas_finais)}")
            print(f"\n📁 Arquivo atualizado: {PERSISTENCE_FILE}")
        
        except Exception as e:
            print(f"\n❌ Erro ao salvar: {e}")
    else:
        print(f"\n⚠️ Nenhuma nota nova encontrada para recuperar")
    
    # Guia para logs do Railway
    if not Path("notas_railway.json").exists():
        extrair_de_logs_railway()
    
    print("\n" + "="*70)
    print("✨ PROCESSO CONCLUÍDO!")
    print("="*70)
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Reinicie o dashboard Streamlit")
    print("2. As notas recuperadas devem aparecer agora!")
    print("3. Se ainda faltam notas, crie notas_railway.json com os dados dos logs")
    print("="*70)

if __name__ == "__main__":
    main()

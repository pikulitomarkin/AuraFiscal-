"""
Gera DANFSE (Documento Auxiliar da NFS-e) em PDF
Layout oficial baseado no padrão ABRASF
"""
import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


def gerar_danfse(xml_path: str, output_path: str):
    """
    Gera DANFSE (PDF) a partir do XML da NFS-e.
    
    Args:
        xml_path: Caminho para o arquivo XML
        output_path: Caminho para salvar o PDF
    """
    try:
        # Ler XML
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Gerar DANFSE
        danfse = Danfse(xml=xml_content)
        danfse.output(output_path)
        
        return True
        
    except Exception as e:
        print(f"Erro ao gerar DANFSE: {e}")
        return False


def processar_xmls_para_danfse(diretorio_xml: str = "xmls_homologacao"):
    """Processa todos os XMLs e gera DANFSEs."""
    
    print("\n" + "="*80)
    print(" GERAÇÃO DE DANFSE - DOCUMENTO AUXILIAR DA NFS-e")
    print("="*80 + "\n")
    
    xml_dir = Path(diretorio_xml)
    if not xml_dir.exists():
        print(f"Erro: Diretório não encontrado: {xml_dir}")
        return
    
    # Criar diretório de saída
    pdf_dir = Path("danfse_homologacao")
    pdf_dir.mkdir(exist_ok=True)
    print(f"✓ Diretório de saída: {pdf_dir.absolute()}\n")
    
    # Encontrar XMLs
    xml_files = list(xml_dir.glob("nfse_*.xml"))  # Apenas os XMLs de NFS-e, não os comprimidos
    
    if not xml_files:
        print(f"Nenhum arquivo XML encontrado em: {xml_dir}")
        return
    
    print(f"Encontrados {len(xml_files)} arquivos XML\n")
    
    sucesso = 0
    erro = 0
    
    for i, xml_file in enumerate(sorted(xml_files), 1):
        try:
            pdf_file = pdf_dir / xml_file.name.replace('.xml', '_danfse.pdf')
            
            print(f"[{i}/{len(xml_files)}] {xml_file.name}")
            
            if gerar_danfse(str(xml_file), str(pdf_file)):
                print(f"            ✓ DANFSE gerado: {pdf_file.name}\n")
                sucesso += 1
            else:
                print(f"            ✗ Falha ao gerar DANFSE\n")
                erro += 1
                
        except Exception as e:
            print(f"            ✗ Erro: {e}\n")
            erro += 1
    
    print("="*80)
    print(" RESUMO")
    print("="*80 + "\n")
    print(f"Total processado: {len(xml_files)}")
    print(f"Sucesso: {sucesso}")
    print(f"Erros: {erro}")
    print(f"\nLocalização: {pdf_dir.absolute()}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        diretorio = sys.argv[1]
    else:
        diretorio = "xmls_homologacao"
    
    processar_xmls_para_danfse(diretorio)

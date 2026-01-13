"""
Gera PDFs das Notas Fiscais a partir dos XMLs
"""
import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("\n" + "="*80)
    print("INSTALANDO BIBLIOTECA reportlab...")
    print("="*80 + "\n")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    print("\nInstalação concluída! Execute o script novamente.")
    sys.exit(0)


class GeradorPDFNFSe:
    """Gera PDF de NFS-e a partir de XML."""
    
    NAMESPACE = {'ns': 'http://www.sped.fazenda.gov.br/nfse'}
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._criar_estilos_customizados()
    
    def _criar_estilos_customizados(self):
        """Cria estilos personalizados para o PDF."""
        self.styles.add(ParagraphStyle(
            name='Titulo',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#003366'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#003366'),
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='Normal_Bold',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold'
        ))
    
    def extrair_dados_xml(self, xml_path: str) -> dict:
        """Extrai dados do XML da NFS-e."""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        dados = {
            'prestador': {},
            'tomador': {},
            'servico': {},
            'valores': {}
        }
        
        # Prestador
        prestador = root.find('.//ns:Prestador', self.NAMESPACE)
        if prestador is not None:
            dados['prestador'] = {
                'cnpj': self._get_text(prestador, 'ns:CNPJ'),
                'razao_social': self._get_text(prestador, 'ns:RazaoSocial'),
                'nome_fantasia': self._get_text(prestador, 'ns:NomeFantasia'),
                'inscricao_municipal': self._get_text(prestador, 'ns:InscricaoMunicipal'),
                'logradouro': self._get_text(prestador, 'ns:Endereco/ns:Logradouro'),
                'numero': self._get_text(prestador, 'ns:Endereco/ns:Numero'),
                'bairro': self._get_text(prestador, 'ns:Endereco/ns:Bairro'),
                'municipio': self._get_text(prestador, 'ns:Endereco/ns:Municipio'),
                'uf': self._get_text(prestador, 'ns:Endereco/ns:UF'),
                'cep': self._get_text(prestador, 'ns:Endereco/ns:CEP'),
                'email': self._get_text(prestador, 'ns:Email'),
                'telefone': self._get_text(prestador, 'ns:Telefone')
            }
        
        # Tomador
        tomador = root.find('.//ns:Tomador', self.NAMESPACE)
        if tomador is not None:
            dados['tomador'] = {
                'cpf': self._get_text(tomador, 'ns:CPF'),
                'cnpj': self._get_text(tomador, 'ns:CNPJ'),
                'nome': self._get_text(tomador, 'ns:Nome'),
                'logradouro': self._get_text(tomador, 'ns:Endereco/ns:Logradouro'),
                'numero': self._get_text(tomador, 'ns:Endereco/ns:Numero'),
                'bairro': self._get_text(tomador, 'ns:Endereco/ns:Bairro'),
                'municipio': self._get_text(tomador, 'ns:Endereco/ns:Municipio'),
                'uf': self._get_text(tomador, 'ns:Endereco/ns:UF'),
                'cep': self._get_text(tomador, 'ns:Endereco/ns:CEP'),
                'email': self._get_text(tomador, 'ns:Email'),
                'telefone': self._get_text(tomador, 'ns:Telefone')
            }
        
        # Serviço
        servico = root.find('.//ns:Servico', self.NAMESPACE)
        if servico is not None:
            dados['servico'] = {
                'descricao': self._get_text(servico, 'ns:Descricao'),
                'discriminacao': self._get_text(servico, 'ns:Discriminacao'),
                'item_lista': self._get_text(servico, 'ns:ItemListaServico'),
                'codigo_cnae': self._get_text(servico, 'ns:CodigoCNAE')
            }
            
            # Valores
            valores = servico.find('ns:Valores', self.NAMESPACE)
            if valores is not None:
                dados['valores'] = {
                    'valor_servico': self._get_text(valores, 'ns:ValorServicos'),
                    'aliquota_iss': self._get_text(valores, 'ns:AliquotaISS'),
                    'valor_iss': self._get_text(valores, 'ns:ValorISS'),
                    'valor_liquido': self._get_text(valores, 'ns:ValorLiquidoNfse')
                }
        
        return dados
    
    def _get_text(self, element, path):
        """Obtém texto de elemento XML."""
        elem = element.find(path, self.NAMESPACE)
        return elem.text if elem is not None and elem.text else ''
    
    def _formatar_cpf_cnpj(self, valor: str) -> str:
        """Formata CPF ou CNPJ."""
        if not valor:
            return ''
        
        if len(valor) == 11:  # CPF
            return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"
        elif len(valor) == 14:  # CNPJ
            return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}"
        return valor
    
    def _formatar_cep(self, cep: str) -> str:
        """Formata CEP."""
        if not cep or len(cep) != 8:
            return cep
        return f"{cep[:5]}-{cep[5:]}"
    
    def _formatar_valor(self, valor: str) -> str:
        """Formata valor monetário."""
        if not valor:
            return 'R$ 0,00'
        try:
            valor_float = float(valor)
            return f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return valor
    
    def gerar_pdf(self, xml_path: str, output_path: str):
        """Gera PDF da NFS-e."""
        
        # Extrair dados do XML
        dados = self.extrair_dados_xml(xml_path)
        
        # Criar PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elementos = []
        
        # Título
        elementos.append(Paragraph("NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e", self.styles['Titulo']))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Informação de ambiente
        elementos.append(Paragraph(
            "<font color='red'>AMBIENTE DE HOMOLOGAÇÃO - SEM VALOR FISCAL</font>",
            ParagraphStyle('Destaque', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=colors.red, fontSize=10)
        ))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Data de emissão
        data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        elementos.append(Paragraph(f"<b>Data de Emissão:</b> {data_emissao}", self.styles['Normal']))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Prestador
        elementos.append(Paragraph("PRESTADOR DE SERVIÇOS", self.styles['Subtitulo']))
        
        prestador = dados['prestador']
        dados_prestador = [
            ['<b>Razão Social:</b>', prestador.get('razao_social', '')],
            ['<b>Nome Fantasia:</b>', prestador.get('nome_fantasia', '')],
            ['<b>CNPJ:</b>', self._formatar_cpf_cnpj(prestador.get('cnpj', ''))],
            ['<b>Inscrição Municipal:</b>', prestador.get('inscricao_municipal', '')],
            ['<b>Endereço:</b>', f"{prestador.get('logradouro', '')}, {prestador.get('numero', '')}"],
            ['<b>Bairro:</b>', prestador.get('bairro', '')],
            ['<b>Município/UF:</b>', f"{prestador.get('municipio', '')}/{prestador.get('uf', '')}"],
            ['<b>CEP:</b>', self._formatar_cep(prestador.get('cep', ''))],
            ['<b>Email:</b>', prestador.get('email', '')],
            ['<b>Telefone:</b>', prestador.get('telefone', '')]
        ]
        
        tabela_prestador = Table(dados_prestador, colWidths=[4.5*cm, 12*cm])
        tabela_prestador.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabela_prestador)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Tomador
        elementos.append(Paragraph("TOMADOR DE SERVIÇOS", self.styles['Subtitulo']))
        
        tomador = dados['tomador']
        doc_tomador = tomador.get('cpf') or tomador.get('cnpj', '')
        tipo_doc = 'CPF' if len(doc_tomador) == 11 else 'CNPJ'
        
        dados_tomador = [
            ['<b>Nome:</b>', tomador.get('nome', '')],
            [f'<b>{tipo_doc}:</b>', self._formatar_cpf_cnpj(doc_tomador)],
            ['<b>Endereço:</b>', f"{tomador.get('logradouro', '')}, {tomador.get('numero', '')}"],
            ['<b>Bairro:</b>', tomador.get('bairro', '')],
            ['<b>Município/UF:</b>', f"{tomador.get('municipio', '')}/{tomador.get('uf', '')}"],
            ['<b>CEP:</b>', self._formatar_cep(tomador.get('cep', ''))],
            ['<b>Email:</b>', tomador.get('email', '')],
            ['<b>Telefone:</b>', tomador.get('telefone', '')]
        ]
        
        tabela_tomador = Table(dados_tomador, colWidths=[4.5*cm, 12*cm])
        tabela_tomador.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabela_tomador)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Descrição do Serviço
        elementos.append(Paragraph("DISCRIMINAÇÃO DOS SERVIÇOS", self.styles['Subtitulo']))
        
        servico = dados['servico']
        elementos.append(Paragraph(servico.get('descricao', ''), self.styles['Normal']))
        elementos.append(Spacer(1, 0.3*cm))
        
        if servico.get('discriminacao'):
            elementos.append(Paragraph(servico.get('discriminacao', ''), self.styles['Normal']))
            elementos.append(Spacer(1, 0.3*cm))
        
        dados_servico = [
            ['<b>Item Lista de Serviços:</b>', servico.get('item_lista', '')],
            ['<b>Código CNAE:</b>', servico.get('codigo_cnae', '')]
        ]
        
        tabela_servico = Table(dados_servico, colWidths=[4.5*cm, 12*cm])
        tabela_servico.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabela_servico)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Valores
        elementos.append(Paragraph("VALORES", self.styles['Subtitulo']))
        
        valores = dados['valores']
        valor_servico = valores.get('valor_servico', '0')
        aliquota_iss = valores.get('aliquota_iss', '0')
        valor_iss = valores.get('valor_iss', '0')
        
        # Calcular valor líquido se não existir
        valor_liquido = valores.get('valor_liquido')
        if not valor_liquido:
            try:
                valor_liquido = str(float(valor_servico) - float(valor_iss))
            except:
                valor_liquido = valor_servico
        
        dados_valores = [
            ['<b>Valor dos Serviços:</b>', self._formatar_valor(valor_servico)],
            ['<b>Alíquota ISS:</b>', f"{aliquota_iss}%"],
            ['<b>Valor ISS:</b>', self._formatar_valor(valor_iss)],
            ['<b>Valor Líquido da NFS-e:</b>', self._formatar_valor(valor_liquido)]
        ]
        
        tabela_valores = Table(dados_valores, colWidths=[4.5*cm, 12*cm])
        tabela_valores.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#E8F4F8')),
        ]))
        elementos.append(tabela_valores)
        
        # Construir PDF
        doc.build(elementos)


def processar_xmls(diretorio_xml: str = "xmls_homologacao"):
    """Processa todos os XMLs e gera PDFs."""
    
    print("\n" + "="*80)
    print(" GERAÇÃO DE PDFs DAS NOTAS FISCAIS")
    print("="*80 + "\n")
    
    xml_dir = Path(diretorio_xml)
    if not xml_dir.exists():
        print(f"Erro: Diretório não encontrado: {xml_dir}")
        return
    
    # Criar diretório de PDFs
    pdf_dir = Path("pdfs_homologacao")
    pdf_dir.mkdir(exist_ok=True)
    print(f"✓ Diretório de saída: {pdf_dir.absolute()}\n")
    
    # Encontrar XMLs
    xml_files = list(xml_dir.glob("*.xml"))
    
    if not xml_files:
        print(f"Nenhum arquivo XML encontrado em: {xml_dir}")
        return
    
    print(f"Encontrados {len(xml_files)} arquivos XML\n")
    
    gerador = GeradorPDFNFSe()
    
    for i, xml_file in enumerate(sorted(xml_files), 1):
        try:
            pdf_file = pdf_dir / xml_file.name.replace('.xml', '.pdf')
            
            print(f"[{i}/{len(xml_files)}] Processando: {xml_file.name}")
            gerador.gerar_pdf(str(xml_file), str(pdf_file))
            print(f"            ✓ PDF gerado: {pdf_file.name}\n")
            
        except Exception as e:
            print(f"            ✗ Erro: {e}\n")
    
    print("="*80)
    print(" CONCLUÍDO")
    print("="*80 + "\n")
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Total: {len(pdf_files)} PDFs gerados")
    print(f"Localização: {pdf_dir.absolute()}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        diretorio = sys.argv[1]
    else:
        diretorio = "xmls_homologacao"
    
    processar_xmls(diretorio)

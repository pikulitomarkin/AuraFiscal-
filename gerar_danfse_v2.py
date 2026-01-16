"""
Gera DANFSE (Documento Auxiliar da NFS-e) em PDF a partir do XML autorizado.
Layout completo com QR Code para validação da chave de acesso.
"""

from pathlib import Path
from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import qrcode
from io import BytesIO


class GeradorDANFSE:
    """Gerador de DANFSE em PDF."""
    
    def __init__(self, xml_path: str):
        """
        Inicializa gerador.
        
        Args:
            xml_path: Caminho do XML da NFS-e autorizada
        """
        self.xml_path = Path(xml_path)
        self.ns = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}
        
        # Carregar e parsear XML
        xml_content = self.xml_path.read_text(encoding='utf-8')
        self.root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Extrair dados
        self._extrair_dados()
    
    def _extrair_dados(self):
        """Extrai dados do XML."""
        
        inf_nfse = self.root.find('.//nfse:infNFSe', self.ns)
        
        # Chave e número
        id_nfse = inf_nfse.get('Id', '')
        self.chave_acesso = id_nfse.replace('NFS', '') if id_nfse.startswith('NFS') else id_nfse
        self.numero_nfse = inf_nfse.findtext('.//nfse:nNFSe', namespaces=self.ns, default='')
        
        # Status e processamento
        self.status = inf_nfse.findtext('.//nfse:cStat', namespaces=self.ns, default='')
        self.dh_processamento = inf_nfse.findtext('.//nfse:dhProc', namespaces=self.ns, default='')
        
        # Locais
        self.local_emissao = inf_nfse.findtext('.//nfse:xLocEmi', namespaces=self.ns, default='')
        self.local_prestacao = inf_nfse.findtext('.//nfse:xLocPrestacao', namespaces=self.ns, default='')
        
        # Prestador (Emitente)
        emit = inf_nfse.find('.//nfse:emit', self.ns)
        self.prestador = {
            'cnpj': emit.findtext('.//nfse:CNPJ', namespaces=self.ns, default=''),
            'nome': emit.findtext('.//nfse:xNome', namespaces=self.ns, default=''),
            'logradouro': emit.findtext('.//nfse:xLgr', namespaces=self.ns, default=''),
            'numero': emit.findtext('.//nfse:nro', namespaces=self.ns, default=''),
            'bairro': emit.findtext('.//nfse:xBairro', namespaces=self.ns, default=''),
            'uf': emit.findtext('.//nfse:UF', namespaces=self.ns, default=''),
            'cep': emit.findtext('.//nfse:CEP', namespaces=self.ns, default=''),
            'fone': emit.findtext('.//nfse:fone', namespaces=self.ns, default=''),
            'email': emit.findtext('.//nfse:email', namespaces=self.ns, default=''),
        }
        
        # Tomador (do DPS)
        dps = self.root.find('.//nfse:DPS', self.ns)
        toma = dps.find('.//nfse:toma', self.ns) if dps is not None else None
        
        if toma is not None:
            cpf = toma.findtext('.//nfse:CPF', namespaces=self.ns, default='')
            cnpj = toma.findtext('.//nfse:CNPJ', namespaces=self.ns, default='')
            
            self.tomador = {
                'documento': cpf if cpf else cnpj,
                'tipo_doc': 'CPF' if cpf else 'CNPJ',
                'nome': toma.findtext('.//nfse:xNome', namespaces=self.ns, default=''),
            }
        else:
            self.tomador = {'documento': '', 'tipo_doc': '', 'nome': ''}
        
        # Serviço
        serv = dps.find('.//nfse:serv', self.ns) if dps is not None else None
        if serv is not None:
            self.servico = {
                'codigo': serv.findtext('.//nfse:cTribNac', namespaces=self.ns, default=''),
                'descricao': serv.findtext('.//nfse:xDescServ', namespaces=self.ns, default=''),
            }
        else:
            self.servico = {'codigo': '', 'descricao': ''}
        
        # Valores
        valores = inf_nfse.find('.//nfse:valores', self.ns)
        self.valores = {
            'base_calculo': valores.findtext('.//nfse:vBC', namespaces=self.ns, default='0.00'),
            'aliquota': valores.findtext('.//nfse:pAliqAplic', namespaces=self.ns, default='0.00'),
            'iss': valores.findtext('.//nfse:vISSQN', namespaces=self.ns, default='0.00'),
            'liquido': valores.findtext('.//nfse:vLiq', namespaces=self.ns, default='0.00'),
        }
    
    def _gerar_qrcode(self) -> Image:
        """
        Gera QR Code com a chave de acesso da NFS-e.
        
        Returns:
            Imagem do QR Code para o ReportLab
        """
        # Criar QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        
        # Dados do QR Code: URL oficial de consulta pública da NFS-e Nacional
        url_consulta = f"https://www.nfse.gov.br/consultapublica?chave={self.chave_acesso}"
        qr.add_data(url_consulta)
        qr.make(fit=True)
        
        # Gerar imagem
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para formato ReportLab
        buffer = BytesIO()
        img_qr.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Criar Image do ReportLab
        img = Image(buffer, width=3*cm, height=3*cm)
        
        return img
    
    def gerar_pdf(self, output_path: str):
        """
        Gera PDF do DANFSE.
        
        Args:
            output_path: Caminho para salvar o PDF
        """
        
        # Criar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#000080'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        secao_style = ParagraphStyle(
            'Secao',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#000080'),
            spaceAfter=6,
            spaceBefore=10
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            leading=11
        )
        
        # Elementos do documento
        elementos = []
        
        # CABEÇALHO
        elementos.append(Paragraph("NOTA FISCAL DE SERVIÇOS ELETRÔNICA", titulo_style))
        elementos.append(Paragraph("NFS-e (DANFSE - Documento Auxiliar)", subtitulo_style))
        
        # Status
        status_text = "AUTORIZADA" if self.status == "100" else f"STATUS: {self.status}"
        elementos.append(Paragraph(f"<b>{status_text}</b>", subtitulo_style))
        
        elementos.append(Spacer(1, 0.3*cm))
        
        # DADOS DA NFS-e com QR CODE
        elementos.append(Paragraph("DADOS DA NFS-e", secao_style))
        
        # Criar tabela com QR Code
        qr_img = self._gerar_qrcode()
        
        # Tabela principal com dados e QR Code
        dados_nfse_esq = [
            ['Número NFS-e:', self.numero_nfse],
            ['Data/Hora:', self.dh_processamento[:19] if self.dh_processamento else ''],
            ['Local Emissão:', self.local_emissao],
            ['Local Prestação:', self.local_prestacao],
        ]
        
        tabela_esq = Table(dados_nfse_esq, colWidths=[3.5*cm, 6.5*cm])
        tabela_esq.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Tabela QR Code à direita
        qr_legenda = Paragraph("<font size=7><b>Consulte a NFS-e:</b><br/>Aponte a câmera<br/>para o QR Code</font>", subtitulo_style)
        dados_qr = [[qr_img], [qr_legenda]]
        tabela_qr = Table(dados_qr, colWidths=[6*cm])
        tabela_qr.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Combinar tabelas lado a lado
        tabela_principal = Table([[tabela_esq, tabela_qr]], colWidths=[10*cm, 6.5*cm])
        tabela_principal.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elementos.append(tabela_principal)
        
        elementos.append(Spacer(1, 0.3*cm))
        
        # CHAVE DE ACESSO (em destaque)
        chave_style = ParagraphStyle(
            'Chave',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Courier',
            textColor=colors.HexColor('#000080'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        elementos.append(Paragraph(f"<b>CHAVE DE ACESSO:</b><br/>{self.chave_acesso}", chave_style))
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # PRESTADOR
        elementos.append(Paragraph("PRESTADOR DE SERVIÇOS (EMITENTE)", secao_style))
        
        prestador_dados = [
            ['CNPJ:', self.prestador['cnpj']],
            ['Razão Social:', self.prestador['nome']],
            ['Endereço:', f"{self.prestador['logradouro']}, {self.prestador['numero']} - {self.prestador['bairro']}"],
            ['UF/CEP:', f"{self.prestador['uf']} / {self.prestador['cep']}"],
        ]
        
        if self.prestador['fone']:
            prestador_dados.append(['Telefone:', self.prestador['fone']])
        if self.prestador['email']:
            prestador_dados.append(['E-mail:', self.prestador['email']])
        
        tabela_prestador = Table(prestador_dados, colWidths=[3.5*cm, 13.5*cm])
        tabela_prestador.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabela_prestador)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # TOMADOR
        elementos.append(Paragraph("TOMADOR DE SERVIÇOS (CLIENTE)", secao_style))
        
        tomador_dados = [
            [f"{self.tomador['tipo_doc']}:", self.tomador['documento']],
            ['Nome:', self.tomador['nome']],
        ]
        
        tabela_tomador = Table(tomador_dados, colWidths=[3.5*cm, 13.5*cm])
        tabela_tomador.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabela_tomador)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # SERVIÇO
        elementos.append(Paragraph("DESCRIÇÃO DO SERVIÇO", secao_style))
        
        servico_dados = [
            ['Código:', self.servico['codigo']],
            ['Descrição:', self.servico['descricao']],
        ]
        
        tabela_servico = Table(servico_dados, colWidths=[3.5*cm, 13.5*cm])
        tabela_servico.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabela_servico)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # VALORES
        elementos.append(Paragraph("VALORES", secao_style))
        
        valores_dados = [
            ['Base de Cálculo:', f"R$ {self.valores['base_calculo']}"],
            ['Alíquota ISS:', f"{self.valores['aliquota']}%"],
            ['Valor ISS:', f"R$ {self.valores['iss']}"],
            ['Valor Líquido:', f"R$ {self.valores['liquido']}"],
        ]
        
        tabela_valores = Table(valores_dados, colWidths=[3.5*cm, 13.5*cm])
        tabela_valores.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D0D0D0')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 8),
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabela_valores)
        
        elementos.append(Spacer(1, 1*cm))
        
        # RODAPÉ
        rodape = Paragraph(
            "<i>Este documento é uma representação gráfica simplificada da NFS-e autorizada pela Secretaria de Finanças.</i><br/>"
            f"<i>Documento gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            subtitulo_style
        )
        elementos.append(rodape)
        
        # Gerar PDF
        doc.build(elementos)
        
        return True


def gerar_danfse(xml_path: str, output_path: str = None) -> str:
    """
    Gera DANFSE em PDF a partir do XML da NFS-e.
    
    Args:
        xml_path: Caminho do XML da NFS-e autorizada
        output_path: Caminho de saída (opcional)
    
    Returns:
        Caminho do PDF gerado
    """
    import os
    
    xml_file = Path(xml_path)
    
    if not xml_file.exists():
        raise FileNotFoundError(f"XML não encontrado: {xml_path}")
    
    # Definir output_path se não fornecido
    if output_path is None:
        # Se estiver usando volume persistente, salvar no outputs/pdf
        volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_path and '/outputs/xml/' in str(xml_file):
            # XML está no volume, salvar PDF também no volume
            pdf_dir = Path(volume_path) / "outputs" / "pdf"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            output_path = pdf_dir / xml_file.with_suffix('.pdf').name
        else:
            # Salvar no mesmo diretório do XML
            output_path = xml_file.with_suffix('.pdf')
    
    # Gerar PDF
    gerador = GeradorDANFSE(xml_path)
    gerador.gerar_pdf(str(output_path))
    
    return str(output_path)


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("GERADOR DE DANFSE (PDF)")
    print("="*70)
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
    else:
        # Usar última NFS-e autorizada
        xml_path = "nfse_autorizada_final.xml"
    
    xml_file = Path(xml_path)
    
    if not xml_file.exists():
        print(f"\n[ERRO] Arquivo não encontrado: {xml_path}")
        print("\nUso: py gerar_danfse_v2.py [caminho_xml]")
        print("Exemplo: py gerar_danfse_v2.py nfse_autorizada_final.xml")
        sys.exit(1)
    
    try:
        print(f"\n[1] Lendo XML: {xml_path}")
        
        # Gerar PDF
        pdf_path = gerar_danfse(xml_path)
        
        print(f"[2] DANFSE gerado com sucesso!")
        print(f"\nArquivo: {pdf_path}")
        print(f"Tamanho: {Path(pdf_path).stat().st_size} bytes")
        
        print("\n" + "="*70)
        print("SUCESSO!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao gerar DANFSE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

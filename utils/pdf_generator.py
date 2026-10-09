import os
from fpdf import FPDF
from datetime import datetime

class ForensicDossierPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 25, 'F')
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'SWAPNA CHITRA: FORENSIC DREAM RECONSTRUCTION DOSSIER', ln=True, align='C')
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 5, 'CONFIDENTIAL // NEURAL ARCHIVE PROTOCOL', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Dossier Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Page {self.page_no()}', align='C')

def generate_case_pdf(case_id: int, dream_text: str, analysis: str, image_paths: list) -> str:
    pdf = ForensicDossierPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Metadata Banner
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, f"CASE RECORD: #{case_id:04d}", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(2)

    # Subject Statement
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "SUBJECT RECALL / RAW TESTIMONY:", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, dream_text)
    pdf.ln(4)

    # Forensic Analysis
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "DETECTIVE MORPHEUS PSYCHO-SYMBOLIC EVALUATION:", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, analysis)
    pdf.ln(6)

    # Embed Reconstructed Panels
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "TRI-PANEL NEURAL RECONSTRUCTIONS:", ln=True)
    pdf.ln(2)

    x_positions = [10, 75, 140]
    labels = ["PANEL 1: REALISTIC", "PANEL 2: SURREAL", "PANEL 3: SYMBOLIC"]
    y_img = pdf.get_y()

    for idx, (img_path, x_pos, label) in enumerate(zip(image_paths, x_positions, labels)):
        if os.path.exists(img_path):
            pdf.image(img_path, x=x_pos, y=y_img, w=60, h=60)
            pdf.set_xy(x_pos, y_img + 62)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(60, 5, label, align='C')

    pdf_path = f"generated_images/dossier_case_{case_id}.pdf"
    pdf.output(pdf_path)
    return pdf_path
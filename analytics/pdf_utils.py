"""
PDF Export Utilities
Generate PDF reports for dashboards and data tables
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_pdf_report(title, data, headers=None, filename="report.pdf", page_size=A4):
    """
    Generate a PDF report with table data.
    
    Args:
        title: Report title
        data: List of lists (table rows)
        headers: Optional list of column headers
        filename: Output filename
        page_size: Page size (default A4)
    
    Returns:
        BytesIO buffer containing PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=page_size, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add metadata
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )
    meta_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Prepare table data
    if headers:
        table_data = [headers] + data
    else:
        table_data = data
    
    if table_data:
        # Create table
        table = Table(table_data, repeatRows=1 if headers else 0)
        
        # Style the table
        table_style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_student_performance_pdf(student, subject_stats, risk_info, heatmap_data=None, study_plan=None):
    """
    Generate comprehensive student performance PDF report.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER)
    elements.append(Paragraph(f"Student Performance Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Student info
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Name:</b> {student.user.get_full_name() or student.user.username}", info_style))
    elements.append(Paragraph(f"<b>Class:</b> {student.school_class}", info_style))
    elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Risk summary
    if risk_info and risk_info.get('available'):
        elements.append(Paragraph("<b>Risk Assessment</b>", styles['Heading2']))
        risk_label = risk_info.get('label', 'Unknown')
        risk_color = 'red' if risk_label == 'High' else 'green'
        elements.append(Paragraph(f"Risk Level: <font color='{risk_color}'><b>{risk_label}</b></font>", info_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Subject performance table
    if subject_stats:
        elements.append(Paragraph("<b>Subject Performance</b>", styles['Heading2']))
        headers = ['Subject', 'Average (%)', 'Status']
        data = [[s['subject_name'], f"{s['avg_pct']:.1f}", s['status']] for s in subject_stats]
        table = Table([headers] + data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Topic mastery summary
    if heatmap_data and heatmap_data.get('details'):
        elements.append(Paragraph("<b>Topic Mastery Summary</b>", styles['Heading2']))
        for subject, topics in heatmap_data['details'].items():
            elements.append(Paragraph(f"<b>{subject}</b>", styles['Heading3']))
            topic_data = [[topic, f"{details['mastery_score']:.1f}%", details['level']] 
                         for topic, details in topics.items()]
            if topic_data:
                topic_table = Table([['Topic', 'Score', 'Level']] + topic_data)
                topic_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                elements.append(topic_table)
                elements.append(Spacer(1, 0.1*inch))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_class_report_pdf(school_class, rows, insights=None):
    """
    Generate class teacher dashboard PDF report.
    """
    title = f"Class Report: {school_class}"
    headers = ['Student', 'Admission No', 'Risk Label', 'Risk Probability']
    data = [
        [
            row['student'].user.username,
            row['student'].admission_number,
            row['risk_label'],
            f"{row['risk_proba']:.3f}"
        ]
        for row in rows
    ]
    
    return generate_pdf_report(title, data, headers)


def create_management_report_pdf(rows, filters_applied=None):
    """
    Generate management dashboard PDF report.
    """
    title = "School-wide Student Risk Report"
    headers = ['Student', 'Class', 'Risk Label', 'Risk Probability']
    data = [
        [
            row['student'].user.username,
            str(row['student'].school_class),
            row['risk_label'],
            f"{row['risk_proba']:.3f}"
        ]
        for row in rows
    ]
    
    return generate_pdf_report(title, data, headers)

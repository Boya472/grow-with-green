from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.http import HttpResponse
from datetime import datetime

def generer_facture_pdf(commande):
    """Génère une facture PDF pour une commande"""
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{commande.numero_commande}.pdf"'
    
    # Créer le document PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # En-tête
    elements.append(Paragraph("GROW WITH GREEN", title_style))
    elements.append(Paragraph("Attinguié, Abidjan, Côte d'Ivoire", styles['Normal']))
    elements.append(Paragraph("Email: contact@growwithgreen.ci", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Titre facture
    elements.append(Paragraph(f"FACTURE N° {commande.numero_commande}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {commande.date_commande.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informations client
    client_info = f"""
    <b>Client:</b><br/>
    {commande.user.get_full_name()}<br/>
    {commande.user.email}<br/>
    {commande.user.telephone}<br/>
    <br/>
    <b>Adresse de livraison:</b><br/>
    {commande.adresse_livraison}<br/>
    {commande.zone_livraison.nom}
    """
    elements.append(Paragraph(client_info, styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Tableau des articles
    data = [['Produit', 'Quantité', 'Prix unitaire', 'Total']]
    
    for item in commande.items.all():
        data.append([
            item.produit.nom,
            f"{item.quantite} kg",
            f"{item.prix_unitaire} FCFA",
            f"{item.sous_total} FCFA"
        ])
    
    # Totaux
    data.append(['', '', 'Sous-total:', f"{commande.montant_produits} FCFA"])
    data.append(['', '', 'Frais de livraison:', f"{commande.frais_livraison} FCFA"])
    data.append(['', '', '<b>TOTAL:</b>', f"<b>{commande.montant_total} FCFA</b>"])
    
    # Style du tableau
    table = Table(data, colWidths=[8*cm, 3*cm, 4*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 1*cm))
    
    # Pied de page
    footer = f"""
    <b>Mode de paiement:</b> {commande.get_mode_paiement_display()}<br/>
    <b>Statut:</b> {commande.get_statut_display()}<br/>
    <br/>
    Merci pour votre confiance !<br/>
    <i>Grow With Green - Légumes Premium</i>
    """
    elements.append(Paragraph(footer, styles['Normal']))
    
    # Construire le PDF
    doc.build(elements)
    
    return response
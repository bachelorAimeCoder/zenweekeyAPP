from fpdf import FPDF

def sanitize(text):
    if not isinstance(text, str):
        text = str(text)
    # Retire les emojis et les symboles non supportes par Helvetica pour eviter les erreurs de generation PDF
    return text.replace('➔', '->').replace('é', 'e').replace('è','e').replace('à','a').replace('â','a').replace('ô','o').replace('ê','e')

def generate_pdf(df, total_km, total_hours, user_filter, month_filter, date_filter):
    pdf = FPDF(orientation="L")
    pdf.add_page()
    
    # Titre
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Recapitulatif des Trajets - Conciergerie", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Parametres
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Filtre Fille : {sanitize(user_filter)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Filtre Mois : {sanitize(month_filter)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Filtre Jour : {sanitize(date_filter)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Total Kilometres : {total_km:.2f} km", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total Heures travail : {total_hours:.2f} h", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("helvetica", "B", 9)
    col_widths = [30, 15, 25, 30, 15, 15, 140]
    headers = ["Date", "KM", "Fille", "Statut", "Heures", "Etapes", "Itineraire"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln(8)
    
    # Table Body
    pdf.set_font("helvetica", "", 8)
    for _, row in df.iterrows():
        route = sanitize(row.get('Itinéraire', ''))
        if len(route) > 95:
            route = route[:92] + "..."
            
        pdf.cell(col_widths[0], 8, sanitize(row.get('Date', '')), border=1)
        pdf.cell(col_widths[1], 8, f"{row.get('Total KM', 0):.2f}", border=1, align="R")
        pdf.cell(col_widths[2], 8, sanitize(row.get('Fille', ''))[:15], border=1)
        pdf.cell(col_widths[3], 8, sanitize(row.get('Statut', ''))[:15], border=1)
        pdf.cell(col_widths[4], 8, f"{row.get('Heures', 0):.2f}", border=1, align="R")
        pdf.cell(col_widths[5], 8, str(row.get('Nb Étapes', 0)), border=1, align="C")
        pdf.cell(col_widths[6], 8, route, border=1)
        pdf.ln(8)
        
    return bytearray(pdf.output())

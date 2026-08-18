import io
import zipfile
from fpdf import FPDF

def sanitize(text):
    if not isinstance(text, str):
        text = str(text)
    # Retire les emojis et les symboles non supportes par Helvetica pour eviter les erreurs de generation PDF
    return text.replace('➔', '->').replace('é', 'e').replace('è','e').replace('à','a').replace('â','a').replace('ô','o').replace('ê','e')

def format_hours_str(val):
    try:
        if val is None or val == "": return "0h"
        val = float(val)
        h = int(val)
        m = int(round((val - h) * 60))
        if m == 0: return f"{h}h"
        return f"{h}h{m:02d}"
    except:
        return str(val)

def format_km(val):
    from decimal import Decimal, ROUND_HALF_UP
    try:
        if val is None or val == "": return "0.0"
        return f"{Decimal(str(val)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP):.1f}"
    except:
        return f"{val:.1f}"

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
    pdf.cell(0, 6, f"Total Kilometres : {format_km(total_km)} km", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total Heures travail : {format_hours_str(total_hours)}", new_x="LMARGIN", new_y="NEXT")
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
        pdf.cell(col_widths[1], 8, format_km(row.get('Total KM', 0)), border=1, align="R")
        pdf.cell(col_widths[2], 8, sanitize(row.get('Fille', ''))[:15], border=1)
        pdf.cell(col_widths[3], 8, sanitize(row.get('Statut', ''))[:15], border=1)
        pdf.cell(col_widths[4], 8, format_hours_str(row.get('Heures', 0)), border=1, align="R")
        pdf.cell(col_widths[5], 8, str(row.get('Nb Étapes', 0)), border=1, align="C")
        pdf.cell(col_widths[6], 8, route, border=1)
        pdf.ln(8)
        
    return bytes(pdf.output())

def format_date_french(date_str):
    months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    try:
        import pandas as pd
        dt = pd.to_datetime(date_str)
        return f"{dt.day} {months[dt.month - 1]} {dt.year}"
    except:
        return date_str

def generate_accounting_pdf(df, girl_name, month_str, total_km, total_hours):
    pdf = FPDF(orientation="P")
    pdf.add_page()
    
    # Zen Weekey Header
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "ZEN WEEKEY", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "10 RUE Rene Lacoste", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 6, "44430 SAINT LYPHARD", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(10)
    
    # Title
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"Fiche Comptable - {sanitize(girl_name)}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Information
    try:
        if "-" in month_str:
            y, m = month_str.split("-")
            import calendar
            last_day = calendar.monthrange(int(y), int(m))[1]
            periode_str = f"Du 01/{m} au {last_day}/{m}"
        else:
            periode_str = month_str
    except:
        periode_str = month_str

    # Counts
    cp_count = len(df[df['Statut'] == "Congé payé"]) if 'Statut' in df.columns else 0
    mal_count = len(df[df['Statut'] == "Maladie avec justificatif"]) if 'Statut' in df.columns else 0
    abs_count = len(df[df['Statut'] == "Absence sans justificatif"]) if 'Statut' in df.columns else 0

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Salariee : {sanitize(girl_name)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Periode : {periode_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total des heures : {format_hours_str(total_hours)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Nombre de kilometres : {format_km(total_km)} km", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Recapitulatif congés/absences
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Jours en conges payes : {cp_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Jours d'absences (maladie) : {mal_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Jours d'absences injustifiees : {abs_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Table Header (Dates -> Description -> Heures -> Kilometres)
    pdf.set_font("helvetica", "B", 10)
    col_widths = [40, 75, 35, 30]
    headers = ["Dates", "Description", "Heures", "Kilometres"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln(8)
    
    # Table Body
    pdf.set_font("helvetica", "", 10)
    # Sort by date optionally
    try:
        df = df.sort_values(by='Date')
    except:
        pass
        
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 8, sanitize(format_date_french(row.get('Date', ''))), border=1, align="C")
        pdf.cell(col_widths[1], 8, sanitize(row.get('Statut', '')), border=1, align="C")
        pdf.cell(col_widths[2], 8, format_hours_str(row.get('Heures', 0)), border=1, align="R")
        pdf.cell(col_widths[3], 8, format_km(row.get('Total KM', 0)), border=1, align="R")
        pdf.ln(8)
        
    return bytes(pdf.output())

def generate_accounting_zip(raw_df, month_str):
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for girl_name, group_df in raw_df.groupby('Fille'):
            total_km = group_df['Total KM'].sum()
            total_hours = group_df['Heures'].sum()
            
            pdf_bytes = generate_accounting_pdf(group_df, girl_name, month_str, total_km, total_hours)
            
            # File name
            safe_name = "".join([c if c.isalnum() else "_" for c in sanitize(girl_name)])
            filename = f"Fiche_Comptable_{safe_name}.pdf"
            
            zip_file.writestr(filename, pdf_bytes)
            
    return zip_buffer.getvalue()

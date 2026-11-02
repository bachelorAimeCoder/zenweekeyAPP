import re
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
    
    # Filter Text
    pdf.set_font("helvetica", "I", 10)
    user_txt = f"Salarie(e) : {sanitize(user_filter)}" if user_filter else "Salarie(e) : Tous"
    month_txt = f"Mois : {sanitize(month_filter)}" if month_filter else "Mois : Tous"
    date_txt = f"Jour specifique : {sanitize(date_filter)}" if date_filter else ""
    pdf.cell(0, 6, user_txt, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, month_txt, new_x="LMARGIN", new_y="NEXT")
    if date_txt: pdf.cell(0, 6, date_txt, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Total Kilometres : {format_km(total_km)} km", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total Heures travail : {format_hours_str(total_hours)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Table Header
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 9)
    col_widths = [30, 15, 28, 30, 15, 15, 137]
    headers = ["Date", "KM", "Salarie(e)", "Statut", "Heures", "Etapes", "Itineraire"]
    
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
        pdf.cell(col_widths[2], 8, sanitize(row.get('Salarié', ''))[:15], border=1)
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

def format_accounting_status(status_val):
    if not status_val:
        return ""
    s = str(status_val).strip()
    s_lower = s.lower()
    if "cong" in s_lower:
        return "Conge"
    if "maladie" in s_lower or "absence" in s_lower:
        return "Absence"
    return s

def parse_time_to_minutes(time_str):
    m = re.match(r'(\d{1,2})[h:](\d{2})', time_str.strip())
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None

def minutes_to_time_str(minutes):
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}h{m:02d}"

def adjust_breaks_for_detail(detail_str):
    if not detail_str or not isinstance(detail_str, str):
        return detail_str
    
    raw_slots = [s.strip() for s in detail_str.split('/') if s.strip()]
    parsed_slots = []
    for s in raw_slots:
        parts = s.split('-')
        if len(parts) == 2:
            t1 = parse_time_to_minutes(parts[0])
            t2 = parse_time_to_minutes(parts[1])
            if t1 is not None and t2 is not None:
                if t2 < t1:
                    t2 += 24 * 60
                parsed_slots.append((t1, t2))
            else:
                return detail_str
        else:
            return detail_str
            
    if not parsed_slots:
        return detail_str
        
    shift_minutes = 0
    new_slots = []
    
    for start, end in parsed_slots:
        curr_start = start + shift_minutes
        curr_end = end + shift_minutes
        duration = curr_end - curr_start
        
        while duration > 360:
            slot_end = curr_start + 360
            new_slots.append((curr_start, slot_end))
            shift_minutes += 20
            curr_start = slot_end + 20
            duration = duration - 360
            curr_end = curr_start + duration
            
        new_slots.append((curr_start, curr_end))
        
    return " / ".join(f"{minutes_to_time_str(s)}-{minutes_to_time_str(e)}" for s, e in new_slots)

def generate_accounting_pdf(df, employee_name, month_str, total_km, total_hours):
    pdf = FPDF(orientation="P")
    pdf.add_page()
    
    # Zen Weekey Header
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "ZEN WEEKEY", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, sanitize("69 rue de la Maisonneuve"), new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 6, sanitize("44350 Guérande"), new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(10)
    
    # Title
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"Fiche Comptable - {sanitize(employee_name)}", new_x="LMARGIN", new_y="NEXT", align="C")
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
    cp_count = len(df[df['Statut'].fillna('').str.contains("cong", case=False)]) if 'Statut' in df.columns else 0
    mal_count = len(df[df['Statut'].fillna('').str.contains("maladie", case=False)]) if 'Statut' in df.columns else 0
    abs_count = len(df[df['Statut'].fillna('').str.contains("sans justificatif", case=False)]) if 'Statut' in df.columns else 0

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Salarie(e) : {sanitize(employee_name)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Periode : {periode_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total des heures : {format_hours_str(total_hours)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Nombre de kilometres : {format_km(total_km)} km", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Recapitulatif congés/absences
    total_abs_count = mal_count + abs_count
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Jours en conges payes : {cp_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Jours d'absence : {total_abs_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Table Header (Dates -> Description -> Detail -> Heures -> Kilometres)
    pdf.set_font("helvetica", "B", 9)
    col_widths = [35, 28, 66, 28, 28]
    headers = ["Dates", "Description", "Detail", "Heures", "Kilometres"]
    
    start_x = (pdf.w - sum(col_widths)) / 2
    pdf.set_x(start_x)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln(8)
    
    # Table Body
    pdf.set_font("helvetica", "", 8.5)
    # Sort by date optionally
    try:
        df = df.sort_values(by='Date')
    except:
        pass
        
    for _, row in df.iterrows():
        detail_val = row.get('Detail', '')
        if not detail_val or str(detail_val) == 'nan':
            detail_val = row.get('hours_detail', '')
        if (not detail_val or str(detail_val) == 'nan') and row.get('Statut') == 'Travail' and row.get('Heures', 0) > 0:
            detail_val = format_hours_str(row.get('Heures', 0))
        elif not detail_val or str(detail_val) == 'nan':
            detail_val = ""
            
        detail_display = adjust_breaks_for_detail(str(detail_val))

        pdf.set_x(start_x)
        pdf.set_font("helvetica", "", 8.5)
        pdf.cell(col_widths[0], 8, sanitize(format_date_french(row.get('Date', ''))), border=1, align="C")
        pdf.cell(col_widths[1], 8, sanitize(format_accounting_status(row.get('Statut', ''))), border=1, align="C")
        
        # Ajuster la police si le texte des créneaux est long
        if len(detail_display) > 30:
            pdf.set_font("helvetica", "", 7.5)
        else:
            pdf.set_font("helvetica", "", 8.5)
        pdf.cell(col_widths[2], 8, sanitize(detail_display), border=1, align="C")
        
        pdf.set_font("helvetica", "", 8.5)
        pdf.cell(col_widths[3], 8, format_hours_str(row.get('Heures', 0)), border=1, align="R")
        pdf.cell(col_widths[4], 8, format_km(row.get('Total KM', 0)), border=1, align="R")
        pdf.ln(8)
        
    return bytes(pdf.output())

def generate_accounting_zip(raw_df, month_str):
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for employee_name, group_df in raw_df.groupby('Salarié'):
            total_km = group_df['Total KM'].sum()
            total_hours = group_df['Heures'].sum()
            
            pdf_bytes = generate_accounting_pdf(group_df, employee_name, month_str, total_km, total_hours)
            
            # File name
            safe_name = "".join([c if c.isalnum() else "_" for c in sanitize(employee_name)])
            filename = f"Fiche_Comptable_{safe_name}.pdf"
            
            zip_file.writestr(filename, pdf_bytes)
            
    return zip_buffer.getvalue()

from __future__ import annotations

from typing import Any

from app.models.ewyp import EWYPFormSchema


def _render_ewyp_html(form: EWYPFormSchema) -> str:
  injured = form.injured_person
  injured_addr = form.injured_address
  accident = form.accident_info

  def fmt(value: object | None) -> str:
    return "" if value is None else str(value)

  return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <title>ZUS EWYP - Zawiadomienie o wypadku</title>
  <style>
    body {{ font-family: Arial, sans-serif; background-color: #f3f4f6; }}
    .a4-page {{
      max-width: 210mm;
      margin: 20px auto;
      background: white;
      padding: 40px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    .section-header {{
      background-color: #e5e7eb;
      padding: 5px 10px;
      font-weight: bold;
      margin-top: 20px;
      margin-bottom: 10px;
      border-left: 5px solid #3b82f6;
      font-size: 0.9rem;
    }}
    label {{ font-size: 0.75rem; font-weight: 600; color: #374151; display: block; }}
    .field-value {{
      border: 1px solid #d1d5db;
      min-height: 18px;
      padding: 2px 6px;
      font-size: 0.8rem;
    }}
    .row {{ display: flex; gap: 8px; margin-bottom: 6px; }}
    .col-1 {{ flex: 1; }}
    .col-2 {{ flex: 2; }}
    .col-3 {{ flex: 3; }}
    .text-xs {{ font-size: 0.7rem; }}
    .text-sm {{ font-size: 0.8rem; }}
    .text-right {{ text-align: right; }}
    .font-bold {{ font-weight: 700; }}
    .mt-2 {{ margin-top: 8px; }}
    .mb-2 {{ margin-bottom: 8px; }}
    .mb-4 {{ margin-bottom: 16px; }}
    .border-top {{ border-top: 2px solid #111827; padding-top: 8px; margin-top: 16px; }}
    .signature-line {{ border-bottom: 1px solid #000; height: 24px; }}
  </style>
</head>
<body>

<div class="a4-page">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; font-size:0.9rem;">
    <div style="width:50%; padding-right:16px;">
      <div style="margin-bottom:12px;">
        <div class="input-line">
          {fmt(injured.first_name)} {fmt(injured.last_name)}
        </div>
        <div style="font-size:0.75rem; text-align:center; color:#6b7280;">
          (imię i nazwisko zgłaszającego)
        </div>
      </div>
      <div>
        <div class="input-line">
          {fmt(form.reporter.document_number) if form.reporter else ""} {fmt(form.reporter.phone) if form.reporter else ""}
        </div>
        <div style="font-size:0.75rem; text-align:center; color:#6b7280;">
          (stanowisko służbowe, nr telefonu)
        </div>
      </div>
    </div>

    <div style="width:50%; padding-left:16px; text-align:right;">
      <div style="margin-bottom:12px;">
        <div class="input-line">
          {fmt(injured_addr.city)}, {fmt(accident.accident_date)}
        </div>
        <div style="font-size:0.75rem; text-align:center; color:#6b7280;">
          (miejscowość i data)
        </div>
      </div>
      <div>
        <div class="input-line"></div>
        <div style="font-size:0.75rem; text-align:center; color:#6b7280;">
          (miejsce pracy)
        </div>
      </div>
    </div>
  </div>

  <div style="margin-bottom:16px; background-color:#eff6ff; padding:12px; border:1px solid #dbeafe; font-size:0.8rem;">
    <div class="font-bold mb-2">Wypadkowi uległa osoba, która (zaznacz X):</div>
    <div class="text-xs">
      <div>☐ prowadzi pozarolniczą działalność</div>
      <div>☐ współpracuje przy prowadzeniu pozarolniczej działalności</div>
      <div>☐ wykonuje pracę na podstawie umowy uaktywniającej (niania)</div>
    </div>
  </div>

  <div class="section-header">I. DANE OSOBY POSZKODOWANEJ</div>
  <div class="row mb-2">
    <div class="col-1">
      <label>PESEL</label>
      <div class="field-value">{fmt(injured.pesel)}</div>
    </div>
    <div class="col-3">
      <label>Dokument tożsamości (rodzaj, seria, numer)</label>
      <div class="field-value">{fmt(injured.document_type)} {fmt(injured.document_number)}</div>
    </div>
  </div>
  <div class="row mb-2">
    <div class="col-1">
      <label>Imię</label>
      <div class="field-value">{fmt(injured.first_name)}</div>
    </div>
    <div class="col-1">
      <label>Nazwisko</label>
      <div class="field-value">{fmt(injured.last_name)}</div>
    </div>
  </div>
  <div class="row mb-4">
    <div class="col-1">
      <label>Data urodzenia</label>
      <div class="field-value">{fmt(injured.birth_date)}</div>
    </div>
    <div class="col-1">
      <label>Miejsce urodzenia</label>
      <div class="field-value">{fmt(injured.birth_place)}</div>
    </div>
  </div>

  <div class="section-header">Adres zamieszkania</div>
  <div class="row mb-2">
    <div class="col-3">
      <label>Ulica</label>
      <div class="field-value">{fmt(injured_addr.street)}</div>
    </div>
    <div class="col-1">
      <label>Nr domu</label>
      <div class="field-value">{fmt(injured_addr.house_number)}</div>
    </div>
    <div class="col-1">
      <label>Nr lokalu</label>
      <div class="field-value">{fmt(injured_addr.apartment_number)}</div>
    </div>
  </div>
  <div class="row mb-4">
    <div class="col-1">
      <label>Kod pocztowy</label>
      <div class="field-value">{fmt(injured_addr.postal_code)}</div>
    </div>
    <div class="col-3">
      <label>Miejscowość</label>
      <div class="field-value">{fmt(injured_addr.city)}</div>
    </div>
  </div>

  <div class="section-header">II. INFORMACJA O WYPADKU</div>
  <div class="row mb-2">
    <div class="col-1">
      <label>Data wypadku</label>
      <div class="field-value">{fmt(accident.accident_date)}</div>
    </div>
    <div class="col-1">
      <label>Godzina</label>
      <div class="field-value">{fmt(accident.accident_time)}</div>
    </div>
    <div class="col-1">
      <label>Planowany start pracy</label>
      <div class="field-value">{fmt(accident.planned_work_start)}</div>
    </div>
    <div class="col-1">
      <label>Planowany koniec pracy</label>
      <div class="field-value">{fmt(accident.planned_work_end)}</div>
    </div>
  </div>
  <div class="mb-4">
    <label>Miejsce wypadku</label>
    <div class="field-value">{fmt(accident.accident_place)}</div>
  </div>

  <div class="mb-4">
    <label class="mb-2">Szczegółowy opis okoliczności, miejsca i przyczyn wypadku</label>
    <div class="field-value" style="min-height:80px; background-color:#fef9c3; white-space:pre-wrap;">
      {fmt(accident.detailed_description)}
    </div>
  </div>

  <div class="mb-4">
    <label>Rodzaj doznanych urazów</label>
    <div class="field-value" style="white-space:pre-wrap;">{fmt(accident.injuries_description)}</div>
  </div>

  <div class="section-header">III. POMOC MEDYCZNA I POSTĘPOWANIE</div>
  <div class="row mb-4">
    <div class="col-1">
      <label>Czy udzielono pierwszej pomocy?</label>
      <div class="field-value text-xs">
        {"TAK" if accident.first_aid_provided else ("NIE" if accident.first_aid_provided is not None else "")}
      </div>
    </div>
    <div class="col-3">
      <label>Organ prowadzący postępowanie (np. policja)</label>
      <div class="field-value">{fmt(accident.investigating_authority)}</div>
    </div>
  </div>

  <div class="section-header">IV. MASZYNY I URZĄDZENIA</div>
  <div class="mb-2">
    <label>Czy wypadek powstał podczas obsługi maszyn/urządzeń?</label>
    <div class="field-value text-xs">
      {"TAK" if accident.machine_involved else ("NIE" if accident.machine_involved is not None else "")}
    </div>
  </div>
  <div style="padding:12px; border:1px dashed #9ca3af; background-color:#f9fafb; border-radius:4px; margin-bottom:16px;">
    <div class="text-xs text-gray-500 mb-2 font-bold" style="text-transform:uppercase;">Wypełnij, jeśli wybrano TAK:</div>
    <div class="mb-2">
      <label>Czy maszyna była sprawna i użytkowana zgodnie z zasadami?</label>
      <div class="field-value">{fmt(accident.machine_description)}</div>
    </div>
    <div class="row">
      <div class="col-1">
        <label>Czy posiada atest/deklarację zgodności?</label>
        <div class="field-value text-xs">
          {"TAK" if accident.machine_certified else ("NIE" if accident.machine_certified is not None else "")}
        </div>
      </div>
      <div class="col-1">
        <label>Wpisana do ewidencji środków trwałych?</label>
        <div class="field-value text-xs">
          {"TAK" if accident.machine_registered else ("NIE" if accident.machine_registered is not None else "")}
        </div>
      </div>
    </div>
  </div>

  <div class="section-header">V. DANE ŚWIADKÓW WYPADKU</div>
  <div class="mb-4" style="border-bottom:1px solid #e5e7eb; padding-bottom:12px;">
    <div class="font-bold text-xs mb-2" style="color:#6b7280;">Świadek 1</div>
    <div class="row mb-2">
      <div class="col-1">
        <label>Imię</label>
        <div class="field-value">{fmt(form.witnesses[0].first_name) if form.witnesses else ""}</div>
      </div>
      <div class="col-1">
        <label>Nazwisko</label>
        <div class="field-value">{fmt(form.witnesses[0].last_name) if form.witnesses else ""}</div>
      </div>
    </div>
    <div class="row">
      <div class="col-2">
        <label>Ulica</label>
        <div class="field-value">{fmt(form.witnesses[0].address.street) if form.witnesses and form.witnesses[0].address else ""}</div>
      </div>
      <div class="col-1">
        <label>Miejscowość</label>
        <div class="field-value">{fmt(form.witnesses[0].address.city) if form.witnesses and form.witnesses[0].address else ""}</div>
      </div>
    </div>
  </div>

  <div class="section-header">VI. ZAŁĄCZNIKI</div>
  <div class="text-sm" style="margin-bottom:12px;">
    <div>☐ Kserokopia karty informacyjnej ze szpitala / zaświadczenie o pierwszej pomocy</div>
    <div>☐ Kserokopia postanowienia prokuratury</div>
    <div>☐ Kserokopia karty zgonu (jeśli dotyczy)</div>
  </div>
  <div class="mb-4">
    <label>Inne dokumenty (wymień jakie):</label>
    <div class="field-value">{", ".join(form.attachments) if form.attachments else ""}</div>
  </div>

  <div class="border-top">
    <p class="text-xs" style="text-align:justify; font-style:italic; margin-bottom:16px;">
      Oświadczam, że dane zawarte w zawiadomieniu podaję zgodnie z prawdą, co potwierdzam złożonym podpisem.
    </p>
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:32px;">
      <div style="width:30%; text-align:center;">
        <div class="field-value" style="border-top:none; border-left:none; border-right:none; border-bottom:1px solid #000;">
          {fmt(form.documents_deadline)}
        </div>
        <div class="text-xs mt-1">Data</div>
      </div>
      <div style="width:40%; text-align:center;">
        <div class="signature-line"></div>
        <div class="text-xs mt-1">Czytelny podpis</div>
      </div>
    </div>
  </div>

</div>

</body>
</html>
"""
def _render_notification_html(form: EWYPFormSchema) -> str:
  return """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Zawiadomienie o wypadku przy pracy</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 11pt;
            line-height: 1.3;
            color: #000;
        }
        .flex { display: flex; }
        .justify-between { justify-content: space-between; }
        .justify-end { justify-content: flex-end; }
        .w-half { width: 45%; }
        .w-full { width: 100%; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .bold { font-weight: bold; }
        .mb-1 { margin-bottom: 0.25cm; }
        .mb-2 { margin-bottom: 0.5cm; }
        .mb-4 { margin-bottom: 1cm; }
        .input-line {
            border-bottom: 1px dotted #000;
            display: inline-block;
            width: 100%;
            min-height: 1em;
        }
        .input-label-under {
            font-size: 8pt;
            color: #444;
            text-align: center;
            margin-top: 2px;
        }
        .form-row {
            margin-bottom: 10px;
        }
        .form-label {
            font-weight: bold;
            margin-right: 5px;
        }
        h1 {
            text-align: center;
            text-transform: uppercase;
            font-size: 14pt;
            margin: 1.5cm 0 1cm 0;
            letter-spacing: 1px;
            font-weight: bold;
        }
    </style>
</head>
<body>

    <div class="flex justify-between mb-4">
        <div class="w-half">
            <div class="mb-2">
                <span class="input-line"></span>
                <div class="input-label-under">(imię i nazwisko zgłaszającego)</div>
            </div>
            <div>
                <span class="input-line"></span>
                <div class="input-label-under">(stanowisko służbowe, nr telefonu)</div>
            </div>
        </div>

        <div class="w-half text-right">
            <div class="mb-2">
                <span class="input-line"></span>
                <div class="input-label-under">(miejscowość i data)</div>
            </div>
            <div>
                <span class="input-line"></span>
                <div class="input-label-under">(miejsce pracy)</div>
            </div>
        </div>
    </div>

    <div class="flex justify-end mb-4" style="margin-top: 1cm;">
        <div class="w-half text-center">
            <div style="text-align: left; margin-bottom: 5px;">Do:</div>
            <span class="input-line"></span>
            <div class="bold" style="margin-top: 5px;">/bezpośredni przełożony/</div>
        </div>
    </div>

    <h1>ZAWIADOMIENIE O WYPADKU PRZY PRACY</h1>

    <div style="margin-top: 0.5cm;">

        <div class="form-row">
            <span class="form-label">1. Imię i nazwisko osoby poszkodowanej:</span>
            <span class="input-line" style="width: 55%;"></span>
        </div>

        <div class="form-row">
            <span class="form-label">2. Miejsce pracy:</span>
            <span class="input-line" style="width: 80%;"></span>
            <div class="input-label-under" style="text-align: right; padding-right: 10px;">(zakład pracy, oddział, wydział)</div>
        </div>

        <div class="form-row">
            <span class="form-label">3. Adres zamieszkania, numer telefonu:</span>
            <span class="input-line"></span>
            <span class="input-line" style="margin-top: 5px;"></span>
        </div>

        <div class="form-row">
            <span class="form-label">4. Data i godzina wypadku:</span>
            <span class="input-line" style="width: 70%;"></span>
        </div>

        <div class="form-row">
            <span class="form-label">5. Miejsce wypadku:</span>
            <span class="input-line" style="width: 80%;"></span>
        </div>

        <div class="form-row">
            <span class="form-label">6. Skutki wypadku:</span>
            <span class="input-line"></span>
            <span class="input-line" style="margin-top: 5px;"></span>
        </div>

        <div class="form-row">
            <div class="form-label" style="margin-bottom: 5px;">7. Świadkowie wypadku (imię, nazwisko, adres zamieszkania, numer telefonu):</div>
            <div style="margin-left: 20px; margin-bottom: 5px;">
                <span style="margin-right: 5px;">a)</span>
                <span class="input-line" style="width: 90%;"></span>
            </div>
            <div style="margin-left: 20px;">
                <span style="margin-right: 5px;">b)</span>
                <span class="input-line" style="width: 90%;"></span>
            </div>
        </div>

        <div class="form-row" style="margin-top: 15px;">
            <div class="form-label">8. Zwięzły opis wypadku:</div>
            <div style="margin-top: 5px;">
                <span class="input-line" style="margin-bottom: 8px;"></span>
                <span class="input-line" style="margin-bottom: 8px;"></span>
                <span class="input-line" style="margin-bottom: 8px;"></span>
                <span class="input-line" style="margin-bottom: 8px;"></span>
                <span class="input-line" style="margin-bottom: 8px;"></span>
                <span class="input-line" style="margin-bottom: 8px;"></span>
            </div>
        </div>

    </div>

    <div class="flex justify-end" style="margin-top: 2cm;">
        <div class="w-half text-center">
            <span class="input-line"></span>
            <div class="input-label-under">(podpis osoby zgłaszającej wypadek)</div>
        </div>
    </div>

</body>
</html>
"""


def generate_ewyp_pdf(form_data: EWYPFormSchema | dict[str, Any]) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError("WeasyPrint is required for PDF export") from exc

    form = form_data if isinstance(form_data, EWYPFormSchema) else EWYPFormSchema(**form_data)
    html = _render_ewyp_html(form)
    return HTML(string=html).write_pdf()


def generate_notification_pdf(form_data: EWYPFormSchema | dict[str, Any]) -> bytes:
  try:
    from weasyprint import HTML
  except Exception as exc:  # noqa: BLE001
    raise RuntimeError("WeasyPrint is required for PDF export") from exc

  form = form_data if isinstance(form_data, EWYPFormSchema) else EWYPFormSchema(**form_data)
  html = _render_notification_html(form)
  return HTML(string=html).write_pdf()



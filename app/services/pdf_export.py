from __future__ import annotations

from typing import Any

from app.models.ewyp import EWYPFormSchema


def _render_html(form: EWYPFormSchema) -> str:
    injured = form.injured_person
    accident = form.accident_info
    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: Arial, sans-serif; }}
          h1 {{ font-size: 20px; }}
          h2 {{ font-size: 16px; margin-top: 16px; }}
          p {{ margin: 4px 0; }}
        </style>
      </head>
      <body>
        <h1>Formularz EWYP</h1>
        <h2>Dane poszkodowanego</h2>
        <p>{injured.first_name or ""} {injured.last_name or ""}</p>
        <p>PESEL: {injured.pesel or "-"}</p>

        <h2>Informacje o wypadku</h2>
        <p>Data: {accident.accident_date or "-"}</p>
        <p>Godzina: {accident.accident_time or "-"}</p>
        <p>Miejsce: {accident.accident_place or "-"}</p>
        <p>Opis: {accident.detailed_description or "-"}</p>
      </body>
    </html>
    """


def generate_ewyp_pdf(form_data: EWYPFormSchema | dict[str, Any]) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("WeasyPrint is required for PDF export") from exc

    form = form_data if isinstance(form_data, EWYPFormSchema) else EWYPFormSchema(**form_data)
    html = _render_html(form)
    return HTML(string=html).write_pdf()



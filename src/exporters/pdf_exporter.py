"""
Exportador de historias clínicas consolidadas a PDF con formato profesional.

Genera PDFs con:
- Encabezado con datos del paciente
- Secciones organizadas (diagnósticos, exámenes, recomendaciones)
- Tabla de alertas destacada
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from src.config.schemas import HistoriaClinicaEstructurada
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _build_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


class PDFExporter:
    """
    Exporta historias clínicas consolidadas a PDF.
    """

    def __init__(self, output_dir: Path | str = Path("data/exports")) -> None:
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab no está instalado. "
                "Instalar con: pip install reportlab"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        self.styles.add(
            ParagraphStyle(
                name="TitleCentered",
                parent=self.styles["Heading1"],
                fontSize=18,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1a365d"),
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=13,
                textColor=colors.HexColor("#2c5282"),
                spaceAfter=6,
                spaceBefore=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Body",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=14,
                alignment=TA_JUSTIFY,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Small",
                parent=self.styles["Normal"],
                fontSize=9,
                alignment=TA_LEFT,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Badge",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                alignment=TA_LEFT,
                backColor=colors.HexColor("#2F855A"),
                leftIndent=4,
                rightIndent=4,
                spaceAfter=6,
            )
        )

    def export(
        self,
        historia: HistoriaClinicaEstructurada,
        output_path: Optional[Path] = None,
    ) -> Path:
        if output_path is None:
            documento = historia.datos_empleado.documento or "sin_documento"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"HC_{documento}_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story: list = []
        story.extend(self._build_header(historia))
        story.extend(self._build_patient_info(historia))

        if historia.signos_vitales:
            story.extend(self._build_vital_signs(historia))

        story.extend(self._build_conclusiones(historia))
        story.extend(self._build_examenes(historia))
        story.extend(self._build_plan(historia))
        story.extend(self._build_metadata(historia))

        if historia.alertas_validacion:
            story.append(PageBreak())
            story.extend(self._build_alertas(historia))

        doc.build(story)
        logger.info("PDF generado: %s", output_path)
        return output_path

    # Secciones -------------------------------------------------------------
    def _build_header(self, historia: HistoriaClinicaEstructurada) -> list:
        paciente = historia.datos_empleado.nombre_completo or "Paciente sin nombre"
        fecha = historia.fecha_emo or historia.fecha_consolidacion or ""

        return [
            _build_paragraph("HISTORIA CLÍNICA OCUPACIONAL CONSOLIDADA", self.styles["TitleCentered"]),
            _build_paragraph(f"<b>Paciente:</b> {paciente}", self.styles["Body"]),
            _build_paragraph(f"<b>Fecha EMO:</b> {fecha}", self.styles["Body"]),
            Spacer(1, 0.2 * inch),
        ]

    def _build_patient_info(self, historia: HistoriaClinicaEstructurada) -> list:
        datos = historia.datos_empleado
        rows = [
            ["Nombre", datos.nombre_completo or "-"],
            ["Documento", datos.documento or "-"],
            ["Edad", datos.edad or "-"],
            ["Cargo", datos.cargo or "-"],
            ["Empresa", datos.empresa or "-"],
        ]

        table = Table(rows, colWidths=[1.8 * inch, 4.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )

        return [
            _build_paragraph("Datos del paciente", self.styles["SectionTitle"]),
            table,
            Spacer(1, 0.15 * inch),
        ]

    def _build_vital_signs(self, historia: HistoriaClinicaEstructurada) -> list:
        sv = historia.signos_vitales
        data = [
            ["Presión arterial", sv.presion_arterial or "-"],
            ["Frecuencia cardiaca", sv.frecuencia_cardiaca or "-"],
            ["Frecuencia respiratoria", sv.frecuencia_respiratoria or "-"],
            ["Temperatura", sv.temperatura or "-"],
            ["Saturación O₂", sv.saturacion_oxigeno or "-"],
            ["Peso (kg)", sv.peso_kg or "-"],
            ["Talla (cm)", sv.talla_cm or "-"],
            ["IMC", sv.imc or "-"],
        ]

        table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
        table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.25, colors.gray)]))

        return [
            _build_paragraph("Signos vitales", self.styles["SectionTitle"]),
            table,
            Spacer(1, 0.15 * inch),
        ]

    def _build_conclusiones(self, historia: HistoriaClinicaEstructurada) -> list:
        blocks = [
            _build_paragraph("Conclusiones y diagnóstico", self.styles["SectionTitle"]),
            _build_paragraph(f"<b>Aptitud laboral:</b> {historia.aptitud_laboral or '-'}", self.styles["Body"]),
        ]

        if historia.restricciones_especificas:
            blocks.append(
                _build_paragraph(f"<b>Restricciones:</b> {historia.restricciones_especificas}", self.styles["Body"])
            )

        if historia.diagnosticos:
            rows = [["Código", "Descripción", "Tipo", "Relacionado", "Confianza"]]
            for diag in historia.diagnosticos:
                rows.append(
                    [
                        diag.codigo_cie10,
                        diag.descripcion,
                        diag.tipo or "-",
                        "Sí" if diag.relacionado_trabajo else "No",
                        f"{diag.confianza:.2f}",
                    ]
                )

            table = Table(rows, colWidths=[0.8 * inch, 2.5 * inch, 0.9 * inch, 1.0 * inch, 0.8 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.gray),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.gray),
                    ]
                )
            )
            blocks.append(table)

        blocks.append(Spacer(1, 0.15 * inch))
        return blocks

    def _build_examenes(self, historia: HistoriaClinicaEstructurada) -> list:
        if not historia.examenes:
            return []

        elements = [_build_paragraph("Exámenes relevantes", self.styles["SectionTitle"])]
        significativos = []
        neutros = 0

        for exam in historia.examenes:
            if self._is_significant_exam(exam):
                block = KeepTogether(
                    [
                        _build_paragraph(f"<b>{exam.tipo.upper()} • {exam.nombre}</b>", self.styles["Body"]),
                        _build_paragraph(f"Fecha: {exam.fecha or '-'}", self.styles["Small"]),
                        _build_paragraph(f"Resultado: {exam.resultado or '-'}", self.styles["Small"]),
                        _build_paragraph(f"Interpretación: {exam.interpretacion or '-'}", self.styles["Small"]),
                        (
                            _build_paragraph(f"Hallazgos: {exam.hallazgos_clave}", self.styles["Small"])
                            if exam.hallazgos_clave
                            else Spacer(1, 0)
                        ),
                        Spacer(1, 0.08 * inch),
                    ]
                )
                significativos.append(block)
            else:
                neutros += 1

        if significativos:
            elements.extend(significativos)
        else:
            elements.append(_build_paragraph("No se reportan exámenes con hallazgos relevantes.", self.styles["Body"]))

        if neutros:
            elements.append(
                _build_paragraph(
                    f"Resto de exámenes sin alteraciones relevantes ({neutros}).",
                    self.styles["Small"],
                )
            )

        elements.append(Spacer(1, 0.15 * inch))
        return elements

    def _is_significant_exam(self, exam) -> bool:
        interpretacion = (exam.interpretacion or "").strip().lower()
        hallazgos = (exam.hallazgos_clave or "").strip().lower()

        if interpretacion and interpretacion not in {"normal", "sin hallazgos"}:
            return True

        if hallazgos and "sin hallazgos" not in hallazgos and "dentro de rangos normales" not in hallazgos:
            return True

        return False

    def _build_plan(self, historia: HistoriaClinicaEstructurada) -> list:
        filas: list[list] = [["Tipo", "Descripción", "Seguimiento"]]

        for rec in historia.recomendaciones or []:
            descripcion = rec.descripcion or ""
            if not descripcion:
                continue
            filas.append(
                [
                    _build_paragraph(self._format_recommendation_type(rec.tipo), self.styles["Small"]),
                    _build_paragraph(descripcion, self.styles["Small"]),
                    _build_paragraph("✔" if rec.requiere_seguimiento else "—", self.styles["Small"]),
                ]
            )

        for rem in historia.remisiones or []:
            descripcion = getattr(rem, "descripcion", None) or getattr(rem, "motivo", None) or ""
            especialidad = getattr(rem, "especialidad", None)
            if not especialidad and not descripcion:
                continue
            filas.append(
                [
                    _build_paragraph(f"Remisión {especialidad or ''}".strip(), self.styles["Small"]),
                    _build_paragraph(descripcion, self.styles["Small"]),
                    _build_paragraph("✔", self.styles["Small"]),
                ]
            )

        if historia.programas_sve:
            for programa in historia.programas_sve:
                filas.append(
                    [
                        _build_paragraph("SVE", self.styles["Small"]),
                        _build_paragraph(programa, self.styles["Small"]),
                        _build_paragraph("✔", self.styles["Small"]),
                    ]
                )

        if len(filas) == 1:
            return []

        table = Table(filas, colWidths=[1.4 * inch, 3.6 * inch, 0.9 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF5F5")),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("ALIGN", (-1, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("WORDWRAP", (0, 0), (-1, -1), True),
                ]
            )
        )

        return [
            _build_paragraph("Plan y seguimiento", self.styles["SectionTitle"]),
            table,
            Spacer(1, 0.15 * inch),
        ]

    def _format_recommendation_type(self, tipo: Optional[str]) -> str:
        mapping = {
            "remision_especialista": "Remisión",
            "seguimiento": "Seguimiento",
            "tratamiento": "Tratamiento",
            "restriccion_laboral": "Restricción",
            "inclusion_sve": "SVE",
            "examen_complementario": "Examen complementario",
            "ajuste_ergonomico": "Ajuste ergonómico",
        }
        if not tipo:
            return "Plan"
        return mapping.get(tipo, tipo.replace("_", " ").title())

    def _build_metadata(self, historia: HistoriaClinicaEstructurada) -> list:
        fuentes = getattr(historia, "archivos_origen_consolidados", None) or []
        fecha = getattr(historia, "fecha_consolidacion", None) or ""

        if not fuentes and not fecha:
            return []

        lines = []
        if fecha:
            lines.append(f"<b>Fecha de consolidación:</b> {fecha}")
        if fuentes:
            joined = ", ".join(fuentes)
            lines.append(f"<b>Fuentes:</b> {joined}")

        return [
            _build_paragraph("Metadatos", self.styles["SectionTitle"]),
            _build_paragraph("<br/>".join(lines), self.styles["Small"]),
            Spacer(1, 0.15 * inch),
        ]

    def _build_alertas(self, historia: HistoriaClinicaEstructurada) -> list:
        grouped = {"critico": [], "inconsistencia": [], "formato": [], "otros": []}
        for alerta in historia.alertas_validacion:
            tipo = alerta.tipo.lower()
            if "valor_critico" in tipo:
                grouped["critico"].append(alerta)
            elif "inconsistencia" in tipo:
                grouped["inconsistencia"].append(alerta)
            elif "formato" in tipo:
                grouped["formato"].append(alerta)
            else:
                grouped["otros"].append(alerta)

        order = [
            ("critico", "Críticos"),
            ("inconsistencia", "Inconsistencias"),
            ("formato", "Formato"),
            ("otros", "Otros"),
        ]

        elements = [_build_paragraph("Alertas clínicas", self.styles["SectionTitle"])]

        for key, titulo in order:
            alertas = grouped[key]
            if not alertas:
                continue
            elements.append(_build_paragraph(f"<b>{titulo}</b>", self.styles["Body"]))
            for alerta in alertas:
                elements.append(
                    _build_paragraph(
                        f"• {alerta.descripcion} (Campo: {alerta.campo_afectado})",
                        self.styles["Small"],
                    )
                )
            elements.append(Spacer(1, 0.05 * inch))

        return elements


def export_consolidated_to_pdf(
    historia: HistoriaClinicaEstructurada,
    output_path: Optional[Path] = None,
) -> Path:
    exporter = PDFExporter()
    return exporter.export(historia, output_path)


__all__ = ["PDFExporter", "export_consolidated_to_pdf"]

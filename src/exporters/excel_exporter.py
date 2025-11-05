"""
Exportador de historias clínicas a formato Excel.

Genera hojas de cálculo con los datos estructurados para análisis.
"""

from pathlib import Path
from typing import List

import pandas as pd

from src.config.schemas import HistoriaClinicaEstructurada
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelExporter:
    """
    Exportador de historias clínicas a Excel.

    Genera un archivo Excel con múltiples hojas:
    - Resumen: Información general de todas las HCs
    - Diagnósticos: Todos los diagnósticos
    - Exámenes: Todos los exámenes paraclínicos
    - Recomendaciones: Todas las recomendaciones
    - Alertas: Todas las alertas de validación
    """

    def __init__(self, output_dir: Path):
        """
        Inicializa el exportador.

        Args:
            output_dir: Directorio de salida para archivos Excel
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ExcelExporter inicializado con output_dir: {self.output_dir}")

    def export(
        self,
        historias: List[HistoriaClinicaEstructurada],
        filename: str = "historias_clinicas.xlsx"
    ) -> Path:
        """
        Exporta historias clínicas a Excel con múltiples hojas.

        Args:
            historias: Lista de historias clínicas a exportar
            filename: Nombre del archivo Excel

        Returns:
            Path: Ruta al archivo Excel creado
        """
        output_path = self.output_dir / filename

        logger.info(f"Exportando {len(historias)} historias a Excel: {filename}")

        # Crear DataFrames para cada hoja
        df_resumen = self._create_summary_df(historias)
        df_diagnosticos = self._create_diagnosticos_df(historias)
        df_examenes = self._create_examenes_df(historias)
        df_recomendaciones = self._create_recomendaciones_df(historias)
        df_alertas = self._create_alertas_df(historias)

        # Escribir a Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            df_diagnosticos.to_excel(writer, sheet_name='Diagnósticos', index=False)
            df_examenes.to_excel(writer, sheet_name='Exámenes', index=False)
            df_recomendaciones.to_excel(writer, sheet_name='Recomendaciones', index=False)
            df_alertas.to_excel(writer, sheet_name='Alertas', index=False)

        logger.info(f"Historias clínicas exportadas a: {output_path}")

        return output_path

    def _create_summary_df(
        self,
        historias: List[HistoriaClinicaEstructurada]
    ) -> pd.DataFrame:
        """Crea DataFrame de resumen."""
        data = []

        for h in historias:
            row = {
                'ID Procesamiento': h.id_procesamiento,
                'Archivo Origen': h.archivo_origen,
                'Fecha Procesamiento': h.fecha_procesamiento,
                'Nombre': h.datos_empleado.nombre_completo,
                'Documento': h.datos_empleado.documento,
                'Cargo': h.datos_empleado.cargo,
                'Empresa': h.datos_empleado.empresa,
                'Tipo EMO': h.tipo_emo,
                'Fecha EMO': h.fecha_emo,
                'Aptitud Laboral': h.aptitud_laboral,
                'Restricciones': h.restricciones_especificas,
                'Programas SVE': ', '.join(h.programas_sve) if h.programas_sve else None,
                'Genera Reincorporación': h.genera_reincorporacion,
                'Num Diagnósticos': len(h.diagnosticos),
                'Num Exámenes': len(h.examenes),
                'Num Recomendaciones': len(h.recomendaciones),
                'Num Alertas': len(h.alertas_validacion),
                'Confianza': h.confianza_extraccion,
            }
            data.append(row)

        return pd.DataFrame(data)

    def _create_diagnosticos_df(
        self,
        historias: List[HistoriaClinicaEstructurada]
    ) -> pd.DataFrame:
        """Crea DataFrame de diagnósticos."""
        data = []

        for h in historias:
            for diag in h.diagnosticos:
                row = {
                    'ID Procesamiento': h.id_procesamiento,
                    'Archivo': h.archivo_origen,
                    'Nombre Empleado': h.datos_empleado.nombre_completo,
                    'Documento': h.datos_empleado.documento,
                    'Código CIE-10': diag.codigo_cie10,
                    'Descripción': diag.descripcion,
                    'Tipo': diag.tipo,
                    'Relacionado Trabajo': diag.relacionado_trabajo,
                    'Confianza': diag.confianza,
                }
                data.append(row)

        return pd.DataFrame(data)

    def _create_examenes_df(
        self,
        historias: List[HistoriaClinicaEstructurada]
    ) -> pd.DataFrame:
        """Crea DataFrame de exámenes."""
        data = []

        for h in historias:
            for exam in h.examenes:
                row = {
                    'ID Procesamiento': h.id_procesamiento,
                    'Archivo': h.archivo_origen,
                    'Nombre Empleado': h.datos_empleado.nombre_completo,
                    'Tipo Examen': exam.tipo,
                    'Nombre Examen': exam.nombre,
                    'Fecha': exam.fecha,
                    'Resultado': exam.resultado,
                    'Valor Numérico': exam.valor_numerico,
                    'Unidad': exam.unidad,
                    'Rango Referencia': exam.rango_referencia,
                    'Hallazgos Clave': exam.hallazgos_clave,
                    'Interpretación': exam.interpretacion,
                }
                data.append(row)

        return pd.DataFrame(data)

    def _create_recomendaciones_df(
        self,
        historias: List[HistoriaClinicaEstructurada]
    ) -> pd.DataFrame:
        """Crea DataFrame de recomendaciones."""
        data = []

        for h in historias:
            for rec in h.recomendaciones:
                row = {
                    'ID Procesamiento': h.id_procesamiento,
                    'Archivo': h.archivo_origen,
                    'Nombre Empleado': h.datos_empleado.nombre_completo,
                    'Tipo': rec.tipo,
                    'Descripción': rec.descripcion,
                    'Vigencia (meses)': rec.vigencia_meses,
                    'Requiere Seguimiento': rec.requiere_seguimiento,
                    'Fecha Seguimiento': rec.fecha_seguimiento,
                    'Prioridad': rec.prioridad,
                }
                data.append(row)

        return pd.DataFrame(data)

    def _create_alertas_df(
        self,
        historias: List[HistoriaClinicaEstructurada]
    ) -> pd.DataFrame:
        """Crea DataFrame de alertas."""
        data = []

        for h in historias:
            for alerta in h.alertas_validacion:
                row = {
                    'ID Procesamiento': h.id_procesamiento,
                    'Archivo': h.archivo_origen,
                    'Nombre Empleado': h.datos_empleado.nombre_completo,
                    'Tipo': alerta.tipo,
                    'Severidad': alerta.severidad,
                    'Campo Afectado': alerta.campo_afectado,
                    'Descripción': alerta.descripcion,
                    'Acción Sugerida': alerta.accion_sugerida,
                }
                data.append(row)

        return pd.DataFrame(data)

    def export_narah_format(
        self,
        historias: List[HistoriaClinicaEstructurada],
        filename: str = "narah_import.xlsx"
    ) -> Path:
        """
        Exporta en formato específico para importación a Narah Metrics.

        Args:
            historias: Lista de historias clínicas
            filename: Nombre del archivo

        Returns:
            Path: Ruta al archivo Excel
        """
        output_path = self.output_dir / filename

        logger.info(
            f"Exportando {len(historias)} historias en formato Narah: {filename}"
        )

        # Formato específico para Narah (ajustar según necesidades)
        data = []

        for h in historias:
            # Concatenar diagnósticos
            diagnosticos_str = "; ".join(
                [f"{d.codigo_cie10} - {d.descripcion}" for d in h.diagnosticos]
            )

            # Concatenar programas SVE
            sve_str = ", ".join(h.programas_sve) if h.programas_sve else ""

            row = {
                'Documento': h.datos_empleado.documento,
                'Nombre': h.datos_empleado.nombre_completo,
                'Cargo': h.datos_empleado.cargo,
                'Area': h.datos_empleado.area,
                'Empresa': h.datos_empleado.empresa,
                'Fecha EMO': h.fecha_emo,
                'Tipo EMO': h.tipo_emo,
                'Aptitud': h.aptitud_laboral,
                'Diagnósticos': diagnosticos_str,
                'Restricciones': h.restricciones_especificas,
                'Programas SVE': sve_str,
                'Genera Reincorporación': 'Sí' if h.genera_reincorporacion else 'No',
                'Causa Reincorporación': h.causa_reincorporacion,
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Exportar
        df.to_excel(output_path, index=False, engine='openpyxl')

        logger.info(f"Formato Narah exportado a: {output_path}")

        return output_path


__all__ = ["ExcelExporter"]

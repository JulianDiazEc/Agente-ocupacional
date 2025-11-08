"""
Schemas Pydantic para Historia Clínica Ocupacional Estructurada.

Estos schemas definen el formato exacto de salida esperado para
las historias clínicas procesadas, incluyendo validaciones de negocio.
"""

from datetime import date, datetime
from typing import Any, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


def convert_to_bool(v: Any) -> bool:
    """
    Convierte valores comunes a booleano.

    Usado para validar campos booleanos que pueden venir como strings desde Claude.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        v_lower = v.lower().strip()
        if v_lower in ('true', 'sí', 'si', 'yes', 'y', '1', 'activo', 'vigente'):
            return True
        if v_lower in ('false', 'no', 'n', '0', 'inactivo', 'resuelto'):
            return False
    if isinstance(v, (int, float)):
        return bool(v)
    # Si no se puede convertir, retornar True por defecto
    return True


def normalize_programa_sve(v: str) -> Optional[str]:
    """
    Normaliza nombres de programas SVE a valores estándar.

    Mapea variaciones comunes que Claude puede retornar:
    - "osteomuscular", "músculo-esquelético" → "dme"
    - "auditivo", "conservación auditiva" → "ruido"
    - etc.
    """
    if not v or not isinstance(v, str):
        return None

    v_clean = v.lower().strip()

    # Mapeo de variaciones comunes
    mapeo = {
        # DME - Desórdenes musculoesqueléticos
        "dme": "dme",
        "osteomuscular": "dme",
        "musculoesqueletico": "dme",
        "musculo-esqueletico": "dme",
        "osteo": "dme",
        "ergonomico": "dme",
        "desordenes_musculoesqueleticos": "dme",

        # Ruido
        "ruido": "ruido",
        "auditivo": "ruido",
        "conservacion_auditiva": "ruido",
        "conservación_auditiva": "ruido",
        "audiometria": "ruido",
        "auditiva": "ruido",

        # Biológico
        "biologico": "biologico",
        "biológico": "biologico",
        "riesgo_biologico": "biologico",

        # Psicosocial
        "psicosocial": "psicosocial",
        "psico": "psicosocial",
        "riesgo_psicosocial": "psicosocial",

        # BTX
        "btx": "btx",
        "solventes": "btx",
        "benceno": "btx",
        "tolueno": "btx",
        "xileno": "btx",

        # Radiaciones
        "radiaciones_ionizantes": "radiaciones_ionizantes",
        "radiaciones": "radiaciones_ionizantes",
        "rayos_x": "radiaciones_ionizantes",

        # Químico
        "quimico": "quimico",
        "químico": "quimico",
        "riesgo_quimico": "quimico",
        "sustancias_quimicas": "quimico",

        # Cardiovascular
        "cardiovascular": "cardiovascular",
        "cardio": "cardiovascular",
        "corazon": "cardiovascular",
        "hipertension": "cardiovascular",

        # Voz
        "voz": "voz",
        "vocal": "voz",
        "laringeo": "voz",

        # Visual
        "visual": "visual",
        "oftalmologico": "visual",
        "oftalmológico": "visual",
        "ojos": "visual",
        "vision": "visual",
        "visión": "visual",

        # Respiratorio
        "respiratorio": "respiratorio",
        "neumologico": "respiratorio",
        "neumológico": "respiratorio",
        "pulmonar": "respiratorio",
        "pulmones": "respiratorio",
    }

    # Buscar coincidencia
    for clave, valor_std in mapeo.items():
        if clave in v_clean:
            return valor_std

    # Si no hay coincidencia, retornar None (se filtrará)
    return None


class Diagnostico(BaseModel):
    """
    Diagnóstico médico con código CIE-10.

    Validaciones:
    - Código CIE-10 debe tener formato: Letra + 2 dígitos + punto + 1 dígito
      Ejemplos válidos: M54.5, J30.1, H52.0, E11.9
    """
    codigo_cie10: str = Field(
        ...,
        description="Código CIE-10 en formato estándar (ej: M54.5)",
        pattern=r"^[A-Z]\d{2}\.\d$"
    )
    descripcion: str = Field(..., description="Descripción del diagnóstico")
    tipo: Optional[Literal["principal", "secundario", "hallazgo"]] = Field(
        None,
        description="Tipo de diagnóstico (solo cuando está explícito en el documento)"
    )
    relacionado_trabajo: bool = Field(
        default=False,
        description="Indica si el diagnóstico está relacionado con la actividad laboral"
    )
    confianza: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nivel de confianza en la extracción (0.0 - 1.0)"
    )

    @field_validator('relacionado_trabajo', mode='before')
    @classmethod
    def validate_relacionado_trabajo(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)

    @field_validator('codigo_cie10')
    @classmethod
    def validar_formato_cie10(cls, v: str) -> str:
        """Valida que el código CIE-10 tenga formato correcto."""
        if not v or len(v) < 5:
            raise ValueError(f"Código CIE-10 inválido: {v}")
        # Convertir a mayúsculas
        v = v.upper()
        # Validar formato básico
        if not (v[0].isalpha() and v[1:3].isdigit()):
            raise ValueError(f"Código CIE-10 debe iniciar con letra seguida de 2 dígitos: {v}")
        return v


class Incapacidad(BaseModel):
    """
    Registro de incapacidad médica.

    Los días totales se calculan automáticamente si no se proporcionan.
    """
    fecha_inicio: date = Field(..., description="Fecha de inicio de la incapacidad")
    fecha_fin: date = Field(..., description="Fecha de finalización de la incapacidad")
    dias_totales: Optional[int] = Field(
        None,
        ge=1,
        description="Días totales de incapacidad (calculado automáticamente)"
    )
    tipo: Literal["general", "laboral", "accidente_trabajo", "enfermedad_laboral"] = Field(
        ...,
        description="Tipo de incapacidad"
    )
    prorroga: bool = Field(
        default=False,
        description="Indica si es una prórroga de incapacidad previa"
    )
    diagnostico_asociado: Optional[str] = Field(
        None,
        description="Código CIE-10 del diagnóstico que generó la incapacidad"
    )

    @field_validator('prorroga', mode='before')
    @classmethod
    def validate_prorroga(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)

    @model_validator(mode='after')
    def calcular_dias_totales(self) -> 'Incapacidad':
        """Calcula días totales si no se proporcionó."""
        if self.dias_totales is None:
            delta = self.fecha_fin - self.fecha_inicio
            self.dias_totales = delta.days + 1  # Incluye ambos días
        return self

    @model_validator(mode='after')
    def validar_fechas(self) -> 'Incapacidad':
        """Valida que fecha_fin sea posterior a fecha_inicio."""
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError(
                f"fecha_fin ({self.fecha_fin}) debe ser posterior a "
                f"fecha_inicio ({self.fecha_inicio})"
            )
        return self


class Examen(BaseModel):
    """
    Examen paraclínico realizado.

    Incluye laboratorios, imágenes, pruebas funcionales, etc.
    """
    tipo: Literal[
        "laboratorio",
        "imagenologia",
        "funcional",
        "audiometria",
        "espirometria",
        "optometria",
        "electrocardiograma",
        "otro"
    ] = Field(..., description="Tipo de examen")
    nombre: str = Field(..., description="Nombre específico del examen")
    fecha: Optional[date] = Field(None, description="Fecha de realización")
    resultado: Optional[str] = Field(None, description="Resultado textual")
    valor_numerico: Optional[float] = Field(None, description="Valor numérico si aplica")
    unidad: Optional[str] = Field(None, description="Unidad de medida")
    rango_referencia: Optional[str] = Field(None, description="Rango de referencia normal")
    hallazgos_clave: Optional[str] = Field(
        None,
        description="Hallazgos relevantes o anormales"
    )
    interpretacion: Optional[Literal["normal", "alterado", "critico"]] = Field(
        None,
        description="Interpretación del resultado"
    )


class Recomendacion(BaseModel):
    """
    Recomendación médica u ocupacional.

    IMPORTANTE: Solo se extraen recomendaciones ESPECÍFICAS, no genéricas.
    """
    tipo: Literal[
        "remision_especialista",
        "examen_complementario",
        "inclusion_sve",
        "tratamiento",
        "restriccion_laboral",
        "ajuste_ergonomico",
        "seguimiento"
    ] = Field(..., description="Tipo de recomendación")
    descripcion: str = Field(..., description="Descripción específica de la recomendación")
    vigencia_meses: Optional[int] = Field(
        None,
        ge=1,
        description="Vigencia en meses (si aplica)"
    )
    requiere_seguimiento: bool = Field(
        default=False,
        description="Indica si requiere seguimiento médico"
    )

    @field_validator('requiere_seguimiento', mode='before')
    @classmethod
    def validate_requiere_seguimiento(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)


class Remision(BaseModel):
    """Remisión a especialista médico."""
    especialidad: str = Field(..., description="Especialidad médica")
    motivo: Optional[str] = Field(None, description="Motivo de la remisión")
    requiere_seguimiento: bool = Field(default=True)
    fecha_planeada: Optional[date] = Field(None, description="Fecha planeada de consulta")
    observaciones: Optional[str] = None

    @field_validator('requiere_seguimiento', mode='before')
    @classmethod
    def validate_requiere_seguimiento(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)


class DatosEmpleado(BaseModel):
    """Información demográfica y laboral del empleado."""
    nombre_completo: Optional[str] = None
    documento: Optional[str] = None
    tipo_documento: Optional[Literal["CC", "CE", "TI", "PEP", "PPT", "NIT"]] = None
    fecha_nacimiento: Optional[date] = None
    edad: Optional[int] = Field(None, ge=0, le=120)
    sexo: Optional[Literal["M", "F", "O"]] = None
    cargo: Optional[str] = None
    area: Optional[str] = None
    empresa: Optional[str] = None
    antiguedad_meses: Optional[int] = Field(None, ge=0)
    eps: Optional[str] = Field(None, description="Entidad Promotora de Salud")
    arl: Optional[str] = Field(None, description="Administradora de Riesgos Laborales")


class SignosVitales(BaseModel):
    """Signos vitales tomados en el examen físico."""
    presion_arterial: Optional[str] = Field(None, description="PA en formato 120/80")
    frecuencia_cardiaca: Optional[int] = Field(None, ge=40, le=200, description="FC en lpm")
    frecuencia_respiratoria: Optional[int] = Field(None, ge=8, le=40, description="FR en rpm")
    temperatura: Optional[float] = Field(None, ge=35.0, le=42.0, description="Temperatura °C")
    saturacion_oxigeno: Optional[int] = Field(None, ge=70, le=100, description="SpO2 en %")
    peso_kg: Optional[float] = Field(None, ge=20.0, le=300.0)
    talla_cm: Optional[float] = Field(None, ge=100.0, le=250.0)
    imc: Optional[float] = Field(None, ge=10.0, le=60.0, description="Índice de Masa Corporal")


class Antecedente(BaseModel):
    """Antecedente médico, quirúrgico, toxicológico, etc."""
    tipo: Literal[
        "patologico",
        "quirurgico",
        "traumatologico",
        "ocupacional",
        "toxicologico",
        "alergico",
        "farmacologico",
        "gineco_obstetrico",
        "familiar"
    ]
    descripcion: str
    fecha_aproximada: Optional[str] = Field(None, description="Año o fecha aproximada")
    activo: bool = Field(default=True, description="Si el antecedente está activo/vigente")

    @field_validator('activo', mode='before')
    @classmethod
    def validate_activo(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)


class Alerta(BaseModel):
    """
    Alerta de validación o inconsistencia detectada.

    Permite rastrear problemas de calidad en la extracción.
    """
    tipo: Literal[
        "inconsistencia_diagnostica",
        "dato_faltante",
        "valor_critico",
        "formato_incorrecto",
        "evaluacion_incompleta"
    ]
    severidad: Literal["alta", "media", "baja"]
    campo_afectado: str = Field(..., description="Campo o sección afectada")
    descripcion: str = Field(..., description="Descripción clara del problema")
    accion_sugerida: str = Field(..., description="Qué debe hacer el revisor")


class HistoriaClinicaEstructurada(BaseModel):
    """
    Schema principal de Historia Clínica Ocupacional estructurada.

    Este es el modelo completo que retorna el sistema de procesamiento.
    """
    # Metadata de procesamiento
    id_procesamiento: str = Field(
        default_factory=lambda: str(uuid4()),
        description="ID único del procesamiento"
    )
    fecha_procesamiento: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del procesamiento"
    )
    archivo_origen: str = Field(..., description="Nombre del archivo PDF original")

    # Tipo de documento fuente (para validaciones condicionales)
    tipo_documento_fuente: Literal[
        "hc_completa",          # Historia clínica ocupacional completa con anamnesis
        "cmo",                  # Certificado médico ocupacional con aptitud
        "examen_especifico"     # Examen aislado: RX, labs, optometría, espirometría, etc.
    ] = Field(
        default="hc_completa",
        description="Tipo de documento procesado - determina qué campos son obligatorios"
    )

    # Datos del empleado
    datos_empleado: DatosEmpleado = Field(default_factory=DatosEmpleado)

    # Tipo y fecha del EMO
    tipo_emo: Optional[Literal[
        "preingreso",
        "periodico",
        "cambio_ocupacion",
        "post_incapacidad",
        "retiro",
        "seguimiento"
    ]] = None
    fecha_emo: Optional[date] = Field(None, description="Fecha del examen médico ocupacional")

    # Examen físico
    signos_vitales: Optional[SignosVitales] = None
    hallazgos_examen_fisico: Optional[str] = Field(
        None,
        description="Hallazgos relevantes del examen físico"
    )

    # Antecedentes
    antecedentes: List[Antecedente] = Field(
        default_factory=list,
        description="Antecedentes médicos, quirúrgicos, etc."
    )

    # Contenido médico principal
    diagnosticos: List[Diagnostico] = Field(
        default_factory=list,
        description="Diagnósticos encontrados (con CIE-10)"
    )
    incapacidades: List[Incapacidad] = Field(
        default_factory=list,
        description="Registro de incapacidades"
    )
    examenes: List[Examen] = Field(
        default_factory=list,
        description="Exámenes paraclínicos realizados"
    )
    recomendaciones: List[Recomendacion] = Field(
        default_factory=list,
        description="Recomendaciones médicas y ocupacionales específicas"
    )
    remisiones: List[Remision] = Field(
        default_factory=list,
        description="Remisiones a especialistas"
    )

    # Aptitud laboral
    aptitud_laboral: Optional[Literal[
        "apto",
        "apto_sin_restricciones",
        "apto_con_recomendaciones",
        "apto_con_restricciones",
        "no_apto_temporal",
        "no_apto_definitivo",
        "pendiente"
    ]] = None
    restricciones_especificas: Optional[str] = Field(
        None,
        description="Descripción detallada de restricciones laborales específicas"
    )

    # Programas de Vigilancia Epidemiológica (SVE)
    programas_sve: List[Literal[
        "dme",  # Desórdenes musculoesqueléticos
        "ruido",
        "biologico",
        "psicosocial",
        "btx",  # Benceno, tolueno, xileno
        "radiaciones_ionizantes",
        "quimico",
        "cardiovascular",
        "voz",
        "visual",
        "respiratorio"
    ]] = Field(default_factory=list, description="Programas SVE en los que debe incluirse")

    @field_validator('programas_sve', mode='before')
    @classmethod
    def normalize_programas_sve(cls, v):
        """Normaliza nombres de programas SVE a valores estándar."""
        if not v:
            return []

        if not isinstance(v, list):
            v = [v]

        programas_normalizados = []
        for programa in v:
            if isinstance(programa, str):
                normalizado = normalize_programa_sve(programa)
                if normalizado and normalizado not in programas_normalizados:
                    programas_normalizados.append(normalizado)

        return programas_normalizados

    # Reincorporación laboral
    genera_reincorporacion: bool = Field(
        default=False,
        description="Indica si genera proceso de reincorporación"
    )
    causa_reincorporacion: Optional[str] = Field(
        None,
        description="Motivo de reincorporación (si aplica)"
    )

    # Calidad y validación
    confianza_extraccion: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confianza global de la extracción (0.0 - 1.0)"
    )
    campos_con_baja_confianza: List[str] = Field(
        default_factory=list,
        description="Lista de campos con confianza < 0.7"
    )
    alertas_validacion: List[Alerta] = Field(
        default_factory=list,
        description="Alertas detectadas durante la validación"
    )
    notas_procesamiento: Optional[str] = Field(
        None,
        description="Notas adicionales sobre el procesamiento"
    )

    @field_validator('genera_reincorporacion', mode='before')
    @classmethod
    def validate_genera_reincorporacion(cls, v) -> bool:
        """Convierte valores comunes a booleano."""
        return convert_to_bool(v)

    @model_validator(mode='after')
    def validar_consistencia(self) -> 'HistoriaClinicaEstructurada':
        """Validaciones de consistencia entre campos."""

        # Si genera reincorporación, debe haber causa
        if self.genera_reincorporacion and not self.causa_reincorporacion:
            self.alertas_validacion.append(
                Alerta(
                    tipo="dato_faltante",
                    severidad="media",
                    campo_afectado="causa_reincorporacion",
                    descripcion="Se indica reincorporación pero no se especifica la causa",
                    accion_sugerida="Verificar motivo de reincorporación en el documento"
                )
            )

        return self

    class Config:
        """Configuración del modelo Pydantic."""
        json_schema_extra = {
            "example": {
                "archivo_origen": "HC_12345_2024.pdf",
                "tipo_emo": "periodico",
                "fecha_emo": "2024-03-15",
                "datos_empleado": {
                    "nombre_completo": "JUAN PÉREZ",
                    "documento": "12345678",
                    "tipo_documento": "CC",
                    "cargo": "Operario de producción",
                    "empresa": "EMPRESA XYZ S.A.S"
                },
                "diagnosticos": [
                    {
                        "codigo_cie10": "M54.5",
                        "descripcion": "Dolor lumbar bajo",
                        "tipo": "principal",
                        "relacionado_trabajo": True,
                        "confianza": 0.95
                    }
                ],
                "aptitud_laboral": "apto_con_restricciones",
                "restricciones_especificas": "No levantar cargas mayores a 15kg",
                "programas_sve": ["dme"],
                "confianza_extraccion": 0.92
            }
        }

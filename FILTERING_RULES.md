# Reglas de Filtrado y Validación - Narah HC Processor

**Autor**: CTO
**Fecha**: 2025-11-09
**Estado**: NORMATIVA - NO NEGOCIABLE

---

## Principio Rector

**Cero ruido estructural. Alertas donde importan. Hallazgos donde aportan. Todo lo demás, afuera.**

---

## 1️⃣ Aptitud Laboral - NO TOCAR LO QUE YA ESTÁ BIEN

### Comportamiento Actual (MANTENER):
- Pre-procesamiento normaliza `"aplazado"` → `"pendiente"`
- Valores fuera de catálogo → `"pendiente"` + alerta `formato_incorrecto`
- **NO rompe pipeline con ValidationError**

### Regla de Oro:
**Si viene un valor válido (`apto`, `apto_con_restricciones`, etc.) → NO LO TOQUES.**

### Prohibido:
- ❌ Inventar aptitud cuando no existe
- ❌ Degradar `"apto"` válido por hallazgos o EPP
- ❌ Hacer depender aptitud de recomendaciones
- ❌ "Corregir" aptitudes válidas

**Responsable**: `src/processors/claude_processor.py::normalize_aptitud_laboral()`

---

## 2️⃣ Exámenes Específicos - SIN ALERTAS DE HC

### Aplica a:
Audiometría, espirometría, RX, optometría, laboratorios, alturas, etc.

### Comportamiento Esperado:
```json
{
  "tipo_documento_fuente": "examen_especifico",
  "alertas_validacion": [
    // SOLO SI HAY VALORES CRÍTICOS REALES
    {"tipo": "valor_critico", "descripcion": "Glucosa 400 mg/dl"}
  ],
  "hallazgos_examen_fisico": "Sin hallazgos relevantes"  // ← SÍNTESIS, NO LISTA
}
```

### Alertas Permitidas:
- ✅ `valor_critico` (ej: glucosa absurda)
- ✅ `formato_incorrecto` (ej: fecha malformada)

### Alertas Prohibidas:
- ❌ "Falta tipo_emo"
- ❌ "Falta aptitud_laboral"
- ❌ "Sin diagnósticos"
- ❌ "Sin signos vitales"

### Hallazgos:
- **Todo normal** → Síntesis: `"Sin hallazgos relevantes"` / `"Dentro de parámetros normales"`
- **Hay anormales** → Listar SOLO parámetros alterados
- **Prohibido** → Copiar 40 ítems normales sistema por sistema

**Responsable**:
- `src/processors/claude_processor.py` (líneas 859-881) - validación condicional
- `src/processors/claude_processor.py::summarize_normal_physical_exam()`

---

## 3️⃣ CMO (Concepto Médico Ocupacional) - NO ES HC COMPLETA

### Tratamiento:
```json
{
  "tipo_documento_fuente": "cmo",
  "aptitud_laboral": "apto_con_restricciones",  // ← OBLIGATORIO
  "tipo_emo": "periodico",                       // ← OBLIGATORIO
  "fecha_emo": "2024-03-15",                     // ← SI APLICA
  "signos_vitales": null                         // ← NO REQUERIDOS EN CMO
}
```

### Campos Obligatorios en CMO:
- ✅ `aptitud_laboral`
- ✅ `tipo_emo`
- ✅ `restricciones_especificas` (si existen)

### Campos NO Requeridos en CMO:
- ❌ `signos_vitales` (se filtra alerta si falta)

### Prohibido:
- ❌ Tratar CMO como historia completa
- ❌ Alertas tipo: `"Signos vitales no registrados en el CMO"`

**Responsable**: `src/processors/alert_filters.py::is_signos_vitales_alert_in_cmo()`

---

## 4️⃣ Consolidado - ÚNICO LUGAR PARA VALIDAR EN SERIO

### Principio:
**El consolidado es la ÚNICA fuente de verdad cross-documento.**

### Comportamiento:
```python
# Individual processing
examen_especifico.alertas_validacion = []  # ← NO GENERA ALERTAS

# Consolidation
consolidado.tipo_documento_fuente = "consolidado"
consolidado.alertas_validacion = validate_historia_completa(consolidado)  # ← AQUÍ
consolidado.alertas_validacion = filter_alerts(...)  # ← FILTRAR CON LISTA BLANCA
```

### Reglas:
1. **NO heredar alertas** de PDFs individuales
2. **Ejecutar `validate_historia_completa()`** solo en consolidado
3. **Aplicar `filter_alerts()`** con lista blanca clínica
4. Validar consistencia:
   - Diagnósticos ↔ Exámenes
   - Aptitud ↔ Restricciones
   - Faltantes clínicos reales (si no aparecen en NINGÚN origen)

### Prohibido:
- ❌ Recrear alertas administrativas
- ❌ Duplicar la misma inconsistencia 3 veces
- ❌ Basar alertas en "documento X dijo Y", solo en estado final

**Responsable**:
- `consolidate_person.py::consolidate_historias()` (líneas 402-436)
- `src/processors/claude_processor.py` (líneas 859-881)

---

## 5️⃣ Recomendaciones - SOLO LO CLÍNICO Y CONTEXTUAL

### Conservar SI cumple AL MENOS UNO:
- ✅ Tiene contexto clínico concreto:
  - Número + unidad (`85 dB`, `15 kg`, `IMC >30`)
  - Frecuencia clara (`cada 6 meses`)
  - Ligadas a diagnóstico, hallazgo o riesgo
- ✅ Instrucción específica aplicable a ese trabajador

### Filtrar SI cumple CUALQUIERA:
- ❌ Nombre suelto de examen (≤3 palabras): `"Espirometría"`, `"Laboratorios"`
- ❌ Fórmula genérica:
  - `"Uso adecuado de EPP"`
  - `"Educación en higiene visual"`
  - `"Adherir lineamientos del ministerio"`
  - `"Hábitos saludables"`, `"Pausas activas"` (sin contexto)
- ❌ Administrativa/marketing: `"Incluir en programa X"`

### Criterio de Duda:
**Si hay duda entre genérica o específica → CONSERVAR.**

El error aceptable es ruido leve, NO perder indicación clínica.

### Excepciones (se reubican automáticamente):
- `"Aplazado para..."` → `restricciones_especificas`
- `"Incluir en SVE de..."` → `programas_sve`

**Responsable**:
- `src/processors/recommendation_filters.py::filter_recommendations()`
- `src/processors/claude_processor.py::relocate_misclassified_recommendations()`

---

## 6️⃣ Alertas - LISTA BLANCA + CONTEXTO

### Lista Blanca (CONSERVAR SIEMPRE):
```python
WHITELIST_ALERT_TYPES = {
    'valor_critico',
    'formato_incorrecto',
    'inconsistencia_diagnostica',
    'fecha_invalida'
}
```

### `dato_faltante` - Reglas Específicas:
- ✅ **Solo en consolidado / HC completa**
- ✅ Solo si el campo **realmente no existe** en resultado final
- ❌ **Nunca** por detalles administrativos (EPS, ARL, cargo, etc.)

### Filtrado por Tipo de Documento:
| Tipo | Validaciones | Alertas Permitidas |
|------|--------------|-------------------|
| `examen_especifico` | ❌ NO | Solo `valor_critico`, `formato_incorrecto` |
| `cmo` | ✅ SÍ | Lista blanca - signos_vitales |
| `hc_completa` | ✅ SÍ | Lista blanca completa |
| `consolidado` | ✅ SÍ | Lista blanca completa |

### Prohibido:
- ❌ Alertas de completitud en exámenes específicos
- ❌ Alertas administrativas en cualquier parte
- ❌ Alertas que contradigan lo claro del médico

**Responsable**:
- `src/processors/alert_filters.py::filter_alerts()`
- `src/processors/alert_filters.py::WHITELIST_ALERT_TYPES`

---

## 7️⃣ Estabilidad - A Prueba de Balas

### Checklist de Cambios:
Antes de modificar filtros, validar:
- [ ] No se reintroducen validaciones dobles
- [ ] No se rompe `HistoriaClinicaEstructurada`
- [ ] No se toca aptitud cuando el valor es válido
- [ ] No se añaden heurísticas débiles (ej: `if len(text) > 100`)
- [ ] No se mueve lógica clínica al prompt

### Principios de Diseño:
1. **Pre-procesamiento sobre Pydantic**: Normalizar antes de validar
2. **Lista blanca sobre lista negra**: Definir qué SÍ, no qué NO
3. **Filtros centralizados**: `recommendation_filters.py`, `alert_filters.py`
4. **Logging explícito**: Por qué se filtró cada cosa

---

## 🎯 Resumen Ejecutivo

| Componente | Regla de Oro |
|------------|--------------|
| **Aptitud** | Si es válida, NO la toques |
| **Examen Específico** | `alertas_validacion = []` |
| **CMO** | NO exigir signos vitales |
| **Consolidado** | ÚNICO lugar para validar cruzado |
| **Recomendaciones** | Clínico y contextual, o fuera |
| **Alertas** | Lista blanca + contexto de documento |
| **Pipeline** | Nunca romper por valores atípicos |

---

## 📋 Archivos Responsables

```
src/
├── config/
│   └── schemas.py                  # Schema Pydantic (acepta "consolidado")
├── processors/
│   ├── claude_processor.py         # Pipeline principal
│   │   ├── normalize_aptitud_laboral()
│   │   ├── validate_signos_vitales()
│   │   ├── relocate_misclassified_recommendations()
│   │   └── process() [líneas 859-881] - validación condicional
│   ├── recommendation_filters.py   # Filtro de recomendaciones
│   │   └── filter_recommendations()
│   ├── alert_filters.py            # Filtro de alertas
│   │   ├── filter_alerts()
│   │   └── WHITELIST_ALERT_TYPES
│   └── validators.py               # validate_historia_completa()
└── consolidate_person.py           # Consolidador (líneas 402-436)
```

---

## ⚠️ Advertencias

**Para Claude Code / Devs futuro**:

1. **NO "mejores" aptitud válida**: Si dice `"apto"`, déjalo. Punto.
2. **NO copies código de prompts a Python**: La lógica médica va en filtros, no en prompts.
3. **NO agregues validaciones sin contexto**: Todo filtro debe tener razón de negocio clara.
4. **NO rompas lista blanca de alertas**: Si agregas tipo nuevo, justifica por qué es clínico.

**Esta especificación es normativa. Cambios requieren aprobación explícita del CTO.**

---

**Última actualización**: 2025-11-09
**Commits relevantes**: `099c758`, `9d836c2`, `3bd48c6`, `17d79f3`

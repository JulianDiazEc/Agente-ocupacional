import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  WarningAmber,
  CheckCircle,
  ExpandMore,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';

interface SignosVitales {
  imc?: number;
  peso?: number;
  presion_arterial?: string;
  frecuencia_cardiaca?: number;
  frecuencia_respiratoria?: number;
}

interface Examen {
  nombre?: string;
  tipo_examen?: string;
  interpretacion?: string;
  resultado?: string;
  hallazgos_clave?: string;
  valor_numerico?: number;
  unidad?: string;
  rango_referencia?: string;
}

interface Diagnostico {
  codigo_cie10?: string;
  descripcion?: string;
}

interface Antecedente {
  tipo?: string;
  descripcion?: string;
  activo?: boolean;
}

interface ClinicalSummaryCardProps {
  signos_vitales?: SignosVitales;
  examenes?: Examen[];
  diagnosticos?: Diagnostico[];
  antecedentes?: Antecedente[];
}

const ClinicalSummaryCard: React.FC<ClinicalSummaryCardProps> = ({
  signos_vitales,
  examenes = [],
  diagnosticos = [],
  antecedentes = [],
}) => {
  const [normalExpanded, setNormalExpanded] = useState(false);

  // Función para extraer hallazgos que requieren atención
  const extractAbnormalFindings = () => {
    const findings: string[] = [];

    // 1. TODOS los diagnósticos
    diagnosticos.forEach((diag) => {
      if (diag.descripcion && diag.codigo_cie10) {
        findings.push(`${diag.descripcion} (${diag.codigo_cie10})`);
      }
    });

    // 2. Exámenes alterados
    const abnormalExams = examenes.filter(
      (ex) => ex.interpretacion?.toLowerCase() === 'alterado'
    );

    abnormalExams.forEach((ex) => {
      let examText = ex.nombre || ex.tipo_examen || 'Examen';

      if (ex.valor_numerico !== undefined && ex.valor_numerico !== null) {
        // Tiene valor numérico
        const valor = ex.valor_numerico;
        const unidad = ex.unidad || '';
        const rango = ex.rango_referencia || '';

        // Determinar flecha (simplificado - idealmente parsear el rango)
        let arrow = '';
        if (rango) {
          // Intentar parsear rango tipo "0-200" o "<200"
          const match = rango.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
          if (match) {
            const min = parseFloat(match[1]);
            const max = parseFloat(match[2]);
            if (valor > max) arrow = ' ↑';
            else if (valor < min) arrow = ' ↓';
          } else if (rango.includes('<')) {
            const limit = parseFloat(rango.replace(/[<>]/g, ''));
            if (valor > limit) arrow = ' ↑';
          } else if (rango.includes('>')) {
            const limit = parseFloat(rango.replace(/[<>]/g, ''));
            if (valor < limit) arrow = ' ↓';
          }
        }

        examText = `${examText}: ${valor} ${unidad}${arrow}${
          rango ? ` (Ref: ${rango})` : ''
        }`;
      } else {
        // No tiene valor numérico
        const detail = ex.hallazgos_clave || ex.resultado || '';
        if (detail) {
          examText = `${examText}: ${detail}`;
        }
      }

      findings.push(examText);
    });

    // 3. Signos vitales fuera de rango
    if (signos_vitales) {
      const { imc, presion_arterial, frecuencia_cardiaca, frecuencia_respiratoria } =
        signos_vitales;

      // IMC
      if (imc !== undefined && imc !== null) {
        if (imc >= 30) {
          findings.push(`Obesidad (IMC: ${imc.toFixed(1)})`);
        } else if (imc >= 25) {
          findings.push(`Sobrepeso (IMC: ${imc.toFixed(1)})`);
        } else if (imc < 18.5) {
          findings.push(`Bajo peso (IMC: ${imc.toFixed(1)})`);
        }
      }

      // Presión arterial
      if (presion_arterial) {
        const match = presion_arterial.match(/(\d+)\/(\d+)/);
        if (match) {
          const sistolica = parseInt(match[1]);
          const diastolica = parseInt(match[2]);

          if (sistolica >= 140 || diastolica >= 90) {
            findings.push(`Presión arterial elevada (${presion_arterial})`);
          } else if (sistolica >= 130 || diastolica >= 80) {
            findings.push(`Presión arterial limítrofe (${presion_arterial})`);
          }
        }
      }

      // Frecuencia cardíaca
      if (frecuencia_cardiaca !== undefined && frecuencia_cardiaca !== null) {
        if (frecuencia_cardiaca > 100) {
          findings.push(`Taquicardia (FC: ${frecuencia_cardiaca} lpm)`);
        } else if (frecuencia_cardiaca < 60) {
          findings.push(`Bradicardia (FC: ${frecuencia_cardiaca} lpm)`);
        }
      }

      // Frecuencia respiratoria
      if (
        frecuencia_respiratoria !== undefined &&
        frecuencia_respiratoria !== null
      ) {
        if (frecuencia_respiratoria > 20) {
          findings.push(`Taquipnea (FR: ${frecuencia_respiratoria} rpm)`);
        } else if (frecuencia_respiratoria < 12) {
          findings.push(`Bradipnea (FR: ${frecuencia_respiratoria} rpm)`);
        }
      }
    }

    // 4. Antecedentes activos
    const activeAntecedentes = antecedentes.filter((ant) => ant.activo === true);

    const antByType: Record<string, string[]> = {
      personales: [],
      familiares: [],
      otros: [],
    };

    activeAntecedentes.forEach((ant) => {
      const desc = ant.descripcion || '';
      if (!desc) return;

      switch (ant.tipo?.toLowerCase()) {
        case 'patologico':
          antByType.personales.push(desc);
          break;
        case 'familiar':
          antByType.familiares.push(desc);
          break;
        case 'toxicologico':
          antByType.otros.push(desc);
          break;
        default:
          antByType.otros.push(desc);
      }
    });

    // Agregar antecedentes al final
    if (antByType.personales.length > 0) {
      findings.push(`Personales: ${antByType.personales.join(', ')}`);
    }
    if (antByType.familiares.length > 0) {
      findings.push(`Familiares: ${antByType.familiares.join(', ')}`);
    }
    if (antByType.otros.length > 0) {
      findings.push(`Otros: ${antByType.otros.join(', ')}`);
    }

    return findings;
  };

  // Función para extraer exámenes normales
  const extractNormalExams = () => {
    return examenes.filter(
      (ex) => ex.interpretacion?.toLowerCase() === 'normal'
    );
  };

  const abnormalFindings = extractAbnormalFindings();
  const normalExams = extractNormalExams();

  return (
    <Box className="space-y-4 mb-6">
      {/* Subsección A: Hallazgos que requieren atención */}
      <Card className="shadow-sm border-l-4 border-pink-500">
        <CardContent className="p-6 bg-pink-50">
          <Box className="flex items-center gap-2 mb-4">
            <WarningAmber className="text-pink-600" />
            <Typography variant="h6" className="font-semibold text-gray-900">
              Hallazgos que requieren atención
            </Typography>
          </Box>

          {abnormalFindings.length > 0 ? (
            <Box component="ul" className="space-y-2 pl-5">
              {abnormalFindings.map((finding, index) => (
                <Typography
                  component="li"
                  key={index}
                  variant="body2"
                  className="text-gray-700"
                >
                  {finding}
                </Typography>
              ))}
            </Box>
          ) : (
            <Typography variant="body2" className="text-gray-500 italic">
              No se identificaron hallazgos anormales
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Subsección B: Parámetros dentro de rangos normales (colapsado) */}
      {normalExams.length > 0 && (
        <Card className="shadow-sm border-l-4 border-green-500">
          <CardContent className="p-6 bg-green-50">
            <Box
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setNormalExpanded(!normalExpanded)}
            >
              <Box className="flex items-center gap-2">
                <CheckCircle className="text-green-600" />
                <Typography variant="h6" className="font-semibold text-gray-900">
                  Parámetros dentro de rangos normales ({normalExams.length}{' '}
                  {normalExams.length === 1 ? 'examen' : 'exámenes'})
                </Typography>
              </Box>
              <IconButton
                size="small"
                sx={{
                  transform: normalExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              >
                <ExpandMore />
              </IconButton>
            </Box>

            <Collapse in={normalExpanded}>
              <Box component="ul" className="space-y-1 pl-5 mt-3">
                {normalExams.map((exam, index) => {
                  const nombre = exam.nombre || exam.tipo_examen || 'Examen';
                  let examText = `✓ ${nombre}`;

                  if (
                    exam.valor_numerico !== undefined &&
                    exam.valor_numerico !== null
                  ) {
                    const unidad = exam.unidad || '';
                    examText += `: ${exam.valor_numerico} ${unidad}`;
                  }

                  return (
                    <Typography
                      component="li"
                      key={index}
                      variant="body2"
                      className="text-gray-700 list-none"
                    >
                      {examText}
                    </Typography>
                  );
                })}
              </Box>
            </Collapse>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ClinicalSummaryCard;

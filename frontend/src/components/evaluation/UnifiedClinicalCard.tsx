import React from 'react';
import { Box, Typography, Card, CardContent, Divider } from '@mui/material';

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

interface Alerta {
  tipo?: string;
  severidad?: 'alta' | 'media' | 'baja';
  mensaje?: string;
  descripcion?: string;
  campo_afectado?: string;
}

interface UnifiedClinicalCardProps {
  signos_vitales?: SignosVitales;
  examenes?: Examen[];
  diagnosticos?: Diagnostico[];
  antecedentes?: Antecedente[];
  alertas?: Alerta[];
}

const UnifiedClinicalCard: React.FC<UnifiedClinicalCardProps> = ({
  signos_vitales,
  examenes = [],
  diagnosticos = [],
  antecedentes = [],
  alertas = [],
}) => {
  // Extraer hallazgos anormales
  const extractAbnormalFindings = () => {
    const findings: string[] = [];

    // 1. Diagnósticos
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
        const valor = ex.valor_numerico;
        const unidad = ex.unidad || '';
        const rango = ex.rango_referencia || '';

        let arrow = '';
        if (rango) {
          const match = rango.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
          if (match) {
            const min = parseFloat(match[1]);
            const max = parseFloat(match[2]);
            if (valor > max) arrow = ' ↑';
            else if (valor < min) arrow = ' ↓';
          }
        }

        examText = `${examText}: ${valor} ${unidad}${arrow}${
          rango ? ` (Ref: ${rango})` : ''
        }`;
      } else {
        const detail = ex.hallazgos_clave || ex.resultado || '';
        if (detail) examText = `${examText}: ${detail}`;
      }

      findings.push(examText);
    });

    // 3. Signos vitales fuera de rango
    if (signos_vitales) {
      const { imc, presion_arterial, frecuencia_cardiaca, frecuencia_respiratoria } =
        signos_vitales;

      if (imc !== undefined && imc !== null) {
        if (imc >= 30) findings.push(`Obesidad (IMC: ${imc.toFixed(1)})`);
        else if (imc >= 25) findings.push(`Sobrepeso (IMC: ${imc.toFixed(1)})`);
        else if (imc < 18.5) findings.push(`Bajo peso (IMC: ${imc.toFixed(1)})`);
      }

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

      if (frecuencia_cardiaca !== undefined && frecuencia_cardiaca !== null) {
        if (frecuencia_cardiaca > 100) {
          findings.push(`Taquicardia (FC: ${frecuencia_cardiaca} lpm)`);
        } else if (frecuencia_cardiaca < 60) {
          findings.push(`Bradicardia (FC: ${frecuencia_cardiaca} lpm)`);
        }
      }

      if (frecuencia_respiratoria !== undefined && frecuencia_respiratoria !== null) {
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
        default:
          antByType.otros.push(desc);
      }
    });

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

  // Extraer exámenes normales
  const extractNormalExams = () => {
    return examenes.filter((ex) => ex.interpretacion?.toLowerCase() === 'normal');
  };

  const abnormalFindings = extractAbnormalFindings();
  const normalExams = extractNormalExams();

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Resumen Clínico
        </Typography>

        {/* Hallazgos que requieren atención */}
        {abnormalFindings.length > 0 && (
          <Box className="mb-6">
            <Typography variant="subtitle2" className="font-semibold text-gray-700 mb-2">
              Hallazgos que requieren atención
            </Typography>
            <Box component="ul" className="space-y-1 pl-5">
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
          </Box>
        )}

        {/* Exámenes normales */}
        {normalExams.length > 0 && (
          <>
            <Divider className="my-4" />
            <Box className="mb-6">
              <Typography variant="subtitle2" className="font-semibold text-gray-700 mb-2">
                Parámetros dentro de rangos normales
              </Typography>
              <Box component="ul" className="space-y-1 pl-5">
                {normalExams.map((exam, index) => {
                  const nombre = exam.nombre || exam.tipo_examen || 'Examen';
                  let examText = nombre;

                  if (exam.valor_numerico !== undefined && exam.valor_numerico !== null) {
                    const unidad = exam.unidad || '';
                    examText += `: ${exam.valor_numerico} ${unidad}`;
                  }

                  return (
                    <Typography
                      component="li"
                      key={index}
                      variant="body2"
                      className="text-gray-600"
                    >
                      {examText}
                    </Typography>
                  );
                })}
              </Box>
            </Box>
          </>
        )}

        {/* Alertas de validación */}
        {alertas.length > 0 && (
          <>
            <Divider className="my-4" />
            <Box>
              <Typography variant="subtitle2" className="font-semibold text-gray-700 mb-2">
                Alertas de validación
              </Typography>
              <Box component="ul" className="space-y-1 pl-5">
                {alertas.map((alerta, index) => {
                  const campo = alerta.campo_afectado || alerta.tipo || 'Alerta';
                  const mensaje = alerta.descripcion || alerta.mensaje || '';

                  return (
                    <Typography
                      component="li"
                      key={index}
                      variant="body2"
                      className="text-gray-700"
                    >
                      <span className="font-medium">{campo}:</span> {mensaje}
                    </Typography>
                  );
                })}
              </Box>
            </Box>
          </>
        )}

        {abnormalFindings.length === 0 && normalExams.length === 0 && alertas.length === 0 && (
          <Typography variant="body2" className="text-gray-500 italic">
            No hay información clínica disponible
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default UnifiedClinicalCard;

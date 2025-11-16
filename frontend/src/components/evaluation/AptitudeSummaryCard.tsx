import React from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';
import {
  CheckCircleOutline,
  WarningAmber,
  CancelOutlined,
  HourglassEmpty,
} from '@mui/icons-material';

interface Diagnostico {
  codigo_cie10?: string;
  descripcion?: string;
}

interface SignosVitales {
  imc?: number;
}

interface Examen {
  tipo_examen?: string;
  resultado?: string;
  hallazgos_clave?: string;
}

interface AptitudeSummaryCardProps {
  aptitud_laboral?: string;
  tipo_emo?: string;
  confianza_extraccion?: number;
  diagnosticos?: Diagnostico[];
  signos_vitales?: SignosVitales;
  examenes?: Examen[];
}

const AptitudeSummaryCard: React.FC<AptitudeSummaryCardProps> = ({
  aptitud_laboral,
  tipo_emo,
  confianza_extraccion,
  diagnosticos = [],
  signos_vitales,
  examenes = [],
}) => {
  const getAptitudConfig = () => {
    const aptitud = aptitud_laboral?.toLowerCase() || '';

    if (aptitud.includes('apto') && !aptitud.includes('restriccion')) {
      return {
        label: 'Apto',
        icon: <CheckCircleOutline className="text-green-600" sx={{ fontSize: 40 }} />,
        color: 'text-green-700',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
      };
    }
    if (aptitud.includes('restriccion')) {
      return {
        label: 'Apto con restricciones',
        icon: <WarningAmber className="text-amber-600" sx={{ fontSize: 40 }} />,
        color: 'text-amber-700',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200',
      };
    }
    if (aptitud.includes('no_apto')) {
      return {
        label: 'No apto',
        icon: <CancelOutlined className="text-red-600" sx={{ fontSize: 40 }} />,
        color: 'text-red-700',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
      };
    }
    return {
      label: 'Pendiente',
      icon: <HourglassEmpty className="text-gray-600" sx={{ fontSize: 40 }} />,
      color: 'text-gray-700',
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
    };
  };

  const extractRelevantFindings = () => {
    const findings: string[] = [];

    // IMC
    if (signos_vitales?.imc) {
      const imc = signos_vitales.imc;
      if (imc >= 30) {
        findings.push(`IMC ${imc.toFixed(1)} – Obesidad + riesgo metabólico`);
      } else if (imc >= 25) {
        findings.push(`IMC ${imc.toFixed(1)} – Sobrepeso + riesgo metabólico`);
      } else if (imc < 18.5) {
        findings.push(`IMC ${imc.toFixed(1)} – Bajo peso`);
      }
    }

    // Diagnósticos relevantes (máximo 4)
    const relevantDiagnoses = diagnosticos
      .filter((d) => d.descripcion && d.codigo_cie10)
      .slice(0, 4);

    relevantDiagnoses.forEach((diag) => {
      const desc = diag.descripcion || '';
      const codigo = diag.codigo_cie10 || '';
      findings.push(`${desc} (${codigo})`);
    });

    // Exámenes con hallazgos anormales
    const abnormalExams = examenes
      .filter(
        (ex) =>
          ex.resultado?.toLowerCase().includes('anormal') ||
          ex.resultado?.toLowerCase().includes('alterado') ||
          ex.hallazgos_clave
      )
      .slice(0, 2);

    abnormalExams.forEach((ex) => {
      if (ex.hallazgos_clave) {
        findings.push(`${ex.tipo_examen}: ${ex.hallazgos_clave}`);
      }
    });

    return findings.slice(0, 5); // Máximo 5 hallazgos
  };

  const config = getAptitudConfig();
  const findings = extractRelevantFindings();

  const formatTipoEmo = (tipo?: string) => {
    if (!tipo) return 'EMO';
    const tipos: Record<string, string> = {
      preingreso: 'Preingreso',
      periodico: 'Periódico',
      post_incapacidad: 'Post-incapacidad',
      cambio_ocupacion: 'Cambio de ocupación',
      retiro: 'Retiro',
    };
    return tipos[tipo] || tipo;
  };

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Estimación de aptitud laboral
        </Typography>

        <Box className="grid md:grid-cols-2 gap-6">
          {/* Columna izquierda: Aptitud */}
          <Box className={`${config.bgColor} ${config.borderColor} border rounded-lg p-6`}>
            <Box className="flex items-center gap-3 mb-3">
              {config.icon}
              <Typography variant="h4" className={`font-bold ${config.color}`}>
                {config.label}
              </Typography>
            </Box>
            <Typography variant="body2" className="text-gray-600">
              {formatTipoEmo(tipo_emo)} · Confianza de extracción:{' '}
              {confianza_extraccion
                ? `${(confianza_extraccion * 100).toFixed(0)}%`
                : 'N/A'}
            </Typography>
          </Box>

          {/* Columna derecha: Hallazgos relevantes */}
          <Box>
            <Typography variant="subtitle2" className="font-semibold text-gray-700 mb-3">
              Hallazgos más relevantes
            </Typography>
            {findings.length > 0 ? (
              <Box component="ul" className="space-y-2 pl-5">
                {findings.map((finding, index) => (
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
                No se identificaron hallazgos relevantes
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default AptitudeSummaryCard;

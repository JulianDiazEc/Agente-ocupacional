import React from 'react';
import { Box, Typography, Card, CardContent, Divider } from '@mui/material';

interface SignosVitales {
  imc?: number;
  peso?: number;
  presion_arterial?: string;
  frecuencia_cardiaca?: number;
}

interface Examen {
  tipo_examen?: string;
  resultado?: string;
  hallazgos_clave?: string;
  valores_relevantes?: string;
}

interface Diagnostico {
  codigo_cie10?: string;
  descripcion?: string;
}

interface KeyFindingsCardProps {
  signos_vitales?: SignosVitales;
  examenes?: Examen[];
  diagnosticos?: Diagnostico[];
}

interface Finding {
  title: string;
  items: string[];
}

const KeyFindingsCard: React.FC<KeyFindingsCardProps> = ({
  signos_vitales,
  examenes = [],
  diagnosticos = [],
}) => {
  const extractKeyFindings = (): Finding[] => {
    const findings: Finding[] = [];

    // 1. IMC y peso
    const imcItems: string[] = [];
    if (signos_vitales?.imc) {
      const imc = signos_vitales.imc;
      let categoria = '';
      if (imc >= 30) categoria = 'Obesidad';
      else if (imc >= 25) categoria = 'Sobrepeso';
      else if (imc < 18.5) categoria = 'Bajo peso';
      else categoria = 'Normal';

      imcItems.push(`IMC: ${imc.toFixed(1)} (${categoria})`);

      if (imc >= 25) {
        imcItems.push('Riesgo metabólico aumentado');
        imcItems.push('Seguimiento nutricional recomendado');
      }
    }
    if (signos_vitales?.peso) {
      imcItems.push(`Peso: ${signos_vitales.peso} kg`);
    }
    if (imcItems.length > 0) {
      findings.push({ title: 'IMC y composición corporal', items: imcItems });
    }

    // 2. Perfil lipídico (de exámenes de laboratorio)
    const labExams = examenes.filter(
      (ex) =>
        ex.tipo_examen?.toLowerCase().includes('laboratorio') ||
        ex.tipo_examen?.toLowerCase().includes('lipid') ||
        ex.tipo_examen?.toLowerCase().includes('colesterol')
    );

    const lipidItems: string[] = [];
    labExams.forEach((exam) => {
      if (exam.hallazgos_clave) {
        const hallazgos = exam.hallazgos_clave.toLowerCase();
        if (
          hallazgos.includes('colesterol') ||
          hallazgos.includes('triglicéridos') ||
          hallazgos.includes('ldl') ||
          hallazgos.includes('hdl')
        ) {
          lipidItems.push(exam.hallazgos_clave);
        }
      }
    });

    // Buscar en diagnósticos relacionados con lípidos
    const lipidDiagnoses = diagnosticos.filter(
      (d) =>
        d.descripcion?.toLowerCase().includes('hiperlipidemia') ||
        d.descripcion?.toLowerCase().includes('colesterol') ||
        d.descripcion?.toLowerCase().includes('dislipidemia')
    );
    lipidDiagnoses.forEach((d) => {
      lipidItems.push(`${d.descripcion} (${d.codigo_cie10})`);
    });

    if (lipidItems.length > 0) {
      findings.push({ title: 'Perfil lipídico', items: lipidItems });
    }

    // 3. Metabolismo / Glucosa
    const glucoseItems: string[] = [];
    labExams.forEach((exam) => {
      if (exam.hallazgos_clave) {
        const hallazgos = exam.hallazgos_clave.toLowerCase();
        if (
          hallazgos.includes('glucosa') ||
          hallazgos.includes('glicemia') ||
          hallazgos.includes('diabetes') ||
          hallazgos.includes('hba1c')
        ) {
          glucoseItems.push(exam.hallazgos_clave);
        }
      }
    });

    const metabolicDiagnoses = diagnosticos.filter(
      (d) =>
        d.descripcion?.toLowerCase().includes('diabetes') ||
        d.descripcion?.toLowerCase().includes('prediabetes') ||
        d.descripcion?.toLowerCase().includes('glucosa')
    );
    metabolicDiagnoses.forEach((d) => {
      glucoseItems.push(`${d.descripcion} (${d.codigo_cie10})`);
    });

    if (glucoseItems.length > 0) {
      findings.push({ title: 'Metabolismo / Glucosa', items: glucoseItems });
    }

    // 4. Presión arterial / Cardiovascular
    const cvItems: string[] = [];
    if (signos_vitales?.presion_arterial) {
      const pa = signos_vitales.presion_arterial;
      cvItems.push(`Presión arterial: ${pa}`);

      // Parsear PA (ej: "120/80")
      const match = pa.match(/(\d+)\/(\d+)/);
      if (match) {
        const sistolica = parseInt(match[1]);
        const diastolica = parseInt(match[2]);

        if (sistolica >= 140 || diastolica >= 90) {
          cvItems.push('Hipertensión arterial detectada');
        } else if (sistolica >= 130 || diastolica >= 85) {
          cvItems.push('Presión arterial en rango prehipertensivo');
        }
      }
    }

    const cvDiagnoses = diagnosticos.filter(
      (d) =>
        d.descripcion?.toLowerCase().includes('hipertens') ||
        d.descripcion?.toLowerCase().includes('cardio')
    );
    cvDiagnoses.forEach((d) => {
      cvItems.push(`${d.descripcion} (${d.codigo_cie10})`);
    });

    if (cvItems.length > 0) {
      findings.push({ title: 'Sistema cardiovascular', items: cvItems });
    }

    // 5. Otros hallazgos relevantes
    const otherDiagnoses = diagnosticos.filter(
      (d) =>
        !d.descripcion?.toLowerCase().includes('hiperlipidemia') &&
        !d.descripcion?.toLowerCase().includes('diabetes') &&
        !d.descripcion?.toLowerCase().includes('hipertens') &&
        !d.descripcion?.toLowerCase().includes('colesterol')
    );

    if (otherDiagnoses.length > 0) {
      const otherItems = otherDiagnoses
        .slice(0, 3)
        .map((d) => `${d.descripcion} (${d.codigo_cie10})`);
      findings.push({ title: 'Otros hallazgos clínicos', items: otherItems });
    }

    return findings;
  };

  const findings = extractKeyFindings();

  if (findings.length === 0) {
    return null;
  }

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Consideraciones clínicas clave
        </Typography>

        <Box className="space-y-4">
          {findings.map((finding, index) => (
            <Box key={index}>
              <Typography
                variant="subtitle2"
                className="font-semibold text-gray-700 mb-2"
              >
                {finding.title}
              </Typography>
              <Box component="ul" className="space-y-1 pl-5">
                {finding.items.map((item, itemIndex) => (
                  <Typography
                    component="li"
                    key={itemIndex}
                    variant="body2"
                    className="text-gray-600"
                  >
                    {item}
                  </Typography>
                ))}
              </Box>
              {index < findings.length - 1 && <Divider className="mt-4" />}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default KeyFindingsCard;

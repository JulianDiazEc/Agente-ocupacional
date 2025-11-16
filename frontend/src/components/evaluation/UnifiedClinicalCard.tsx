import React from 'react';
import { Box, Typography, Card, CardContent, Divider } from '@mui/material';
import {
  LocalHospital,
  Science,
  FavoriteRounded,
  FamilyRestroom,
  CheckCircle,
  WarningAmber,
  Assignment,
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

interface Alerta {
  tipo?: string;
  severidad?: 'alta' | 'media' | 'baja';
  mensaje?: string;
  descripcion?: string;
  campo_afectado?: string;
  accion_sugerida?: string;
}

interface Recomendacion {
  tipo?: string;
  descripcion?: string;
  especialidad?: string;
  prioridad?: 'alta' | 'media' | 'baja';
}

interface UnifiedClinicalCardProps {
  signos_vitales?: SignosVitales;
  examenes?: Examen[];
  diagnosticos?: Diagnostico[];
  antecedentes?: Antecedente[];
  recomendaciones?: Recomendacion[];
  alertas?: Alerta[];
}

const UnifiedClinicalCard: React.FC<UnifiedClinicalCardProps> = ({
  signos_vitales,
  examenes = [],
  diagnosticos = [],
  antecedentes = [],
  recomendaciones = [],
  alertas = [],
}) => {
  // Función para comparar valor con rango y obtener flecha
  const getValueArrow = (valor: number, rango?: string): { arrow: string; color: string } => {
    if (!rango) return { arrow: '', color: '' };

    // Parsear rangos tipo "0-200" o "< 200" o "> 50"
    const rangeMatch = rango.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
    if (rangeMatch) {
      const min = parseFloat(rangeMatch[1]);
      const max = parseFloat(rangeMatch[2]);
      if (valor > max) return { arrow: '↑', color: 'text-pink-600 font-bold' };
      if (valor < min) return { arrow: '↓', color: 'text-gray-500' };
    } else if (rango.includes('<')) {
      const limit = parseFloat(rango.replace(/[<>]/g, ''));
      if (valor > limit) return { arrow: '↑', color: 'text-pink-600 font-bold' };
    } else if (rango.includes('>')) {
      const limit = parseFloat(rango.replace(/[<>]/g, ''));
      if (valor < limit) return { arrow: '↓', color: 'text-gray-500' };
    }

    return { arrow: '', color: '' };
  };

  // Extraer exámenes alterados
  const examenesAlterados = examenes.filter(
    (ex) => ex.interpretacion?.toLowerCase() === 'alterado'
  );

  // Extraer signos vitales fuera de rango
  const signosVitalesFueraRango: string[] = [];
  if (signos_vitales) {
    const { imc, presion_arterial, frecuencia_cardiaca, frecuencia_respiratoria } =
      signos_vitales;

    if (imc !== undefined && imc !== null) {
      if (imc >= 30) signosVitalesFueraRango.push(`Obesidad (IMC: ${imc.toFixed(1)})`);
      else if (imc >= 25) signosVitalesFueraRango.push(`Sobrepeso (IMC: ${imc.toFixed(1)})`);
      else if (imc < 18.5) signosVitalesFueraRango.push(`Bajo peso (IMC: ${imc.toFixed(1)})`);
    }

    if (presion_arterial) {
      const match = presion_arterial.match(/(\d+)\/(\d+)/);
      if (match) {
        const sistolica = parseInt(match[1]);
        const diastolica = parseInt(match[2]);
        if (sistolica >= 140 || diastolica >= 90) {
          signosVitalesFueraRango.push(`Presión arterial elevada (${presion_arterial})`);
        } else if (sistolica >= 130 || diastolica >= 80) {
          signosVitalesFueraRango.push(`Presión arterial limítrofe (${presion_arterial})`);
        }
      }
    }

    if (frecuencia_cardiaca !== undefined && frecuencia_cardiaca !== null) {
      if (frecuencia_cardiaca > 100) {
        signosVitalesFueraRango.push(`Taquicardia (FC: ${frecuencia_cardiaca} lpm)`);
      } else if (frecuencia_cardiaca < 60) {
        signosVitalesFueraRango.push(`Bradicardia (FC: ${frecuencia_cardiaca} lpm)`);
      }
    }

    if (frecuencia_respiratoria !== undefined && frecuencia_respiratoria !== null) {
      if (frecuencia_respiratoria > 20) {
        signosVitalesFueraRango.push(`Taquipnea (FR: ${frecuencia_respiratoria} rpm)`);
      } else if (frecuencia_respiratoria < 12) {
        signosVitalesFueraRango.push(`Bradipnea (FR: ${frecuencia_respiratoria} rpm)`);
      }
    }
  }

  // Extraer antecedentes activos agrupados por tipo
  const antecedentesActivos = antecedentes.filter((ant) => ant.activo === true);
  const antecedentesPatologicos = antecedentesActivos.filter(
    (ant) => ant.tipo?.toLowerCase() === 'patologico'
  );
  const antecedentesFamiliares = antecedentesActivos.filter(
    (ant) => ant.tipo?.toLowerCase() === 'familiar'
  );
  const antecedentesOtros = antecedentesActivos.filter(
    (ant) =>
      ant.tipo?.toLowerCase() !== 'patologico' && ant.tipo?.toLowerCase() !== 'familiar'
  );

  // Extraer exámenes normales
  const examenesNormales = examenes.filter(
    (ex) => ex.interpretacion?.toLowerCase() === 'normal'
  );

  // Función para limpiar y simplificar descripciones de recomendaciones
  const limpiarDescripcion = (_tipo: string | undefined, descripcion: string): string => {
    let desc = descripcion.trim();

    // Remover prefijos redundantes del tipo
    const prefijos = [
      'seguimiento:',
      'inclusion_sve:',
      'tratamiento:',
      'remision_especialista:',
      'remisión:',
      'control:',
      'inclusión en programa sve',
      'inclusión en',
      'seguimiento en',
      'seguimiento con',
      'remisión a eps para',
    ];

    const descLower = desc.toLowerCase();
    for (const prefijo of prefijos) {
      if (descLower.startsWith(prefijo)) {
        desc = desc.substring(prefijo.length).trim();
        break;
      }
    }

    return desc.charAt(0).toUpperCase() + desc.slice(1);
  };

  // Eliminar recomendaciones duplicadas y limpiar descripciones
  const recomendacionesUnicas = recomendaciones.reduce((acc: Recomendacion[], rec) => {
    if (!rec.descripcion) return acc;

    const descripcionLimpia = limpiarDescripcion(rec.tipo, rec.descripcion);
    const descripcionNormalizada = descripcionLimpia.toLowerCase().trim();

    const existe = acc.some((r) => {
      const rDescLimpia = limpiarDescripcion(r.tipo, r.descripcion || '');
      return rDescLimpia.toLowerCase().trim() === descripcionNormalizada;
    });

    if (!existe) {
      acc.push({
        ...rec,
        descripcion: descripcionLimpia,
      });
    }
    return acc;
  }, []);

  const hayContenido =
    diagnosticos.length > 0 ||
    examenesAlterados.length > 0 ||
    signosVitalesFueraRango.length > 0 ||
    antecedentesActivos.length > 0 ||
    examenesNormales.length > 0 ||
    recomendacionesUnicas.length > 0 ||
    alertas.length > 0;

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Resumen Clínico
        </Typography>

        {!hayContenido && (
          <Typography variant="body2" className="text-gray-500 italic">
            No hay información clínica disponible
          </Typography>
        )}

        {/* PRIMERA FILA: 3 Columnas - Diagnósticos | Signos Vitales | Antecedentes */}
        <Box className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* COLUMNA 1: Diagnósticos */}
          {diagnosticos.length > 0 && (
            <Box>
              <Box className="flex items-center gap-2 mb-3">
                <LocalHospital className="text-gray-700" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Diagnósticos
                </Typography>
              </Box>
              <Box component="ul" className="space-y-1.5 pl-5">
                {diagnosticos.map((diag, index) => (
                  <Typography
                    component="li"
                    key={index}
                    variant="body2"
                    className="text-gray-800"
                  >
                    {diag.descripcion} {diag.codigo_cie10 && `(${diag.codigo_cie10})`}
                  </Typography>
                ))}
              </Box>
            </Box>
          )}

          {/* COLUMNA 2: Signos Vitales */}
          {signosVitalesFueraRango.length > 0 && (
            <Box>
              <Box className="flex items-center gap-2 mb-3">
                <FavoriteRounded className="text-gray-700" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Signos Vitales
                </Typography>
              </Box>
              <Box component="ul" className="space-y-1.5 pl-5">
                {signosVitalesFueraRango.map((signo, index) => (
                  <Typography
                    component="li"
                    key={index}
                    variant="body2"
                    className="text-gray-800"
                  >
                    {signo}
                  </Typography>
                ))}
              </Box>
            </Box>
          )}

          {/* COLUMNA 3: Antecedentes Activos */}
          {antecedentesActivos.length > 0 && (
            <Box>
              <Box className="flex items-center gap-2 mb-3">
                <FamilyRestroom className="text-gray-700" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Antecedentes
                </Typography>
              </Box>

              {/* Personales */}
              {antecedentesPatologicos.length > 0 && (
                <Box className="mb-3">
                  <Typography variant="body2" className="font-medium text-gray-800 mb-1">
                    Personales:
                  </Typography>
                  <Box component="ul" className="space-y-1 pl-5">
                    {antecedentesPatologicos.map((ant, index) => (
                      <Typography
                        component="li"
                        key={index}
                        variant="body2"
                        className="text-gray-800"
                      >
                        {ant.descripcion}
                      </Typography>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Familiares */}
              {antecedentesFamiliares.length > 0 && (
                <Box className="mb-3">
                  <Typography variant="body2" className="font-medium text-gray-800 mb-1">
                    Familiares:
                  </Typography>
                  <Box component="ul" className="space-y-1 pl-5">
                    {antecedentesFamiliares.map((ant, index) => (
                      <Typography
                        component="li"
                        key={index}
                        variant="body2"
                        className="text-gray-800"
                      >
                        {ant.descripcion}
                      </Typography>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Otros */}
              {antecedentesOtros.length > 0 && (
                <Box>
                  <Typography variant="body2" className="font-medium text-gray-800 mb-1">
                    Otros:
                  </Typography>
                  <Box component="ul" className="space-y-1 pl-5">
                    {antecedentesOtros.map((ant, index) => (
                      <Typography
                        component="li"
                        key={index}
                        variant="body2"
                        className="text-gray-800"
                      >
                        {ant.descripcion}
                      </Typography>
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </Box>

        {/* SECCIÓN: Exámenes Alterados (ancho completo) */}
        {examenesAlterados.length > 0 && (
          <Box className="mb-6">
            <Box className="flex items-center gap-2 mb-3">
              <Science className="text-gray-700" fontSize="small" />
              <Typography variant="subtitle2" className="font-semibold text-gray-900">
                Exámenes Alterados
              </Typography>
            </Box>

            {/* Tabla para exámenes con valores numéricos */}
            <Box className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 font-semibold text-gray-800">
                      Examen
                    </th>
                    <th className="text-left py-2 px-3 font-semibold text-gray-800">
                      Valor
                    </th>
                    <th className="text-left py-2 px-3 font-semibold text-gray-800">
                      Referencia
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {examenesAlterados.map((exam, index) => {
                    const nombre = exam.nombre || exam.tipo_examen || 'Examen';
                    const hasNumericValue =
                      exam.valor_numerico !== undefined && exam.valor_numerico !== null;

                    if (hasNumericValue) {
                      const { arrow, color } = getValueArrow(
                        exam.valor_numerico!,
                        exam.rango_referencia
                      );

                      return (
                        <tr
                          key={index}
                          className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}
                        >
                          <td className="py-2 px-3 text-gray-800">{nombre}</td>
                          <td className="py-2 px-3 text-gray-900 font-medium">
                            {exam.valor_numerico} {exam.unidad || ''}
                          </td>
                          <td className="py-2 px-3 text-gray-700">
                            {arrow && <span className={`${color} mr-1`}>{arrow}</span>}
                            {exam.rango_referencia || '-'}
                          </td>
                        </tr>
                      );
                    } else {
                      // Examen sin valor numérico
                      const detail = exam.hallazgos_clave || exam.resultado || '';
                      return (
                        <tr
                          key={index}
                          className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}
                        >
                          <td className="py-2 px-3 text-gray-800">{nombre}</td>
                          <td colSpan={2} className="py-2 px-3 text-gray-800">
                            {detail}
                          </td>
                        </tr>
                      );
                    }
                  })}
                </tbody>
              </table>
            </Box>
          </Box>
        )}

        {/* SECCIÓN: Parámetros Normales (siempre visible, sin collapse) */}
        {examenesNormales.length > 0 && (
          <>
            {(diagnosticos.length > 0 ||
              examenesAlterados.length > 0 ||
              signosVitalesFueraRango.length > 0 ||
              antecedentesActivos.length > 0) && <Divider className="my-4" />}
            <Box className="mb-6">
              <Box className="flex items-center gap-2 mb-3">
                <CheckCircle className="text-green-600" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Parámetros dentro de rangos normales
                </Typography>
              </Box>
              <Box component="ul" className="space-y-1.5 pl-5">
                {examenesNormales.map((exam, index) => {
                  const nombre = exam.nombre || exam.tipo_examen || 'Examen';
                  let examText = `✓ ${nombre}`;

                  if (exam.valor_numerico !== undefined && exam.valor_numerico !== null) {
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
            </Box>
          </>
        )}

        {/* SECCIÓN: Remisiones y Recomendaciones (siempre visible, sin collapse) */}
        {recomendacionesUnicas.length > 0 && (
          <>
            <Divider className="my-4" />
            <Box>
              <Box className="flex items-center gap-2 mb-3">
                <Assignment className="text-blue-700" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Remisiones y Recomendaciones
                </Typography>
              </Box>
              <Box component="ul" className="space-y-1.5 pl-5">
                {recomendacionesUnicas.map((rec, index) => {
                  const tipo = rec.tipo?.toLowerCase() || '';
                  const especialidad = rec.especialidad;
                  const prioridad = rec.prioridad;
                  const descripcion = rec.descripcion || '';

                  // Determinar icono según tipo
                  let prefijo = '•';
                  if (
                    tipo.includes('remision') ||
                    tipo.includes('especialista') ||
                    tipo.includes('remisión')
                  ) {
                    prefijo = '→';
                  } else if (tipo.includes('inclusion') || tipo.includes('sve')) {
                    prefijo = '◉';
                  } else if (tipo.includes('seguimiento')) {
                    prefijo = '↻';
                  }

                  return (
                    <Typography
                      component="li"
                      key={index}
                      variant="body2"
                      className="text-gray-800 list-none"
                    >
                      {prefijo} {descripcion}
                      {especialidad && (
                        <span className="text-gray-600 text-xs ml-1">({especialidad})</span>
                      )}
                      {prioridad === 'alta' && (
                        <span className="text-red-600 text-xs font-semibold ml-1">
                          [Urgente]
                        </span>
                      )}
                    </Typography>
                  );
                })}
              </Box>
            </Box>
          </>
        )}

        {/* SECCIÓN: Alertas de Validación (siempre visible, sin collapse) */}
        {alertas.length > 0 && (
          <>
            <Divider className="my-4" />
            <Box>
              <Box className="flex items-center gap-2 mb-3">
                <WarningAmber className="text-amber-600" fontSize="small" />
                <Typography variant="subtitle2" className="font-semibold text-gray-900">
                  Alertas de validación
                </Typography>
              </Box>
              <Box component="ul" className="space-y-2 pl-5">
                {alertas.map((alerta, index) => {
                  const campo = alerta.campo_afectado || alerta.tipo || 'Alerta';
                  const severidad = alerta.severidad || 'baja';
                  const mensaje = alerta.descripcion || alerta.mensaje || '';
                  const accion = alerta.accion_sugerida;

                  const severidadLabel = {
                    alta: 'Alta',
                    media: 'Media',
                    baja: 'Baja',
                  }[severidad];

                  return (
                    <Box component="li" key={index} className="text-gray-800">
                      <Typography variant="body2" className="mb-1">
                        <span className="font-medium">{campo}</span>
                        <span className="text-gray-600 text-xs ml-2">
                          [{severidadLabel}]
                        </span>
                        {mensaje && <span>: {mensaje}</span>}
                      </Typography>
                      {accion && (
                        <Typography variant="body2" className="text-gray-700 pl-4">
                          → {accion}
                        </Typography>
                      )}
                    </Box>
                  );
                })}
              </Box>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default UnifiedClinicalCard;

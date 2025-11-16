/**
 * Componente optimizado para exportación PDF
 * Diseño profesional tipo documento médico
 */

import React from 'react';
import type { HistoriaClinicaProcesada } from '@/types/medical';

interface PDFExportViewProps {
  historia: HistoriaClinicaProcesada;
}

const PDFExportView: React.FC<PDFExportViewProps> = ({ historia }) => {
  const { datos_empleado, tipo_emo, fecha_emo, signos_vitales, examenes, diagnosticos, aptitud_laboral, recomendaciones } = historia;

  // Procesar aptitud laboral
  const aptitud = typeof aptitud_laboral === 'string'
    ? aptitud_laboral
    : aptitud_laboral?.resultado_aptitud || 'pendiente_concepto';

  const aptitudTexto = {
    'apto': 'APTO',
    'apto_sin_restricciones': 'APTO SIN RESTRICCIONES',
    'apto_con_restricciones': 'APTO CON RESTRICCIONES',
    'no_apto_temporal': 'NO APTO TEMPORAL',
    'no_apto_definitivo': 'NO APTO DEFINITIVO',
    'no_apto_permanente': 'NO APTO PERMANENTE',
    'pendiente_concepto': 'PENDIENTE DE CONCEPTO',
  }[aptitud] || aptitud.toUpperCase();

  const aptitudColor = aptitud.includes('apto') && !aptitud.includes('no') ? '#10b981' : '#ef4444';

  // Filtrar exámenes
  const examenesAlterados = examenes?.filter(ex => ex.interpretacion?.toLowerCase() === 'alterado') || [];
  const examenesNormales = examenes?.filter(ex => ex.interpretacion?.toLowerCase() === 'normal') || [];

  // Procesar signos vitales
  const signosAlterados: string[] = [];
  if (signos_vitales) {
    const { imc, presion_arterial, frecuencia_cardiaca, frecuencia_respiratoria } = signos_vitales;

    if (imc !== undefined && imc !== null) {
      if (imc >= 30) signosAlterados.push(`IMC: ${imc.toFixed(1)} (Obesidad)`);
      else if (imc >= 25) signosAlterados.push(`IMC: ${imc.toFixed(1)} (Sobrepeso)`);
      else if (imc < 18.5) signosAlterados.push(`IMC: ${imc.toFixed(1)} (Bajo peso)`);
    }

    if (presion_arterial) {
      const match = presion_arterial.match(/(\d+)\/(\d+)/);
      if (match) {
        const sistolica = parseInt(match[1]);
        const diastolica = parseInt(match[2]);
        if (sistolica >= 140 || diastolica >= 90) {
          signosAlterados.push(`Presión arterial: ${presion_arterial} mmHg (Elevada)`);
        } else if (sistolica >= 130 || diastolica >= 80) {
          signosAlterados.push(`Presión arterial: ${presion_arterial} mmHg (Limítrofe)`);
        }
      }
    }

    if (frecuencia_cardiaca !== undefined && frecuencia_cardiaca !== null) {
      if (frecuencia_cardiaca > 100) signosAlterados.push(`FC: ${frecuencia_cardiaca} lpm (Taquicardia)`);
      else if (frecuencia_cardiaca < 60) signosAlterados.push(`FC: ${frecuencia_cardiaca} lpm (Bradicardia)`);
    }

    if (frecuencia_respiratoria !== undefined && frecuencia_respiratoria !== null) {
      if (frecuencia_respiratoria > 20) signosAlterados.push(`FR: ${frecuencia_respiratoria} rpm (Taquipnea)`);
      else if (frecuencia_respiratoria < 12) signosAlterados.push(`FR: ${frecuencia_respiratoria} rpm (Bradipnea)`);
    }
  }

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      fontSize: '11pt',
      lineHeight: '1.4',
      color: '#1f2937',
      padding: '40px',
      backgroundColor: '#ffffff',
      maxWidth: '210mm',
      margin: '0 auto',
    }}>
      {/* HEADER */}
      <div style={{ borderBottom: '3px solid #EC4899', paddingBottom: '20px', marginBottom: '30px' }}>
        <h1 style={{
          margin: 0,
          fontSize: '20pt',
          fontWeight: 'bold',
          color: '#1f2937',
          marginBottom: '8px'
        }}>
          HISTORIA CLÍNICA OCUPACIONAL
        </h1>
        <div style={{ fontSize: '10pt', color: '#6b7280' }}>
          Examen Médico Ocupacional - {tipo_emo?.toUpperCase() || 'PERIÓDICO'}
        </div>
      </div>

      {/* DATOS DEL PACIENTE */}
      <div style={{ marginBottom: '30px', backgroundColor: '#f9fafb', padding: '20px', borderRadius: '8px' }}>
        <h2 style={{ margin: '0 0 15px 0', fontSize: '14pt', fontWeight: 'bold', color: '#1f2937' }}>
          DATOS DEL PACIENTE
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <span style={{ fontWeight: 'bold' }}>Nombre:</span> {datos_empleado.nombre_completo}
          </div>
          <div>
            <span style={{ fontWeight: 'bold' }}>Documento:</span> {datos_empleado.documento}
          </div>
          <div>
            <span style={{ fontWeight: 'bold' }}>Edad:</span> {datos_empleado.edad || 'N/A'} años
          </div>
          <div>
            <span style={{ fontWeight: 'bold' }}>Fecha EMO:</span> {new Date(fecha_emo).toLocaleDateString('es-CO')}
          </div>
          <div>
            <span style={{ fontWeight: 'bold' }}>Cargo:</span> {datos_empleado.cargo || 'N/A'}
          </div>
          <div>
            <span style={{ fontWeight: 'bold' }}>Empresa:</span> {datos_empleado.empresa || 'N/A'}
          </div>
        </div>
      </div>

      {/* APTITUD LABORAL */}
      <div style={{
        marginBottom: '30px',
        padding: '20px',
        borderRadius: '8px',
        border: `3px solid ${aptitudColor}`,
        backgroundColor: aptitud.includes('apto') && !aptitud.includes('no') ? '#f0fdf4' : '#fef2f2'
      }}>
        <h2 style={{ margin: '0 0 10px 0', fontSize: '14pt', fontWeight: 'bold', color: '#1f2937' }}>
          CONCEPTO DE APTITUD LABORAL
        </h2>
        <div style={{ fontSize: '16pt', fontWeight: 'bold', color: aptitudColor }}>
          {aptitudTexto}
        </div>
      </div>

      {/* HALLAZGOS CLÍNICOS */}
      {(diagnosticos && diagnosticos.length > 0 || signosAlterados.length > 0 || examenesAlterados.length > 0) && (
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ margin: '0 0 15px 0', fontSize: '14pt', fontWeight: 'bold', color: '#1f2937', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
            HALLAZGOS CLÍNICOS
          </h2>

          {/* Diagnósticos */}
          {diagnosticos && diagnosticos.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '12pt', fontWeight: 'bold', marginBottom: '10px', color: '#374151' }}>
                Diagnósticos
              </h3>
              <ul style={{ margin: '0', paddingLeft: '20px' }}>
                {diagnosticos.map((diag, idx) => (
                  <li key={idx} style={{ marginBottom: '6px' }}>
                    {diag.descripcion} {diag.codigo_cie10 && `(${diag.codigo_cie10})`}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Signos vitales alterados */}
          {signosAlterados.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '12pt', fontWeight: 'bold', marginBottom: '10px', color: '#374151' }}>
                Signos Vitales Alterados
              </h3>
              <ul style={{ margin: '0', paddingLeft: '20px' }}>
                {signosAlterados.map((signo, idx) => (
                  <li key={idx} style={{ marginBottom: '6px', color: '#dc2626' }}>
                    {signo}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Exámenes alterados */}
          {examenesAlterados.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '12pt', fontWeight: 'bold', marginBottom: '10px', color: '#374151' }}>
                Exámenes Paráclínicos Alterados
              </h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10pt' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #d1d5db' }}>
                    <th style={{ textAlign: 'left', padding: '8px', fontWeight: 'bold' }}>Examen</th>
                    <th style={{ textAlign: 'left', padding: '8px', fontWeight: 'bold' }}>Valor</th>
                    <th style={{ textAlign: 'left', padding: '8px', fontWeight: 'bold' }}>Referencia</th>
                  </tr>
                </thead>
                <tbody>
                  {examenesAlterados.map((exam, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '8px' }}>{exam.nombre || exam.tipo_examen}</td>
                      <td style={{ padding: '8px', fontWeight: 'bold', color: '#dc2626' }}>
                        {exam.valor_numerico !== undefined ? `${exam.valor_numerico} ${exam.unidad || ''}` : exam.hallazgos_clave || exam.resultado || '-'}
                      </td>
                      <td style={{ padding: '8px' }}>{exam.rango_referencia || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* EXÁMENES NORMALES */}
      {examenesNormales.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ margin: '0 0 15px 0', fontSize: '14pt', fontWeight: 'bold', color: '#1f2937', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
            PARÁMETROS DENTRO DE RANGOS NORMALES
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10pt' }}>
            {examenesNormales.map((exam, idx) => {
              const nombre = exam.nombre || exam.tipo_examen || 'Examen';
              const valor = exam.valor_numerico !== undefined
                ? `: ${exam.valor_numerico} ${exam.unidad || ''}`
                : '';
              return (
                <div key={idx} style={{ color: '#059669' }}>
                  ✓ {nombre}{valor}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RECOMENDACIONES */}
      {recomendaciones && recomendaciones.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ margin: '0 0 15px 0', fontSize: '14pt', fontWeight: 'bold', color: '#1f2937', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
            RECOMENDACIONES Y REMISIONES
          </h2>
          <ul style={{ margin: '0', paddingLeft: '20px' }}>
            {recomendaciones.map((rec, idx) => (
              <li key={idx} style={{ marginBottom: '8px' }}>
                {rec.descripcion}
                {rec.especialidad && <span style={{ color: '#6b7280', fontSize: '10pt' }}> ({rec.especialidad})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* FOOTER */}
      <div style={{ marginTop: '50px', paddingTop: '20px', borderTop: '2px solid #e5e7eb', fontSize: '9pt', color: '#6b7280', textAlign: 'center' }}>
        <div>Documento generado el {new Date().toLocaleDateString('es-CO')} a las {new Date().toLocaleTimeString('es-CO')}</div>
        <div style={{ marginTop: '5px' }}>Sistema de Gestión de Historias Clínicas Ocupacionales</div>
      </div>
    </div>
  );
};

export default PDFExportView;

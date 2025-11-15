import React from 'react';
import { User, FileText, Building, Briefcase, Calendar } from 'lucide-react';
import { DatosEmpleado, HistoriaClinicaProcesada } from '@/types';

interface PatientInfoProps {
  empleado?: DatosEmpleado;
  tipoEMO?: string;
  fechaEMO?: string;
  className?: string;
  historia?: HistoriaClinicaProcesada;
}

/**
 * Grid de información del paciente/empleado
 * Muestra datos estructurados en cards
 */
export const PatientInfo: React.FC<PatientInfoProps> = ({
  empleado,
  tipoEMO,
  fechaEMO,
  historia,
  className = '',
}) => {
  const resolvedEmpleado = historia ? historia.datos_empleado : empleado;
  const resolvedTipoEMO = historia ? historia.tipo_emo : tipoEMO;
  const resolvedFechaEMO = historia ? historia.fecha_emo : fechaEMO;

  if (!resolvedEmpleado) {
    return null;
  }

  const infoItems = [
    {
      icon: <User size={16} />,
      label: 'Nombre completo',
      value: resolvedEmpleado.nombre_completo,
      show: true,
    },
    {
      icon: <FileText size={16} />,
      label: 'Documento',
      value: `${resolvedEmpleado.tipo_documento} ${resolvedEmpleado.documento}`,
      show: true,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Edad',
      value: resolvedEmpleado.edad ? `${resolvedEmpleado.edad} años` : 'No especificado',
      show: !!resolvedEmpleado.edad,
    },
    {
      icon: <Briefcase size={16} />,
      label: 'Cargo',
      value: resolvedEmpleado.cargo || 'No especificado',
      show: !!resolvedEmpleado.cargo,
    },
    {
      icon: <Building size={16} />,
      label: 'Empresa',
      value: resolvedEmpleado.empresa || 'No especificado',
      show: !!resolvedEmpleado.empresa,
      fullWidth: true,
    },
    {
      icon: <FileText size={16} />,
      label: 'Área',
      value: resolvedEmpleado.area || 'No especificado',
      show: !!resolvedEmpleado.area,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Tipo de EMO',
      value: resolvedTipoEMO?.toUpperCase() || 'No especificado',
      show: !!resolvedTipoEMO,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Fecha de EMO',
      value: resolvedFechaEMO ? new Date(resolvedFechaEMO).toLocaleDateString('es-CO') : 'No especificado',
      show: !!resolvedFechaEMO,
    },
  ];

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
      {infoItems.filter(item => item.show).map((item, index) => (
        <div
          key={index}
          className={`
            bg-gray-50 rounded-lg p-4 border border-gray-200
            ${item.fullWidth ? 'md:col-span-2 lg:col-span-3' : ''}
          `}
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="text-gray-400">
              {item.icon}
            </div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {item.label}
            </p>
          </div>
          <p className="text-sm font-medium text-gray-900 break-words">
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
};

export default PatientInfo;

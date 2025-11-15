import React from 'react';
import { User, FileText, Building, Briefcase, Calendar } from 'lucide-react';
import { DatosEmpleado } from '@/types';

interface PatientInfoProps {
  empleado: DatosEmpleado;
  tipoEMO?: string;
  fechaEMO?: string;
  className?: string;
}

/**
 * Grid de información del paciente/empleado
 * Muestra datos estructurados en cards
 */
export const PatientInfo: React.FC<PatientInfoProps> = ({
  empleado,
  tipoEMO,
  fechaEMO,
  className = '',
}) => {
  const infoItems = [
    {
      icon: <User size={16} />,
      label: 'Nombre completo',
      value: empleado.nombre_completo,
      show: true,
    },
    {
      icon: <FileText size={16} />,
      label: 'Documento',
      value: `${empleado.tipo_documento} ${empleado.documento}`,
      show: true,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Edad',
      value: empleado.edad ? `${empleado.edad} años` : 'No especificado',
      show: !!empleado.edad,
    },
    {
      icon: <Briefcase size={16} />,
      label: 'Cargo',
      value: empleado.cargo || 'No especificado',
      show: !!empleado.cargo,
    },
    {
      icon: <Building size={16} />,
      label: 'Empresa',
      value: empleado.empresa || 'No especificado',
      show: !!empleado.empresa,
      fullWidth: true,
    },
    {
      icon: <FileText size={16} />,
      label: 'Área',
      value: empleado.area || 'No especificado',
      show: !!empleado.area,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Tipo de EMO',
      value: tipoEMO?.toUpperCase() || 'No especificado',
      show: !!tipoEMO,
    },
    {
      icon: <Calendar size={16} />,
      label: 'Fecha de EMO',
      value: fechaEMO ? new Date(fechaEMO).toLocaleDateString('es-CO') : 'No especificado',
      show: !!fechaEMO,
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

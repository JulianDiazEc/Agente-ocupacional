import React from 'react';
import { useParams } from 'react-router-dom';
import { Container, CircularProgress, Alert, Stack } from '@mui/material';
import { useEmpresa } from '../hooks/useEmpresa';
import { empresaApi } from '../services/empresaApi';
import { EmpresaDetailForm } from '../components/EmpresaDetailForm';
import { GesSection } from '../components/GesSection';
import { SveSection } from '../components/SveSection';

export const EmpresaDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, saving, saveEmpresa, refetch } = useEmpresa(id);

  if (!id) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">ID de empresa inválido</Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 6, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !data) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error || 'No se pudo cargar la empresa'}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <EmpresaDetailForm empresa={data} saving={saving} error={error} onSave={saveEmpresa} />
        <GesSection
          ges={data.ges}
          onCreate={async (values) => {
            await empresaApi.addGes(data.id, values);
            await refetch();
          }}
          onUpdate={async (gesId, values) => {
            await empresaApi.updateGes(data.id, gesId, values);
            await refetch();
          }}
        />
        <SveSection
          sve={data.sve}
          onUpdate={async (tipos) => {
            await empresaApi.setSve(data.id, tipos);
            await refetch();
          }}
        />
      </Stack>
    </Container>
  );
};

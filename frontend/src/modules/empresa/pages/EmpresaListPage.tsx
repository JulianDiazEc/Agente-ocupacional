import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Box } from '@mui/material';
import { useEmpresas } from '../hooks/useEmpresas';
import { empresaApi } from '../services/empresaApi';
import { EmpresaTable } from '../components/EmpresaTable';
import { CreateEmpresaDialog } from '../components/dialogs/CreateEmpresaDialog';
import { CreateEmpresaInput } from '../types';

export const EmpresaListPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useEmpresas();
  const [open, setOpen] = useState(false);

  const handleCreate = async (values: CreateEmpresaInput) => {
    await empresaApi.createEmpresa(values);
    await refetch();
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box>
        <EmpresaTable
          empresas={data}
          loading={loading}
          error={error}
          onSelect={(empresa) => navigate(`/admin/empresas/${empresa.id}`)}
          onCreate={() => setOpen(true)}
        />
      </Box>
      <CreateEmpresaDialog
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={async (values) => {
          await handleCreate(values);
          setOpen(false);
        }}
      />
    </Container>
  );
};

import React, { useEffect, useState } from 'react';
import { Paper, Box, Typography, Stack, TextField, Button, Alert } from '@mui/material';
import { EmpresaDetail, UpdateEmpresaInput } from '../types';

interface Props {
  empresa: EmpresaDetail;
  saving: boolean;
  error?: string | null;
  onSave: (values: UpdateEmpresaInput) => Promise<void>;
}

export const EmpresaDetailForm: React.FC<Props> = ({ empresa, saving, error, onSave }) => {
  const [values, setValues] = useState<UpdateEmpresaInput>({});
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setValues({
      nombre: empresa.nombre,
      nit: empresa.nit,
      responsable_sst_nombre: empresa.responsable_sst_nombre,
      responsable_sst_email: empresa.responsable_sst_email,
      responsable_sst_telefono: empresa.responsable_sst_telefono,
    });
  }, [empresa]);

  const handleChange = (key: keyof UpdateEmpresaInput) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async () => {
    if (!values.nombre || !values.responsable_sst_nombre || !values.responsable_sst_email || !values.responsable_sst_telefono) {
      setLocalError('Los campos obligatorios no pueden quedar vacíos');
      return;
    }
    setLocalError(null);
    await onSave(values);
  };

  return (
    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
      <Box px={3} py={2} borderBottom="1px solid" borderColor="divider">
        <Typography variant="h6">Datos básicos</Typography>
        <Typography variant="body2" color="text.secondary">
          Información general de la empresa
        </Typography>
      </Box>
      <Box p={3}>
        <Stack spacing={2}>
          {(localError || error) && <Alert severity="error">{localError || error}</Alert>}
          <TextField label="Nombre" value={values.nombre || ''} onChange={handleChange('nombre')} required fullWidth />
          <TextField label="NIT" value={values.nit || ''} onChange={handleChange('nit')} fullWidth />
          <TextField
            label="Responsable SST"
            value={values.responsable_sst_nombre || ''}
            onChange={handleChange('responsable_sst_nombre')}
            required
            fullWidth
          />
          <TextField
            label="Email Responsable"
            value={values.responsable_sst_email || ''}
            onChange={handleChange('responsable_sst_email')}
            required
            fullWidth
          />
          <TextField
            label="Teléfono Responsable"
            value={values.responsable_sst_telefono || ''}
            onChange={handleChange('responsable_sst_telefono')}
            required
            fullWidth
          />
          <Box display="flex" justifyContent="flex-end">
            <Button variant="contained" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar cambios'}
            </Button>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
};

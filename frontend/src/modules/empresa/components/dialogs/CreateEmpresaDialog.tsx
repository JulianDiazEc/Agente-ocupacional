import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack,
  Button,
  Alert,
} from '@mui/material';
import { CreateEmpresaInput } from '../../types';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (values: CreateEmpresaInput) => Promise<void>;
}

const initialState: CreateEmpresaInput = {
  nombre: '',
  nit: '',
  responsable_sst_nombre: '',
  responsable_sst_email: '',
  responsable_sst_telefono: '',
};

export const CreateEmpresaDialog: React.FC<Props> = ({ open, onClose, onSubmit }) => {
  const [values, setValues] = useState<CreateEmpresaInput>(initialState);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (key: keyof CreateEmpresaInput) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        ...values,
        nit: values.nit || undefined,
      });
      setValues(initialState);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'No se pudo crear la empresa');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      setValues(initialState);
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Nueva empresa</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2} mt={1}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Nombre" value={values.nombre} onChange={handleChange('nombre')} required fullWidth />
          <TextField label="NIT" value={values.nit} onChange={handleChange('nit')} fullWidth />
          <TextField
            label="Responsable SST"
            value={values.responsable_sst_nombre}
            onChange={handleChange('responsable_sst_nombre')}
            required
            fullWidth
          />
          <TextField
            label="Email Responsable"
            value={values.responsable_sst_email}
            onChange={handleChange('responsable_sst_email')}
            required
            fullWidth
          />
          <TextField
            label="Teléfono Responsable"
            value={values.responsable_sst_telefono}
            onChange={handleChange('responsable_sst_telefono')}
            required
            fullWidth
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Cancelar
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Guardando...' : 'Crear'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

import React, { useEffect, useMemo, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Stack, Button, Chip, Box, Alert } from '@mui/material';
import { CreateGesInput } from '../../types';

interface Props {
  open: boolean;
  initialValues?: CreateGesInput;
  title?: string;
  onClose: () => void;
  onSubmit: (values: CreateGesInput) => Promise<void>;
}

const defaultValues: CreateGesInput = {
  nombre: '',
  descripcion: '',
  cargos: [],
  peligros_principales: [],
  examenes_incluidos: [],
  criterios_clinicos: '',
  relacion_examenes: '',
};

export const GesDialog: React.FC<Props> = ({ open, onClose, onSubmit, initialValues, title }) => {
  const [values, setValues] = useState<CreateGesInput>(defaultValues);
  const [cargoInput, setCargoInput] = useState('');
  const [peligroInput, setPeligroInput] = useState('');
  const [examenesTexto, setExamenesTexto] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialValues && open) {
      setValues({
        ...defaultValues,
        ...initialValues,
        cargos: initialValues.cargos || [],
        peligros_principales: initialValues.peligros_principales || [],
        examenes_incluidos: initialValues.examenes_incluidos || [],
        criterios_clinicos: initialValues.criterios_clinicos || '',
        relacion_examenes: initialValues.relacion_examenes || '',
      });
      setExamenesTexto((initialValues.examenes_incluidos || []).join('\n'));
    } else if (open) {
      setValues(defaultValues);
      setExamenesTexto('');
    }
    if (!open) {
      setCargoInput('');
      setPeligroInput('');
      setError(null);
    }
  }, [initialValues, open]);

  const dialogTitle = useMemo(() => title || (initialValues ? 'Editar GES' : 'Agregar GES'), [initialValues, title]);

  const addCargo = () => {
    const value = cargoInput.trim();
    if (!value) return;
    setValues((prev) => {
      if (prev.cargos.includes(value)) return prev;
      return { ...prev, cargos: [...prev.cargos, value] };
    });
    setCargoInput('');
  };

  const addPeligro = () => {
    const value = peligroInput.trim();
    if (!value) return;
    setValues((prev) => {
      if (prev.peligros_principales.includes(value)) return prev;
      return { ...prev, peligros_principales: [...prev.peligros_principales, value] };
    });
    setPeligroInput('');
  };

  const removeChip = (key: 'cargos' | 'peligros_principales', value: string) => {
    setValues((prev) => ({
      ...prev,
      [key]: prev[key].filter((item) => item !== value),
    }));
  };

  const handleSubmit = async () => {
    if (!values.nombre.trim()) {
      setError('El nombre es obligatorio');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        ...values,
        examenes_incluidos: examenesTexto
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean),
      });
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'No se pudo agregar el GES');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (saving) return;
    setValues(defaultValues);
    setExamenesTexto('');
    setCargoInput('');
    setPeligroInput('');
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{dialogTitle}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2} mt={1}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Nombre"
            value={values.nombre}
            onChange={(e) => setValues((prev) => ({ ...prev, nombre: e.target.value }))}
            required
            fullWidth
          />
          <TextField
            label="Descripción"
            value={values.descripcion}
            onChange={(e) => setValues((prev) => ({ ...prev, descripcion: e.target.value }))}
            multiline
            rows={3}
          />
          <TextField
            label="Agregar cargo"
            value={cargoInput}
            onChange={(e) => setCargoInput(e.target.value)}
            helperText="Escribe el cargo y presiona Enter para agregarlo"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addCargo();
              }
            }}
          />
          <Box display="flex" flexWrap="wrap" gap={1}>
            {values.cargos.map((cargo) => (
              <Chip key={cargo} label={cargo} onDelete={() => removeChip('cargos', cargo)} />
            ))}
          </Box>
          <TextField
            label="Agregar peligro principal"
            value={peligroInput}
            onChange={(e) => setPeligroInput(e.target.value)}
            helperText="Escribe el peligro y presiona Enter para agregarlo"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addPeligro();
              }
            }}
          />
          <Box display="flex" flexWrap="wrap" gap={1}>
            {values.peligros_principales.map((peligro) => (
              <Chip key={peligro} label={peligro} onDelete={() => removeChip('peligros_principales', peligro)} />
            ))}
          </Box>
          <TextField
            label="Exámenes incluidos (uno por línea)"
            value={examenesTexto}
            onChange={(e) => setExamenesTexto(e.target.value)}
            multiline
            rows={3}
          />
          <TextField
            label="Criterios clínicos"
            value={values.criterios_clinicos}
            onChange={(e) => setValues((prev) => ({ ...prev, criterios_clinicos: e.target.value }))}
            multiline
            rows={2}
          />
          <TextField
            label="Relación entre exámenes, hallazgos y decisiones"
            value={values.relacion_examenes}
            onChange={(e) => setValues((prev) => ({ ...prev, relacion_examenes: e.target.value }))}
            multiline
            rows={2}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Cancelar
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Guardando...' : 'Agregar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

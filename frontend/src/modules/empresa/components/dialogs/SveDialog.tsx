import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  Stack,
} from '@mui/material';
import { Sve, SveTipo } from '../../types';

const SVE_OPTIONS: { value: SveTipo; label: string }[] = [
  { value: 'voz' as SveTipo, label: 'Voz' },
  { value: 'auditivo' as SveTipo, label: 'Auditivo' },
  { value: 'quimico' as SveTipo, label: 'Químico' },
  { value: 'cardiovascular' as SveTipo, label: 'Cardiovascular' },
  { value: 'psicosocial' as SveTipo, label: 'Psicosocial' },
  { value: 'osteomuscular' as SveTipo, label: 'Osteomuscular' },
  { value: 'btx' as SveTipo, label: 'BTX' },
  { value: 'biologico' as SveTipo, label: 'Biológico' },
  { value: 'dme' as SveTipo, label: 'DME' },
  { value: 'radiaciones ionizantes' as SveTipo, label: 'Radiaciones Ionizantes' },
];

interface Props {
  open: boolean;
  selected: Sve[];
  onClose: () => void;
  onSubmit: (tipos: SveTipo[]) => Promise<void>;
}

export const SveDialog: React.FC<Props> = ({ open, onClose, onSubmit, selected }) => {
  const [localSelection, setLocalSelection] = useState<SveTipo[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLocalSelection(selected.map((item) => (item.tipo || 'visual') as SveTipo));
      setError(null);
    }
  }, [open, selected]);

  const toggleTipo = (tipo: SveTipo) => {
    setLocalSelection((prev) =>
      prev.includes(tipo) ? prev.filter((t) => t !== tipo) : [...prev, tipo]
    );
  };

  const handleSubmit = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSubmit(localSelection);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'No se pudo actualizar la lista de SVE');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (saving) return;
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Selecciona los SVE activos</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}
          <FormGroup>
            {SVE_OPTIONS.map((option) => (
              <FormControlLabel
                key={option.value}
                control={
                  <Checkbox
                    checked={localSelection.includes(option.value)}
                    onChange={() => toggleTipo(option.value)}
                  />
                }
                label={option.label}
              />
            ))}
          </FormGroup>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Cancelar
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Guardando...' : 'Guardar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

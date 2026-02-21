import React, { useState } from 'react';
import { Paper, Box, Typography, Button, Stack, Chip, Alert } from '@mui/material';
import { Sve, SveTipo } from '../types';
import { SveDialog } from './dialogs/SveDialog';

const SVE_LABELS: Record<SveTipo, string> = {
  visual: 'Visual',
  auditivo: 'Auditivo',
  quimico: 'Químico',
  cardiovascular: 'Cardiovascular',
  psicosocial: 'Psicosocial',
  osteomuscular: 'Osteomuscular',
  btx: 'BTX',
};

interface Props {
  sve: Sve[];
  onUpdate: (tipos: SveTipo[]) => Promise<void>;
}

export const SveSection: React.FC<Props> = ({ sve, onUpdate }) => {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async (tipos: SveTipo[]) => {
    try {
      setError(null);
      await onUpdate(tipos);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'No se pudo actualizar la lista de SVE');
      throw err;
    }
  };

  return (
    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
      <Box
        px={3}
        py={2}
        borderBottom="1px solid"
        borderColor="divider"
        display="flex"
        justifyContent="space-between"
        alignItems="center"
      >
        <div>
          <Typography variant="h6">Sistemas de vigilancia epidemiológica</Typography>
          <Typography variant="body2" color="text.secondary">
            Selecciona qué SVE aplica para esta empresa
          </Typography>
        </div>
        <Button variant="outlined" onClick={() => setOpen(true)}>
          Configurar SVE
        </Button>
      </Box>
      <Box p={3}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {sve.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No hay sistemas configurados.
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {sve.map((item) => (
              <Chip key={item.id} label={item.tipo ? SVE_LABELS[item.tipo] || item.tipo : item.nombre} />
            ))}
          </Stack>
        )}
      </Box>
      <SveDialog
        open={open}
        selected={sve}
        onClose={() => setOpen(false)}
        onSubmit={async (tipos) => {
          await handleUpdate(tipos);
          setOpen(false);
        }}
      />
    </Paper>
  );
};

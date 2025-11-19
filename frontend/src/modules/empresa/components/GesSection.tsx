import React, { useState } from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  Stack,
  Chip,
  Alert,
} from '@mui/material';
import { Ges, CreateGesInput } from '../types';
import { GesDialog } from './dialogs/GesDialog';

interface Props {
  ges: Ges[];
  onCreate: (values: CreateGesInput) => Promise<void>;
  onUpdate: (gesId: string, values: CreateGesInput) => Promise<void>;
}

export const GesSection: React.FC<Props> = ({ ges, onCreate, onUpdate }) => {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Ges | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (values: CreateGesInput) => {
    try {
      setError(null);
      await onCreate(values);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'No se pudo crear el GES');
      throw err;
    }
  };

  return (
    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
      <Box px={3} py={2} borderBottom="1px solid" borderColor="divider" display="flex" justifyContent="space-between" alignItems="center">
        <div>
          <Typography variant="h6">Grupos de exposición (GES)</Typography>
          <Typography variant="body2" color="text.secondary">
            Define los grupos de riesgo de la empresa
          </Typography>
        </div>
        <Button
          variant="outlined"
          onClick={() => {
            setEditing(null);
            setOpen(true);
          }}
        >
          Agregar GES
        </Button>
      </Box>
      <Box p={3}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {ges.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No hay grupos configurados.
          </Typography>
        ) : (
          <List disablePadding>
            {ges.map((item, index) => (
              <React.Fragment key={item.id}>
                {index !== 0 && <Divider sx={{ my: 1.5 }} />}
                <ListItem alignItems="flex-start" disableGutters>
                  <ListItemText
                    primary={item.nombre}
                    secondary={
                      <Stack spacing={1} mt={1}>
                        {item.descripcion && <Typography variant="body2">{item.descripcion}</Typography>}
                        {(item.cargos || []).length > 0 && (
                          <Stack spacing={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              Cargos
                            </Typography>
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              {(item.cargos || []).map((cargo) => (
                                <Chip key={cargo} size="small" label={cargo} />
                              ))}
                            </Stack>
                          </Stack>
                        )}
                        {(item.peligros_principales || []).length > 0 && (
                          <Stack spacing={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              Peligros principales
                            </Typography>
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              {(item.peligros_principales || []).map((peligro) => (
                                <Chip key={peligro} size="small" label={peligro} />
                              ))}
                            </Stack>
                          </Stack>
                        )}
                        {(item.examenes_incluidos || []).length > 0 && (
                          <Stack spacing={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              Exámenes incluidos
                            </Typography>
                            {item.examenes_incluidos?.map((exam) => (
                              <Typography key={exam} variant="body2">
                                • {exam}
                              </Typography>
                            ))}
                          </Stack>
                        )}
                        {item.criterios_clinicos && (
                          <Typography variant="body2">Criterios clínicos: {item.criterios_clinicos}</Typography>
                        )}
                        {item.relacion_examenes && (
                          <Typography variant="body2">Relación exámenes/hallazgos: {item.relacion_examenes}</Typography>
                        )}
                      </Stack>
                    }
                  />
                  <Button
                    size="small"
                    onClick={() => {
                      setEditing(item);
                      setOpen(true);
                    }}
                  >
                    Editar
                  </Button>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        )}
      </Box>
      <GesDialog
        open={open}
        initialValues={
          editing
            ? {
                nombre: editing.nombre,
                descripcion: editing.descripcion || '',
                cargos: editing.cargos || [],
                peligros_principales: editing.peligros_principales || [],
                examenes_incluidos: editing.examenes_incluidos || [],
                criterios_clinicos: editing.criterios_clinicos || '',
                relacion_examenes: editing.relacion_examenes || '',
              }
            : undefined
        }
        onClose={() => {
          setOpen(false);
          setEditing(null);
        }}
        onSubmit={async (values) => {
          if (editing) {
            await onUpdate(editing.id, values);
          } else {
            await handleCreate(values);
          }
          setOpen(false);
          setEditing(null);
        }}
      />
    </Paper>
  );
};

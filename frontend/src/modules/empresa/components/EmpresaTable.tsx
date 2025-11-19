import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  CircularProgress,
  Alert,
} from '@mui/material';
import { EmpresaBase } from '../types';

interface Props {
  empresas: EmpresaBase[];
  loading: boolean;
  error?: string | null;
  onSelect: (empresa: EmpresaBase) => void;
  onCreate: () => void;
}

export const EmpresaTable: React.FC<Props> = ({ empresas, loading, error, onSelect, onCreate }) => {
  return (
    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" px={3} py={2} borderBottom="1px solid" borderColor="divider">
        <div>
          <Typography variant="h6">Empresas</Typography>
          <Typography variant="body2" color="text.secondary">
            Configura clientes y responsables SST
          </Typography>
        </div>
        <Button variant="contained" onClick={onCreate}>
          Crear empresa
        </Button>
      </Box>
      {loading ? (
        <Box p={4} display="flex" justifyContent="center">
          <CircularProgress />
        </Box>
      ) : error ? (
        <Box p={3}>
          <Alert severity="error">{error}</Alert>
        </Box>
      ) : empresas.length === 0 ? (
        <Box p={4} textAlign="center">
          <Typography variant="body2" color="text.secondary">
            No hay empresas registradas.
          </Typography>
        </Box>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nombre</TableCell>
                <TableCell>NIT</TableCell>
                <TableCell>Responsable SST</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Teléfono</TableCell>
                <TableCell align="center"># GES</TableCell>
                <TableCell align="center"># SVE</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {empresas.map((empresa) => (
                <TableRow key={empresa.id} hover sx={{ cursor: 'pointer' }} onClick={() => onSelect(empresa)}>
                  <TableCell>{empresa.nombre}</TableCell>
                  <TableCell>{empresa.nit || 'N/A'}</TableCell>
                  <TableCell>{empresa.responsable_sst_nombre}</TableCell>
                  <TableCell>{empresa.responsable_sst_email}</TableCell>
                  <TableCell>{empresa.responsable_sst_telefono}</TableCell>
                  <TableCell align="center">{empresa.ges_count ?? 0}</TableCell>
                  <TableCell align="center">{empresa.sve_count ?? 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

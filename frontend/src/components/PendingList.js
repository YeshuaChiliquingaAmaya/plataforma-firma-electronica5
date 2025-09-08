import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Typography, Paper, List, ListItem, ListItemText, CircularProgress, Divider, IconButton, Box, Checkbox, ListItemButton, ListItemIcon } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

// Añadimos 'setPendingDocs' para comunicarnos con el componente padre
function PendingList({ onDocumentSelect, refreshKey, selectedIds, onToggleSelect, setPendingDocs }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/documents/pending');
      setDocuments(response.data);
      setPendingDocs(response.data); // Informamos al padre de la lista de documentos
      setError(null);
    } catch (err) {
      setError('No se pudo cargar la lista de documentos.');
      setDocuments([]);
      setPendingDocs([]); // Informamos al padre que la lista está vacía
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshKey]);

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" gutterBottom>Bandeja de Entrada</Typography>
        <IconButton onClick={fetchDocuments} disabled={isLoading} aria-label="refrescar">
          <RefreshIcon />
        </IconButton>
      </Box>
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}><CircularProgress /></Box>
      ) : (
        <List>
          {documents.length === 0 ? (
            <ListItem><ListItemText primary="No hay documentos pendientes de firma." /></ListItem>
          ) : (
            documents.map((doc, index) => {
              const labelId = `checkbox-list-label-${doc.id}`;
              const isSelected = selectedIds.includes(doc.id);

              return (
                <React.Fragment key={doc.id}>
                  <ListItem disablePadding>
                    <ListItemIcon>
                      <Checkbox
                        edge="start"
                        checked={isSelected}
                        tabIndex={-1}
                        disableRipple
                        inputProps={{ 'aria-labelledby': labelId }}
                        onChange={() => onToggleSelect(doc.id)}
                      />
                    </ListItemIcon>
                    <ListItemButton component="button" onClick={() => onDocumentSelect(doc)}>
                      <ListItemText 
                        id={labelId}
                        primary={doc.original_filename} 
                        secondary={`Esperando firma de Nivel ${doc.current_signer_level}.`} 
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < documents.length - 1 && <Divider />}
                </React.Fragment>
              );
            })
          )}
        </List>
      )}
    </Paper>
  );
}

export default PendingList;
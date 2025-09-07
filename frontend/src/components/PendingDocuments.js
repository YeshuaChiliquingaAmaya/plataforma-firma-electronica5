import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, List, ListItem, ListItemText, CircularProgress, Divider, IconButton } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

// Ahora el componente acepta una prop 'key' que podemos usar para forzar su recarga.
function PendingDocuments({ onDocumentSelect, refreshKey }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Esta función ahora se puede llamar de nuevo para recargar los datos.
  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/documents/pending');
      setDocuments(response.data);
      setError(null);
    } catch (err) {
      setError('No se pudo cargar la lista de documentos.');
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  // useEffect ahora observa la prop 'refreshKey'. Si cambia, vuelve a ejecutar fetchDocuments.
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
            <ListItem>
              <ListItemText primary="No hay documentos pendientes de firma." />
            </ListItem>
          ) : (
            documents.map((doc, index) => (
              <React.Fragment key={doc.id}>
                <ListItem button onClick={() => onDocumentSelect(doc)}>
                  <ListItemText 
                    primary={doc.original_filename} 
                    secondary={`Esperando firma de Nivel ${doc.current_signer_level}.`} 
                  />
                </ListItem>
                {index < documents.length - 1 && <Divider />}
              </React.Fragment>
            ))
          )}
        </List>
      )}
    </Paper>
  );
}

export default PendingDocuments;
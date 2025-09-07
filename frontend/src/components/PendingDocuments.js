import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, List, ListItem, ListItemText, CircularProgress, Divider } from '@mui/material';

function PendingDocuments({ onDocumentSelect }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Esta función se ejecuta automáticamente cuando el componente se carga
    const fetchDocuments = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/documents/pending');
        setDocuments(response.data);
      } catch (err) {
        setError('No se pudo cargar la lista de documentos.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []); // El array vacío [] significa que solo se ejecuta una vez

  if (isLoading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Bandeja de Entrada</Typography>
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
                  secondary={`Esperando firma de Nivel ${doc.current_signer_level}. Estado: ${doc.status}`} 
                />
              </ListItem>
              {index < documents.length - 1 && <Divider />}
            </React.Fragment>
          ))
        )}
      </List>
    </Paper>
  );
}

export default PendingDocuments;
import React, { useState } from 'react';
import { Box, Button, Typography, CircularProgress, Paper } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

function FileUpload({ onUpload, isLoading }) {
  const [pdfFiles, setPdfFiles] = useState([]);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (pdfFiles.length > 0) {
      onUpload(pdfFiles);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>Iniciar Nuevo Flujo de Firma</Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
        <Button variant="outlined" component="label" fullWidth startIcon={<UploadFileIcon />} sx={{ mb: 2 }}>
          Seleccionar PDF(s) para Iniciar Flujo
          <input type="file" hidden accept=".pdf" multiple onChange={(e) => setPdfFiles(Array.from(e.target.files))} />
        </Button>
        
        {pdfFiles.length > 0 && <Typography variant="body2" sx={{ mb: 2 }}>{pdfFiles.length} archivo(s) seleccionado(s).</Typography>}

        <Box sx={{ my: 2, position: 'relative' }}>
          <Button 
            type="submit" 
            fullWidth 
            variant="contained" 
            disabled={isLoading || pdfFiles.length === 0} 
            size="large"
          >
            Subir y Registrar
          </Button>
          {isLoading && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', marginTop: '-12px', marginLeft: '-12px' }} />}
        </Box>
      </Box>
    </Paper>
  );
}

export default FileUpload;
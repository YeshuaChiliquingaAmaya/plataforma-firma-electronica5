import React, { useState } from 'react';
import { Box, Button, TextField, Typography, CircularProgress } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

function SignForm({ onSubmit, onPdfSelect, isLoading }) {
  const [pdfFiles, setPdfFiles] = useState([]);
  const [certFile, setCertFile] = useState(null);
  const [password, setPassword] = useState('');
  const [reason, setReason] = useState('Documento revisado y aprobado');

    const handlePdfChange = (e) => {
    const files = Array.from(e.target.files);
    setPdfFiles(files);
    // Notificamos al padre sobre los nuevos archivos
    if (onPdfSelect) {
      onPdfSelect(files);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // Pasamos todos los datos del formulario al componente padre (App.js)
    onSubmit({ pdfFiles, certFile, password, reason });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
      <Button variant="outlined" component="label" fullWidth startIcon={<UploadFileIcon />} sx={{ mb: 2 }}>
        1. Seleccionar PDF(s)
       <input type="file" hidden accept=".pdf" multiple onChange={handlePdfChange} />
      </Button>
      {pdfFiles.length > 0 && <Typography variant="body2" sx={{ mb: 2 }}>{pdfFiles.length} archivo(s) seleccionado(s).</Typography>}

      <Button variant="outlined" component="label" fullWidth startIcon={<UploadFileIcon />} sx={{ mb: 2 }}>
        2. Seleccionar Certificado
        <input type="file" hidden accept=".p12,.pfx" onChange={(e) => setCertFile(e.target.files[0])} />
      </Button>
      {certFile && <Typography variant="body2" sx={{ mb: 2 }}>{certFile.name}</Typography>}

      <TextField margin="normal" required fullWidth name="password" label="3. Contraseña" type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <TextField margin="normal" fullWidth name="reason" label="4. Razón (Opcional)" type="text" id="reason" value={reason} onChange={(e) => setReason(e.target.value)} />

      <Box sx={{ my: 2, position: 'relative' }}>
        <Button type="submit" fullWidth variant="contained" disabled={isLoading} size="large">
          Firmar Documentos
        </Button>
        {isLoading && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', marginTop: '-12px', marginLeft: '-12px' }} />}
      </Box>
    </Box>
  );
}

export default SignForm;
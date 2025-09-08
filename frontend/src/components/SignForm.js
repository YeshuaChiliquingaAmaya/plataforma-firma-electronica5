import React, { useState } from 'react';
import { Box, Button, TextField, Typography, CircularProgress } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

function SignForm({ onSubmit, isLoading, selectionCount }) {
  const [certFile, setCertFile] = useState(null);
  const [password, setPassword] = useState('');
  const [reason, setReason] = useState('Documento revisado y aprobado');

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({ certFile, password, reason });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
      <Button variant="outlined" component="label" fullWidth startIcon={<UploadFileIcon />} sx={{ mb: 2 }}>
        1. Seleccionar Certificado
        <input type="file" hidden accept=".p12,.pfx" onChange={(e) => setCertFile(e.target.files[0])} />
      </Button>
      {certFile && <Typography variant="body2" sx={{ mb: 2 }}>{certFile.name}</Typography>}

      <TextField margin="normal" required fullWidth name="password" label="2. Contraseña" type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      
      <TextField margin="normal" fullWidth name="reason" label="3. Razón (Opcional)" type="text" id="reason" value={reason} onChange={(e) => setReason(e.target.value)} />

      <Box sx={{ my: 2, position: 'relative' }}>
        <Button 
          type="submit" 
          fullWidth 
          variant="contained" 
          disabled={isLoading || selectionCount === 0}
          size="large"
        >
          {isLoading ? 'Firmando...' : `Firmar ${selectionCount} Documento(s)`}
        </Button>
        {isLoading && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', marginTop: '-12px', marginLeft: '-12px' }} />}
      </Box>
    </Box>
  );
}

export default SignForm;
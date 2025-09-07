import React, { useState, useCallback } from 'react';
import axios from 'axios';

// Importamos los componentes de Material-UI que vamos a usar
import { Box, Button, Container, CssBaseline, TextField, Typography, Alert, CircularProgress, Link } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import UploadFileIcon from '@mui/icons-material/UploadFile';

// Creamos un tema básico para la aplicación
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
  },
});

function App() {
  const [pdfFiles, setPdfFiles] = useState([]);
  const [certFile, setCertFile] = useState(null);
  const [password, setPassword] = useState('');
  const [reason, setReason] = useState('Documento revisado y aprobado');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ message: 'Seleccione los archivos para firmar.', type: 'info' });
  const [downloadLinks, setDownloadLinks] = useState([]);

  const handlePdfChange = (event) => {
    setPdfFiles(Array.from(event.target.files));
  };

  const handleCertChange = (event) => {
    setCertFile(event.target.files[0]);
  };
  
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (pdfFiles.length === 0 || !certFile || !password) {
      setStatus({ message: 'Por favor, complete todos los campos requeridos.', type: 'error' });
      return;
    }

    setIsLoading(true);
    setStatus({ message: `Firmando ${pdfFiles.length} documento(s)...`, type: 'info' });
    setDownloadLinks([]); // Limpiamos los enlaces anteriores

    const newLinks = [];

    for (const pdfFile of pdfFiles) {
      const formData = new FormData();
      formData.append('pdf_file', pdfFile);
      formData.append('cert_file', certFile);
      formData.append('password', password);
      formData.append('reason', reason);
      formData.append('location', 'Ecuador');
      formData.append('page_index', 0);
      formData.append('x_coord', 400);
      formData.append('y_coord', 100);
      formData.append('width', 150);

      try {
        const response = await axios.post('/api/sign', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          responseType: 'blob',
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const signedFileName = `firmado_${pdfFile.name}`;
        newLinks.push({ url, name: signedFileName });

      } catch (error) {
        let errorMessage = 'Ocurrió un error al firmar el archivo.';
        if (error.response && error.response.data) {
          try {
            const errorText = await error.response.data.text();
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorMessage;
          } catch (e) { /* Fallback a mensaje genérico */ }
        }
        setStatus({ message: `Error al firmar ${pdfFile.name}: ${errorMessage}`, type: 'error' });
        setIsLoading(false);
        return;
      }
    }
    
    setDownloadLinks(newLinks);
    setStatus({ message: `¡Éxito! ${pdfFiles.length} documento(s) firmado(s).`, type: 'success' });
    setIsLoading(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Normaliza los estilos CSS en todos los navegadores */}
      <Container maxWidth="sm">
        <Box
          sx={{
            my: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            p: 3,
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 3,
          }}
        >
          <Typography component="h1" variant="h4" gutterBottom>
            Firma Electrónica
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
            Cargue sus documentos y certificado para la firma digital.
          </Typography>

          <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1, width: '100%' }}>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              startIcon={<UploadFileIcon />}
              sx={{ mb: 2 }}
            >
              1. Seleccionar PDF(s)
              <input type="file" hidden accept=".pdf" multiple onChange={handlePdfChange} />
            </Button>
            {pdfFiles.length > 0 && <Typography variant="body2" sx={{ mb: 2 }}>{pdfFiles.length} archivo(s) PDF seleccionado(s).</Typography>}

            <Button
              variant="outlined"
              component="label"
              fullWidth
              startIcon={<UploadFileIcon />}
              sx={{ mb: 2 }}
            >
              2. Seleccionar Certificado (.p12)
              <input type="file" hidden accept=".p12,.pfx" onChange={handleCertChange} />
            </Button>
            {certFile && <Typography variant="body2" sx={{ mb: 2 }}>{certFile.name}</Typography>}

            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="3. Contraseña del Certificado"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            
            <TextField
              margin="normal"
              fullWidth
              name="reason"
              label="4. Razón de la Firma (Opcional)"
              type="text"
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />

            <Box sx={{ my: 2, position: 'relative' }}>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={isLoading}
                size="large"
              >
                Firmar Documentos
              </Button>
              {isLoading && (
                <CircularProgress
                  size={24}
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    marginTop: '-12px',
                    marginLeft: '-12px',
                  }}
                />
              )}
            </Box>
          </Box>
        </Box>
        
        {status.message && (
          <Alert severity={status.type} sx={{ mt: 2 }}>
            {status.message}
          </Alert>
        )}

        {downloadLinks.length > 0 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: '#e8f5e9', borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>Archivos Firmados:</Typography>
            {downloadLinks.map((link, index) => (
              <Typography key={index}>
                <Link href={link.url} download={link.name}>
                  Descargar {link.name}
                </Link>
              </Typography>
            ))}
          </Box>
        )}

      </Container>
    </ThemeProvider>
  );
}

export default App;
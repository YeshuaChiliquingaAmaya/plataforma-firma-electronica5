import React, { useState } from 'react';
import axios from 'axios';

// Importaciones de Material-UI
import { Box, Container, CssBaseline, Typography, Alert, Link, Paper } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import SignForm from './components/SignForm';
import PdfViewer from './components/PdfViewer';

const theme = createTheme({
  palette: { primary: { main: '#1976d2' } },
});

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ message: 'Seleccione los archivos para firmar.', type: 'info' });
  const [downloadLinks, setDownloadLinks] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  
  // --- ¡NUEVO ESTADO PARA LAS COORDENADAS! ---
  const [signatureCoords, setSignatureCoords] = useState({ pageIndex: 0, x: 400, y: 100 });

  const handlePdfSelection = (files) => {
    setSelectedPdf(files[0] || null);
    setDownloadLinks([]);
  };
  
  const handlePageClick = (coords) => {
    // Actualizamos las coordenadas cuando el usuario hace clic en el visor
    setSignatureCoords(coords);
    setStatus({ 
        message: `Posición de firma seleccionada en página ${coords.pageIndex + 1} (X: ${Math.round(coords.x)}, Y: ${Math.round(coords.y)})`, 
        type: 'info' 
    });
  };

  const handleFormSubmit = async ({ pdfFiles, certFile, password, reason }) => {
    if (pdfFiles.length === 0 || !certFile || !password) {
      setStatus({ message: 'Por favor, complete todos los campos requeridos.', type: 'error' });
      return;
    }
    
    setIsLoading(true);
    setStatus({ message: `Firmando ${pdfFiles.length} documento(s)...`, type: 'info' });
    setDownloadLinks([]);
    const newLinks = [];

    for (const pdfFile of pdfFiles) {
      const formData = new FormData();
      formData.append('pdf_file', pdfFile);
      formData.append('cert_file', certFile);
      formData.append('password', password);
      formData.append('reason', reason);
      formData.append('location', 'Ecuador');
      // --- ¡USAMOS LAS COORDENADAS SELECCIONADAS! ---
      formData.append('page_index', signatureCoords.pageIndex);
      formData.append('x_coord', signatureCoords.x);
      formData.append('y_coord', signatureCoords.y);
      formData.append('width', 150); // Mantenemos el ancho fijo por ahora

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
          } catch (e) { /* Fallback */ }
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
      <CssBaseline />
      <Container maxWidth="lg" sx={{ my: 2 }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Firma Electrónica
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
          
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Datos de la Firma</Typography>
              {/* Pasamos la nueva función handlePdfSelection al formulario */}
              <SignForm onSubmit={handleFormSubmit} onPdfSelect={handlePdfSelection} isLoading={isLoading} />
            </Paper>
            {status.message && (
              <Alert severity={status.type}>{status.message}</Alert>
            )}
            {downloadLinks.length > 0 && (
              <Paper elevation={3} sx={{ p: 2, bgcolor: '#e8f5e9' }}>
                <Typography variant="h6" gutterBottom>Archivos Firmados:</Typography>
                {downloadLinks.map((link, index) => (
                  <Typography key={index}>
                    <Link href={link.url} download={link.name}>Descargar {link.name}</Link>
                  </Typography>
                ))}
              </Paper>
            )}
          </Box>

          <Box sx={{ flex: 1.5 }}>
             <Typography variant="h6" gutterBottom>Previsualización (Haz clic para posicionar la firma)</Typography>
             {/* Pasamos la nueva función handlePageClick al visor */}
             <PdfViewer file={selectedPdf} onPageClick={handlePageClick} />
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
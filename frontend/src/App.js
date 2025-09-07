import React, { useState } from 'react';
import axios from 'axios';

// Importaciones de Material-UI
import { Box, Container, CssBaseline, Typography, Alert, Link, Paper } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

// Importamos nuestros componentes
import SignForm from './components/SignForm';
import PdfViewer from './components/PdfViewer';
import PendingDocuments from './components/PendingDocuments';

const theme = createTheme({
  palette: { primary: { main: '#1976d2' } },
});

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ message: 'Bienvenido a la plataforma de firma.', type: 'info' });
  const [downloadLinks, setDownloadLinks] = useState([]);
  
  const [selectedDocument, setSelectedDocument] = useState(null);
  // --- ¡NUEVO ESTADO PARA GUARDAR EL ARCHIVO DEL VISOR! ---
  const [pdfFileForViewer, setPdfFileForViewer] = useState(null);
  
  // --- ¡NUEVA FUNCIÓN PARA MANEJAR LA SELECCIÓN! ---
  const handleDocumentSelect = async (doc) => {
    setSelectedDocument(doc);
    setPdfFileForViewer(null); // Limpiamos el visor anterior
    setStatus({ message: `Cargando previsualización de ${doc.original_filename}...`, type: 'info' });

    try {
      // Llamamos a nuestro nuevo endpoint de descarga
      const response = await axios.get(`/api/documents/${doc.id}/download`, {
        responseType: 'blob', // Esperamos un archivo
      });
      
      // Creamos un objeto File a partir del blob para que react-pdf lo entienda
      const file = new File([response.data], doc.original_filename, { type: 'application/pdf' });
      setPdfFileForViewer(file); // Se lo pasamos al visor
      setStatus({
          message: `Documento '${doc.original_filename}' listo para ser firmado por el Nivel ${doc.current_signer_level}.`,
          type: 'info'
      });
    } catch (err) {
      setStatus({ message: 'Error al cargar la previsualización del PDF.', type: 'error' });
    }
  };


  const handleFormSubmit = async ({ certFile, password, reason }) => {
    if (!selectedDocument || !certFile || !password) {
      setStatus({ message: 'Por favor, seleccione un documento de la bandeja de entrada y complete los datos de firma.', type: 'error' });
      return;
    }
    
    setIsLoading(true);
    setStatus({ message: `Firmando ${selectedDocument.original_filename}...`, type: 'info' });
    setDownloadLinks([]);

    const formData = new FormData();
    formData.append('cert_file', certFile);
    formData.append('password', password);
    formData.append('reason', reason);
    formData.append('signer_level', selectedDocument.current_signer_level);
    formData.append('location', 'Ecuador');

    try {
      const response = await axios.post(`/api/documents/${selectedDocument.id}/sign`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const signedFileName = `firmado_nivel_${selectedDocument.current_signer_level}_${selectedDocument.original_filename}`;
      setDownloadLinks([{ url, name: signedFileName }]);
      setStatus({ message: `¡Éxito! Documento firmado.`, type: 'success' });
    } catch (error) {
      let errorMessage = 'Ocurrió un error al firmar el archivo.';
      if (error.response && error.response.data) {
        try {
          const errorText = await error.response.data.text();
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch (e) { /* Fallback */ }
      }
      setStatus({ message: `Error: ${errorMessage}`, type: 'error' });
    } finally {
        setIsLoading(false);
        // Recargamos la lista de pendientes para que se actualice
        // TODO: En un futuro, esto se puede mejorar para que no recargue toda la página
        window.location.reload(); 
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ my: 2 }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Firma Electrónica Jerárquica
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
          
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <PendingDocuments onDocumentSelect={handleDocumentSelect} />
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                {selectedDocument ? `Firmar: ${selectedDocument.original_filename}` : 'Datos de Firma'}
              </Typography>
              <SignForm onSubmit={handleFormSubmit} isLoading={isLoading} />
            </Paper>
            {status.message && (
              <Alert severity={status.type}>{status.message}</Alert>
            )}
            {downloadLinks.length > 0 && (
              <Paper elevation={3} sx={{ p: 2, bgcolor: '#e8f5e9' }}>
                <Typography variant="h6" gutterBottom>Archivo Firmado:</Typography>
                {downloadLinks.map((link, index) => (
                  <Typography key={index}>
                    <Link href={link.url} download={link.name}>Descargar {link.name}</Link>
                  </Typography>
                ))}
              </Paper>
            )}
          </Box>

          <Box sx={{ flex: 1.5 }}>
             <Typography variant="h6" gutterBottom>Previsualización</Typography>
             {/* ¡AHORA EL VISOR ES COMPLETAMENTE FUNCIONAL! */}
             <PdfViewer file={pdfFileForViewer} />
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
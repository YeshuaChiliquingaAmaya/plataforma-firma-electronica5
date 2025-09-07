import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Importaciones de Material-UI, añadiendo Tabs y Tab
import { Box, Container, CssBaseline, Typography, Alert, Link, Paper, Tabs, Tab } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

// Importamos todos nuestros componentes
import SignForm from './components/SignForm';
import PdfViewer from './components/PdfViewer';
import PendingDocuments from './components/PendingDocuments';
import DocumentUploader from './components/DocumentUploader';

const theme = createTheme({
  palette: { primary: { main: '#1976d2' } },
});

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ message: 'Bienvenido a la plataforma de firma.', type: 'info' });
  const [downloadLinks, setDownloadLinks] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [pdfFileForViewer, setPdfFileForViewer] = useState(null);
  
  // Nuevo estado para controlar la pestaña activa y forzar la recarga de la lista
  const [activeTab, setActiveTab] = useState(0);
  const [refreshPendingList, setRefreshPendingList] = useState(false);

  const handleDocumentSelect = async (doc) => {
    setSelectedDocument(doc);
    setPdfFileForViewer(null);
    setStatus({ message: `Cargando previsualización...`, type: 'info' });

    try {
      const response = await axios.get(`/api/documents/${doc.id}/download`, { responseType: 'blob' });
      const file = new File([response.data], doc.original_filename, { type: 'application/pdf' });
      setPdfFileForViewer(file);
      setStatus({ message: `Documento '${doc.original_filename}' listo para firmar.`, type: 'info' });
    } catch (err) {
      setStatus({ message: 'Error al cargar la previsualización del PDF.', type: 'error' });
    }
  };

  const handleSignSubmit = async ({ certFile, password, reason }) => {
    // ... (Esta función se mantiene igual)
    if (!selectedDocument || !certFile || !password) {
      setStatus({ message: 'Por favor, seleccione un documento de la bandeja y complete los datos de firma.', type: 'error' });
      return;
    }
    setIsLoading(true);
    // ... resto de la lógica ...
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
      // ... manejo de errores ...
    } finally {
        setIsLoading(false);
        setRefreshPendingList(prev => !prev); // Forzamos la recarga de la bandeja de entrada
        setSelectedDocument(null);
        setPdfFileForViewer(null);
    }
  };

  // --- ¡NUEVA FUNCIÓN PARA MANEJAR LA SUBIDA DE NUEVOS DOCUMENTOS! ---
  const handleUploadSubmit = async (filesToUpload) => {
    setIsLoading(true);
    setStatus({ message: `Subiendo ${filesToUpload.length} documento(s)...`, type: 'info' });
    
    let successCount = 0;
    for (const file of filesToUpload) {
      const formData = new FormData();
      formData.append('pdf_file', file);
      try {
        await axios.post('/api/documents', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        successCount++;
      } catch (error) {
        setStatus({ message: `Error al subir ${file.name}.`, type: 'error' });
        setIsLoading(false);
        return; // Detenemos si un archivo falla
      }
    }
    
    setStatus({ message: `${successCount} documento(s) subido(s) con éxito. Cambie a la 'Bandeja de Entrada' para verlos.`, type: 'success' });
    setIsLoading(false);
    setRefreshPendingList(prev => !prev); // Forzamos la recarga de la bandeja
    setActiveTab(0); // Cambiamos a la bandeja de entrada automáticamente
  };


  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ my: 2 }}>
        <Typography component="h1" variant="h4" gutterBottom align="center">
          Plataforma de Firma Electrónica
        </Typography>
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={activeTab} onChange={(event, newValue) => setActiveTab(newValue)}>
            <Tab label="Bandeja de Entrada" />
            <Tab label="Subir Nuevo Documento" />
          </Tabs>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
          
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Contenido condicional basado en la pestaña activa */}
            {activeTab === 0 && (
              <>
                <PendingDocuments onDocumentSelect={handleDocumentSelect} key={refreshPendingList} />
                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    {selectedDocument ? `Firmar: ${selectedDocument.original_filename}` : 'Datos de Firma'}
                  </Typography>
                  <SignForm onSubmit={handleSignSubmit} isLoading={isLoading} />
                </Paper>
              </>
            )}
            {activeTab === 1 && (
              <Paper elevation={3} sx={{ p: 3 }}>
                 <Typography variant="h6" gutterBottom>Iniciar Nuevo Flujo de Firma</Typography>
                 <DocumentUploader onUpload={handleUploadSubmit} isLoading={isLoading} />
              </Paper>
            )}

            {status.message && (<Alert severity={status.type}>{status.message}</Alert>)}
            {downloadLinks.length > 0 && (
              <Paper elevation={3} sx={{ p: 2, bgcolor: '#e8f5e9' }}>
                <Typography variant="h6" gutterBottom>Archivo Firmado:</Typography>
                <Link href={downloadLinks[0].url} download={downloadLinks[0].name}>Descargar {downloadLinks[0].name}</Link>
              </Paper>
            )}
          </Box>

          <Box sx={{ flex: 1.5 }}>
             <Typography variant="h6" gutterBottom>Previsualización</Typography>
             <PdfViewer file={pdfFileForViewer} />
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
import React, { useState } from 'react';
import axios from 'axios';
import { Box, Container, CssBaseline, Typography, Alert, Link, Paper, Tabs, Tab } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import FileUpload from './components/FileUpload';
import PendingList from './components/PendingList';
import SignForm from './components/SignForm';
import PdfViewer from './components/PdfViewer';

const theme = createTheme({
  palette: { primary: { main: '#1976d2' } },
});

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ message: 'Bienvenido.', type: 'info' });
  const [downloadLinks, setDownloadLinks] = useState([]);
  const [pdfFileForViewer, setPdfFileForViewer] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [refreshCounter, setRefreshCounter] = useState(0);
  
  const [pendingDocs, setPendingDocs] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  
  const [signaturePosition, setSignaturePosition] = useState(null);
  const [signatureSize, setSignatureSize] = useState({ width: 150, height: 75 });

  const handleDocumentSelectForPreview = async (doc) => {
    setPdfFileForViewer(null);
    setStatus({ message: `Cargando previsualización de ${doc.original_filename}...`, type: 'info' });
    try {
      const response = await axios.get(`/api/documents/${doc.id}/download`, { responseType: 'blob' });
      const file = new File([response.data], doc.original_filename, { type: 'application/pdf' });
      setPdfFileForViewer(file);
      setStatus({ message: `Documento listo. La posición de firma se aplicará a todos los seleccionados.`, type: 'info' });
    } catch (err) {
      setStatus({ message: 'Error al cargar la previsualización del PDF.', type: 'error' });
    }
  };

  const handleToggleSelect = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  const handlePageClick = (coords) => {
    setSignaturePosition(coords);
    setStatus({ message: `Posición seleccionada en pág. ${coords.pageIndex + 1}`, type: 'info' });
  };

  const handleSignSubmit = async ({ certFile, password, reason }) => {
    if (selectedDocIds.length === 0 || !certFile || !password) {
      setStatus({ message: 'Seleccione al menos un documento y complete los datos de firma.', type: 'error' });
      return;
    }
    if (!signaturePosition) {
      setStatus({ message: 'Por favor, haga clic en el PDF para seleccionar la posición de la firma.', type: 'error' });
      return;
    }

    setIsLoading(true);
    setStatus({ message: `Iniciando firma de ${selectedDocIds.length} documento(s)...`, type: 'info' });
    setDownloadLinks([]);
    const newLinks = [];
    
    // Obtenemos la lista de objetos de documento a firmar
    const docsToSign = pendingDocs.filter(doc => selectedDocIds.includes(doc.id));

    for (const doc of docsToSign) {
      setStatus({ message: `Firmando ${doc.original_filename}...`, type: 'info' });
      const formData = new FormData();
      formData.append('cert_file', certFile);
      formData.append('password', password);
      formData.append('reason', reason);
      formData.append('signer_level', doc.current_signer_level);
      formData.append('location', 'Ecuador');
      formData.append('page_index', signaturePosition.pageIndex);
      formData.append('x_coord', signaturePosition.x);
      formData.append('y_coord', signaturePosition.y);
      formData.append('width', signatureSize.width);

      try {
        const response = await axios.post(`/api/documents/${doc.id}/sign`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }, responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const signedFileName = `firmado_nivel_${doc.current_signer_level}_${doc.original_filename}`;
        newLinks.push({ url, name: signedFileName });
      } catch (error) {
        let errorMessage = 'Ocurrió un error al firmar el archivo.';
        if (error.response && error.response.data) {
          try {
            const errorText = await error.response.data.text();
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorMessage;
          } catch(e) {/* fallback */}
        }
        setStatus({ message: `Error al firmar ${doc.original_filename}: ${errorMessage}`, type: 'error' });
        setIsLoading(false);
        return;
      }
    }
    
    setDownloadLinks(newLinks);
    setStatus({ message: `¡Éxito! ${docsToSign.length} documento(s) firmado(s).`, type: 'success' });
    setIsLoading(false);
    setRefreshCounter(prev => prev + 1);
    setSelectedDocIds([]);
    setPdfFileForViewer(null);
  };
  
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
        return;
      }
    }
    setStatus({ message: `${successCount} documento(s) subido(s) con éxito.`, type: 'success' });
    setIsLoading(false);
    setRefreshCounter(prev => prev + 1);
    setActiveTab(0);
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
            {activeTab === 0 && (
              <>
                <PendingList 
                  onDocumentSelect={handleDocumentSelectForPreview} 
                  refreshKey={refreshCounter}
                  selectedIds={selectedDocIds}
                  onToggleSelect={handleToggleSelect}
                  setPendingDocs={setPendingDocs}
                />
                {selectedDocIds.length > 0 && (
                  <Paper elevation={3} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Datos de Firma
                    </Typography>
                    <SignForm 
                      onSubmit={handleSignSubmit} 
                      isLoading={isLoading} 
                      selectionCount={selectedDocIds.length} 
                    />
                  </Paper>
                )}
              </>
            )}
            {activeTab === 1 && (
               <FileUpload onUpload={handleUploadSubmit} isLoading={isLoading} />
            )}
             <Box sx={{ mt: 2 }}>
              {status.message && (<Alert severity={status.type}>{status.message}</Alert>)}
              {downloadLinks.length > 0 && (
                <Paper elevation={3} sx={{ p: 2, mt: 2, bgcolor: '#e8f5e9' }}>
                  <Typography variant="h6" gutterBottom>Archivos Firmados:</Typography>
                  {downloadLinks.map((link, index) => (
                      <Typography key={index}>
                        <Link href={link.url} download={link.name}>Descargar {link.name}</Link>
                      </Typography>
                    ))}
                </Paper>
              )}
            </Box>
          </Box>
          <Box sx={{ flex: 1.5 }}>
             <Typography variant="h6" gutterBottom>Previsualización</Typography>
             <PdfViewer 
                file={pdfFileForViewer} 
                onPageClick={handlePageClick}
                signatureSize={signatureSize}
                signaturePosition={signaturePosition}
             />
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
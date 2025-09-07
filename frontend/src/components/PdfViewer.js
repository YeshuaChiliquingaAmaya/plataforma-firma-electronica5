import React, { useState } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import './PdfViewer.css'; // Importaremos un nuevo archivo CSS

pdfjs.GlobalWorkerOptions.workerSrc = `/pdf.worker.min.mjs`;

function PdfViewer({ file, onPageClick }) {
  const [numPages, setNumPages] = useState(null);
  const [clickPosition, setClickPosition] = useState(null);
  const [pageDimensions, setPageDimensions] = useState({});

  const handlePageClick = (event, pageNumber) => {
    // Obtenemos las coordenadas relativas al contenedor de la página
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    setClickPosition({ pageIndex: pageNumber - 1, x, y });
    
    // Devolvemos las coordenadas al componente padre (App.js)
    if (onPageClick) {
      const originalPage = pageDimensions[pageNumber];
      if (originalPage) {
        // Convertimos las coordenadas de la vista a las coordenadas reales del PDF
        const scale = rect.width / originalPage.width;
        const originalX = x / scale;
        const originalY = originalPage.height - (y / scale); // El eje Y en PDF es inverso
        onPageClick({ pageIndex: pageNumber - 1, x: originalX, y: originalY });
      }
    }
  };
  
  const handlePageLoad = (page) => {
    // Guardamos las dimensiones originales de la página
    setPageDimensions(prev => ({
        ...prev,
        [page.pageNumber]: { width: page.originalWidth, height: page.originalHeight }
    }));
  };

  if (!file) {
    return (
      <Box sx={{ p: 2, border: '1px dashed grey', borderRadius: 2, textAlign: 'center', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography>Seleccione un archivo PDF para previsualizarlo</Typography>
      </Box>
    );
  }

  return (
    <Paper elevation={4} sx={{ height: 'calc(100vh - 150px)', overflowY: 'auto' }}>
      <Document
        file={file}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
        onLoadError={(error) => console.error('Error al cargar el PDF:', error.message)}
      >
        {Array.from(new Array(numPages), (el, index) => (
          <div key={`page_wrapper_${index + 1}`} className="page-container" onClick={(e) => handlePageClick(e, index + 1)}>
             <Page 
                pageNumber={index + 1}
                onLoadSuccess={handlePageLoad} 
             />
             {clickPosition && clickPosition.pageIndex === index && (
                <div className="click-marker" style={{ left: `${clickPosition.x}px`, top: `${clickPosition.y}px` }}></div>
             )}
          </div>
        ))}
      </Document>
    </Paper>
  );
}

export default PdfViewer;
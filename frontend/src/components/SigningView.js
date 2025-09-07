import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import SignForm from './SignForm';
import PdfViewer from './PdfViewer';

function SigningView({ document, onSignSubmit, isLoading, pdfFile, onPageClick, signatureSize }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, mt: 2 }}>
      {document && (
        <Box sx={{ flex: 1 }}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Firmar: {document.original_filename}
            </Typography>
            <SignForm onSubmit={onSignSubmit} isLoading={isLoading} />
          </Paper>
        </Box>
      )}
      <Box sx={{ flex: 1.5 }}>
        <Typography variant="h6" gutterBottom>Previsualización</Typography>
        <PdfViewer file={pdfFile} onPageClick={onPageClick} signatureSize={signatureSize} />
      </Box>
    </Box>
  );
}

export default SigningView;
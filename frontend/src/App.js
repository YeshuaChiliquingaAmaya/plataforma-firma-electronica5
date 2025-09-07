import React, { useState } from 'react';
import axios from 'axios'; // Importamos axios
import './App.css';

function App() {
  const [pdfFiles, setPdfFiles] = useState([]);
  const [certFile, setCertFile] = useState(null);
  const [password, setPassword] = useState('');
  const [reason, setReason] = useState('Documento revisado y aprobado');
  
  // Nuevo estado para manejar el estado de carga
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('Seleccione los archivos para firmar.');
  const [isError, setIsError] = useState(false);

  const handlePdfChange = (event) => {
    setPdfFiles(Array.from(event.target.files));
  };

  const handleCertChange = (event) => {
    setCertFile(event.target.files[0]);
  };

  // --- ¡AQUÍ ESTÁ LA MAGIA! ---
  // Esta función ahora se comunica con el backend.
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (pdfFiles.length === 0 || !certFile || !password) {
      setMessage('Por favor, complete todos los campos requeridos.');
      setIsError(true);
      return;
    }

    setIsLoading(true);
    setMessage(`Firmando ${pdfFiles.length} documento(s)... por favor espere.`);
    setIsError(false);

    // Usamos un bucle para enviar cada PDF a firmar
    for (const pdfFile of pdfFiles) {
      // FormData es la forma estándar de enviar archivos a una API
      const formData = new FormData();
      formData.append('pdf_file', pdfFile);
      formData.append('cert_file', certFile);
      formData.append('password', password);
      formData.append('reason', reason);
      // Añadimos los demás campos que nuestra API espera
      formData.append('location', 'Ecuador');
      formData.append('page_index', 0);
      formData.append('x_coord', 400);
      formData.append('y_coord', 100);
      formData.append('width', 150);

      try {
        // Hacemos la llamada POST a nuestra API de FastAPI
        const response = await axios.post('/api/sign', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          responseType: 'blob', // ¡Importante! Le decimos que esperamos un archivo como respuesta
        });

        // Creamos una URL temporal para el archivo recibido (blob)
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        // Le damos un nombre al archivo descargado
        link.setAttribute('download', `firmado_${pdfFile.name}`);
        document.body.appendChild(link);
        link.click(); // Simulamos un clic para iniciar la descarga
        
        // Limpiamos
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);

      } catch (error) {
        let errorMessage = 'Ocurrió un error al firmar el archivo.';
        // Si el backend nos da un error específico, lo mostramos
        if (error.response && error.response.data) {
           try {
            // El error del backend viene como un Blob, necesitamos leerlo como texto
            const errorText = await error.response.data.text();
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorMessage;
           } catch (e) {
            // Si no se puede parsear, mostramos el error genérico
           }
        }
        setMessage(`Error al firmar ${pdfFile.name}: ${errorMessage}`);
        setIsError(true);
        setIsLoading(false); // Detenemos la carga si hay un error
        return; // Salimos del bucle si un archivo falla
      }
    }

    // Si todo sale bien
    setMessage(`¡Éxito! ${pdfFiles.length} documento(s) ha(n) sido firmado(s) y descargado(s).`);
    setIsLoading(false);
  };


  return (
    <div className="App">
      <header className="App-header">
        <h1>Plataforma de Firma Electrónica</h1>
        <p>Cargue uno o varios documentos PDF y su certificado para firmarlos digitalmente.</p>
      </header>
      <main>
        <form className="sign-form" onSubmit={handleSubmit}>
          
          <div className="form-group">
            <label htmlFor="pdf-files">1. Seleccione Archivo(s) PDF</label>
            <input 
              type="file" 
              id="pdf-files" 
              accept=".pdf" 
              multiple 
              onChange={handlePdfChange} 
            />
            {pdfFiles.length > 0 && <p>{pdfFiles.length} archivo(s) seleccionado(s)</p>}
          </div>
          
          <div className="form-group">
            <label htmlFor="cert-file">2. Seleccione su Certificado (.p12)</label>
            <input 
              type="file" 
              id="cert-file" 
              accept=".p12,.pfx" 
              onChange={handleCertChange} 
            />
            {certFile && <p>{certFile.name}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="password">3. Ingrese su Contraseña</label>
            <input 
              type="password" 
              id="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="Contraseña del certificado"
            />
          </div>

          <div className="form-group">
            <label htmlFor="reason">4. Razón de la Firma (Opcional)</label>
            <input 
              type="text" 
              id="reason" 
              value={reason} 
              onChange={(e) => setReason(e.target.value)}
            />
          </div>

          <button type="submit" className="submit-btn" disabled={isLoading}>
            {isLoading ? 'Firmando...' : 'Firmar Documentos'}
          </button>
        </form>
        
        <div className={`status-message ${isError ? 'error' : isLoading ? 'loading' : 'success'}`}>
          {message}
        </div>
      </main>
    </div>
  );
}

export default App;
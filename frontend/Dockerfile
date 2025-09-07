# Usar una imagen oficial de Node.js
FROM node:18-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de definición del proyecto
COPY package.json ./
COPY package-lock.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código fuente
COPY . ./

# Exponer el puerto 3000 que usa el servidor de desarrollo de React
EXPOSE 3000

# Comando para iniciar el servidor de desarrollo
CMD ["npm", "start"]
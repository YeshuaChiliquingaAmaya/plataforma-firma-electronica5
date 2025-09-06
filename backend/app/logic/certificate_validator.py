"""
Módulo para validar certificados digitales y extraer información clave.
"""

import os
from datetime import datetime, timezone
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12


class CertificateValidator:
    """Clase para validar y extraer información de certificados digitales"""
    
    def __init__(self):
        self.certificate = None
        self.private_key = None
        self.certificate_info = {}
    
    def load_certificate(self, cert_path, password=None):
        """
        Cargar certificado desde archivo .p12
        
        Args:
            cert_path (str): Ruta del archivo de certificado
            password (str): Contraseña del certificado
            
        Returns:
            tuple: (success, message)
        """
        try:
            if not os.path.exists(cert_path):
                return False, "El archivo de certificado no existe"
            
            if not cert_path.lower().endswith('.p12'):
                return False, "Solo se admiten archivos .p12"
            
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            # Convertir contraseña a bytes si se proporciona
            password_bytes = password.encode('utf-8') if password else None
            
            # Cargar el certificado PKCS12
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                cert_data, password_bytes, default_backend()
            )
            
            self.certificate = certificate
            self.private_key = private_key
            
            # Extraer información del certificado
            self._extract_certificate_info()
            
            return True, "Certificado cargado correctamente"
            
        except ValueError as e:
            if "could not deserialize" in str(e).lower() or "invalid" in str(e).lower():
                return False, "Contraseña incorrecta o archivo corrupto"
            return False, f"Error al cargar certificado: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def _extract_certificate_info(self):
        """Extraer información detallada del certificado"""
        if not self.certificate:
            return
        
        self.certificate_info = {}
        
        try:
            # Información del titular (Subject)
            subject = self.certificate.subject
            self.certificate_info['subject'] = {}
            for attribute in subject:
                oid_name = self._get_oid_name(attribute.oid)
                self.certificate_info['subject'][oid_name] = attribute.value
            
            # Información del emisor (Issuer)
            issuer = self.certificate.issuer
            self.certificate_info['issuer'] = {}
            for attribute in issuer:
                oid_name = self._get_oid_name(attribute.oid)
                self.certificate_info['issuer'][oid_name] = attribute.value
            
            # Fechas de validez
            self.certificate_info['not_valid_before'] = self.certificate.not_valid_before
            self.certificate_info['not_valid_after'] = self.certificate.not_valid_after
            
            # Número de serie
            self.certificate_info['serial_number'] = str(self.certificate.serial_number)
            
            # Versión
            self.certificate_info['version'] = str(self.certificate.version.name)
            
            # Algoritmo de firma
            self.certificate_info['signature_algorithm'] = self.certificate.signature_algorithm_oid._name
            
            # Clave pública
            public_key = self.certificate.public_key()
            self.certificate_info['public_key_size'] = public_key.key_size
            self.certificate_info['public_key_type'] = type(public_key).__name__.replace('PublicKey', '')
            
            # Extensiones importantes
            self.certificate_info['extensions'] = {}
            try:
                # Key Usage
                key_usage = self.certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
                self.certificate_info['extensions']['key_usage'] = self._parse_key_usage(key_usage.value)
            except x509.ExtensionNotFound:
                pass
            
            try:
                # Subject Alternative Name
                san = self.certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                self.certificate_info['extensions']['subject_alt_name'] = [str(name) for name in san.value]
            except x509.ExtensionNotFound:
                pass
            
            try:
                # Basic Constraints
                basic_constraints = self.certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.BASIC_CONSTRAINTS)
                self.certificate_info['extensions']['basic_constraints'] = {
                    'ca': basic_constraints.value.ca,
                    'path_length': basic_constraints.value.path_length
                }
            except x509.ExtensionNotFound:
                pass
            
            # Estado de validez - mejorar manejo de zonas horarias
            now_utc = datetime.now(timezone.utc)
            now_local = datetime.now()
            
            # Obtener fechas del certificado
            not_before = self.certificate_info['not_valid_before']
            not_after = self.certificate_info['not_valid_after']
            
            # Si las fechas del certificado no tienen zona horaria, asumimos que son locales
            if not_before.tzinfo is None:
                not_before = not_before.replace(tzinfo=timezone.utc)
            if not_after.tzinfo is None:
                not_after = not_after.replace(tzinfo=timezone.utc)
            
            # Comparar con tiempo actual
            self.certificate_info['is_valid'] = (not_before <= now_utc <= not_after)
            
            # Información adicional para debug
            self.certificate_info['debug_info'] = {
                'now_utc': now_utc.isoformat(),
                'not_before_normalized': not_before.isoformat(),
                'not_after_normalized': not_after.isoformat(),
                'comparison_result': f"{not_before} <= {now_utc} <= {not_after}"
            }
            
            # Días hasta expiración
            if self.certificate_info['is_valid']:
                days_until_expiry = (not_after - now_utc).days
                self.certificate_info['days_until_expiry'] = max(0, days_until_expiry)
            else:
                # Si está expirado, calcular cuántos días hace que expiró (número negativo)
                days_since_expiry = (now_utc - not_after).days
                self.certificate_info['days_until_expiry'] = -days_since_expiry
            
        except Exception as e:
            print(f"Error extrayendo información del certificado: {e}")
    
    def _get_oid_name(self, oid):
        """Convertir OID a nombre legible"""
        oid_names = {
            x509.oid.NameOID.COMMON_NAME: 'common_name',
            x509.oid.NameOID.COUNTRY_NAME: 'country',
            x509.oid.NameOID.LOCALITY_NAME: 'locality',
            x509.oid.NameOID.STATE_OR_PROVINCE_NAME: 'state_province',
            x509.oid.NameOID.ORGANIZATION_NAME: 'organization',
            x509.oid.NameOID.ORGANIZATIONAL_UNIT_NAME: 'organizational_unit',
            x509.oid.NameOID.EMAIL_ADDRESS: 'email',
            x509.oid.NameOID.SERIAL_NUMBER: 'certificate_serial',
        }
        return oid_names.get(oid, str(oid))
    
    def _parse_key_usage(self, key_usage):
        """Parsear extensiones de uso de clave"""
        usages = []
        if key_usage.digital_signature:
            usages.append('Firma Digital')
        if key_usage.key_encipherment:
            usages.append('Cifrado de Clave')
        if key_usage.data_encipherment:
            usages.append('Cifrado de Datos')
        if key_usage.key_agreement:
            usages.append('Acuerdo de Clave')
        if key_usage.key_cert_sign:
            usages.append('Firma de Certificados')
        if key_usage.crl_sign:
            usages.append('Firma CRL')
        if hasattr(key_usage, 'content_commitment') and key_usage.content_commitment:
            usages.append('No Repudio')
        return usages
    
    def get_certificate_summary(self):
        """Obtener resumen del certificado para mostrar en la UI"""
        if not self.certificate_info:
            return None
        
        # Información básica del titular
        subject_cn = self.certificate_info.get('subject', {}).get('common_name', 'N/A')
        subject_org = self.certificate_info.get('subject', {}).get('organization', 'N/A')
        
        # Información del emisor
        issuer_cn = self.certificate_info.get('issuer', {}).get('common_name', 'N/A')
        issuer_org = self.certificate_info.get('issuer', {}).get('organization', 'N/A')
        
        # Fechas - mejorar formato de visualización
        valid_from = self.certificate_info.get('not_valid_before')
        valid_to = self.certificate_info.get('not_valid_after')
        
        # Formatear fechas para mostrar (usar zona horaria local para display)
        if valid_from:
            if valid_from.tzinfo is not None:
                valid_from_local = valid_from.astimezone()
            else:
                valid_from_local = valid_from
            valid_from_str = valid_from_local.strftime('%d/%m/%Y %H:%M:%S')
        else:
            valid_from_str = 'N/A'
            
        if valid_to:
            if valid_to.tzinfo is not None:
                valid_to_local = valid_to.astimezone()
            else:
                valid_to_local = valid_to
            valid_to_str = valid_to_local.strftime('%d/%m/%Y %H:%M:%S')
        else:
            valid_to_str = 'N/A'
        
        # Estado
        is_valid = self.certificate_info.get('is_valid', False)
        days_until_expiry = self.certificate_info.get('days_until_expiry', 0)
        
        # Información de debug (opcional)
        debug_info = self.certificate_info.get('debug_info', {})
        
        return {
            'subject_name': subject_cn,
            'subject_organization': subject_org,
            'issuer_name': issuer_cn,
            'issuer_organization': issuer_org,
            'valid_from': valid_from_str,
            'valid_to': valid_to_str,
            'is_valid': is_valid,
            'days_until_expiry': days_until_expiry,
            'serial_number': self.certificate_info.get('serial_number', 'N/A'),
            'public_key_type': self.certificate_info.get('public_key_type', 'N/A'),
            'public_key_size': self.certificate_info.get('public_key_size', 'N/A'),
            'signature_algorithm': self.certificate_info.get('signature_algorithm', 'N/A'),
            'key_usage': self.certificate_info.get('extensions', {}).get('key_usage', []),
            'debug_info': debug_info  # Incluir información de debug para troubleshooting
        }
    
    def validate_certificate_chain(self):
        """Validar la cadena de certificados (funcionalidad avanzada)"""
        # Esta funcionalidad se puede implementar más adelante
        # Requiere validación contra CAs raíz
        pass
    
    def export_certificate_info(self, format='dict'):
        """Exportar información del certificado en diferentes formatos"""
        if format == 'dict':
            return self.certificate_info
        elif format == 'pem':
            if self.certificate:
                return self.certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        return None

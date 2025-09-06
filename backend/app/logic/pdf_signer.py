import os
import platform
import datetime
import random
import qrcode
import uuid
from PIL import Image, ImageDraw, ImageFont

from pyhanko.sign.signers import SimpleSigner, PdfSigner
from pyhanko.sign import PdfSignatureMetadata
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.stamp import TextStampStyle

class PDFSigner:
    def __init__(self, cert_path, password, custom_settings=None):
        self.signer = SimpleSigner.load_pkcs12(
            pfx_file=cert_path,
            passphrase=password.encode("utf-8") if password else None
        )
        cert_obj = getattr(self.signer, 'signer_cert', getattr(self.signer, 'signing_cert', None))
        if cert_obj:
            cert_subject_dict = cert_obj.subject.native
            self.cert_subject = cert_subject_dict.get("common_name",
                                 cert_subject_dict.get("organization_name", "NOMBRE NO DISPONIBLE"))
        else:
            self.cert_subject = "NOMBRE NO DISPONIBLE"
            
        # Configuraciones personalizables
        self.settings = {
            'qr_box_size': 12,
            'text_font_size_normal': 60,
            'text_font_size_bold': 120,
            'scale_factor': 4,
            'separacion_1_2': 2,
            'separacion_2_3': 15,
            'separacion_final': 80,
            'desfase_vertical_texto': 120,
            'text_padding_hr': 8,
            'timestamp_offset_seconds': 1,  # Compensación para sincronizar QR con timestamp de firma
            'use_exact_timestamp_sync': False  # Si True, fuerza el mismo timestamp exacto en QR y firma
        }
        
        # Aplicar configuraciones personalizadas si se proporcionan
        if custom_settings:
            self.settings.update(custom_settings)

    def _get_unique_field_name(self, input_pdf):
        """Genera un nombre único para el campo de firma verificando campos existentes"""
        try:
            with open(input_pdf, "rb") as infile:
                reader = PdfFileReader(infile)
                existing_fields = set()
                
                # Obtener campos de firma existentes
                if hasattr(reader.root, '/AcroForm') and reader.root['/AcroForm'] is not None:
                    acro_form = reader.root['/AcroForm']
                    if hasattr(acro_form, '/Fields') and acro_form['/Fields'] is not None:
                        for field_ref in acro_form['/Fields']:
                            field = field_ref.get_object()
                            if hasattr(field, '/T') and field['/T'] is not None:
                                field_name = str(field['/T'])
                                existing_fields.add(field_name)
                
                # Generar nombre único
                base_name = "QRSignature"
                counter = 1
                unique_name = base_name
                
                while unique_name in existing_fields:
                    unique_name = f"{base_name}_{counter}"
                    counter += 1
                
                return unique_name
                
        except Exception as e:
            # Si hay error leyendo el PDF, usar UUID como fallback
            return f"QRSignature_{uuid.uuid4().hex[:8]}"

    def create_stamp_image(self, reason, location, timestamp=None):
        # Si están vacíos, poner un espacio para evitar null en la validación
        if not reason:
            reason = " "
        if not location:
            location = " "
        
        validar_con, version_firma_ec = "https://www.firmadigital.gob.ec", "FirmaEC 4.0.1" # Ejemplo
        
        os_name, os_release = platform.system(), platform.release()
        os_ver_detail = ""
        if os_name == "Windows": os_ver_detail = platform.win32_ver()[0] # e.g., "10"
        elif os_name == "Darwin": os_ver_detail = platform.mac_ver()[0] # e.g., "13.2.1"
        elif os_name == "Linux":
             # Buscar fuentes comunes en Linux, esto puede variar
            common_fonts = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]
            common_fonts_bold = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"]
            font_path_normal = next((f for f in common_fonts if os.path.exists(f)), "default")
            font_path_bold = next((f for f in common_fonts_bold if os.path.exists(f)), "default")
        
        sis_operativo = f"{os_name} {os_ver_detail if os_ver_detail else os_release} 10.0"
        
        # Usar timestamp pasado como parámetro o generar uno nuevo
        if timestamp:
            now = timestamp
        else:
            now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        tz_iso = now.strftime('%z')
        tz_with_colon = f"{tz_iso[:3]}:{tz_iso[3:]}"
        microsegundos = now.microsecond
        nanoseg_aleatorio = random.randint(0, 999)
        fecha_iso = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}.{microsegundos:06d}{nanoseg_aleatorio:03d}{tz_with_colon}"

        qr_text = (
            f"FIRMADO POR: {self.cert_subject}\n"
            f"RAZON: {reason}\n"
            f"LOCALIZACION: {location}\n"
            f"FECHA:\n{fecha_iso}\n"
            f"VALIDAR CON: {validar_con}\n"
            f"Firmado digitalmente con {version_firma_ec}\n"
            f"{sis_operativo}"
        )
        
        QR_BOX_SIZE = self.settings['qr_box_size']
        TEXT_FONT_SIZE_NORMAL = self.settings['text_font_size_normal']
        TEXT_FONT_SIZE_BOLD = self.settings['text_font_size_bold']
        SCALE_FACTOR = self.settings['scale_factor']

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=QR_BOX_SIZE, border=0)
        qr.add_data(qr_text)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        # Explicitly crop any remaining white border from the QR code image itself
        bbox_qr_crop = img_qr.getbbox()
        if bbox_qr_crop:
            img_qr = img_qr.crop(bbox_qr_crop)
        qr_px_width, qr_px_height = img_qr.size

        # Intentar cargar fuentes específicas, si no, usar la default
        font_path_normal, font_path_bold = "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/courbd.ttf" # Courrier New
        if platform.system() == "Darwin": # macOS
            font_path_normal, font_path_bold = "/System/Library/Fonts/Courier.dfont", "/System/Library/Fonts/Courier.dfont" # Bold variant might need specific name
        elif platform.system() == "Linux":
             # Buscar fuentes comunes en Linux, esto puede variar
            common_fonts = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]
            common_fonts_bold = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"]
            font_path_normal = next((f for f in common_fonts if os.path.exists(f)), "default")
            font_path_bold = next((f for f in common_fonts_bold if os.path.exists(f)), "default")


        try: font_normal_hr = ImageFont.truetype(font_path_normal, size=TEXT_FONT_SIZE_NORMAL * SCALE_FACTOR) if font_path_normal != "default" else ImageFont.load_default(size=TEXT_FONT_SIZE_NORMAL * SCALE_FACTOR)
        except IOError: font_normal_hr = ImageFont.load_default(size=TEXT_FONT_SIZE_NORMAL * SCALE_FACTOR)
        try: font_bold_hr = ImageFont.truetype(font_path_bold, size=TEXT_FONT_SIZE_BOLD * SCALE_FACTOR) if font_path_bold != "default" else ImageFont.load_default(size=TEXT_FONT_SIZE_BOLD * SCALE_FACTOR)
        except IOError: font_bold_hr = ImageFont.load_default(size=TEXT_FONT_SIZE_BOLD * SCALE_FACTOR)


        SEPARACION_1_2 = self.settings['separacion_1_2']
        SEPARACION_2_3 = self.settings['separacion_2_3']
        SEPARACION_FINAL = self.settings['separacion_final']
        DESFASE_VERTICAL_TEXTO = self.settings['desfase_vertical_texto']
        line1_text = "Firmado electrónicamente por:"
        tokens = self.cert_subject.upper().split()
        name_line1_str = " ".join(tokens[:2]) if len(tokens) > 2 else " ".join(tokens) or "NO DISPONIBLE"
        name_line2_str = " ".join(tokens[2:]) if len(tokens) > 2 else None
        line3_text = "Validar únicamente con FirmaEC"

        temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        text_lines_data = [
            (line1_text, font_normal_hr),

            (name_line1_str, font_bold_hr),

        ]
        if name_line2_str:
            text_lines_data.append((name_line2_str, font_bold_hr))
        text_lines_data.append((line3_text, font_normal_hr))

        text_heights_scaled = []
        max_text_width_scaled = 0
        for text, font in text_lines_data:
            bbox = temp_draw.textbbox((0,0), text, font=font) # left, top, right, bottom
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_heights_scaled.append(text_height)
            max_text_width_scaled = max(max_text_width_scaled, text_width)

        total_text_height_scaled = text_heights_scaled[0]
        if len(text_heights_scaled) > 1: total_text_height_scaled += (SEPARACION_1_2 * SCALE_FACTOR) + text_heights_scaled[1]
        if name_line2_str and len(text_heights_scaled) > 2: total_text_height_scaled += (SEPARACION_2_3 * SCALE_FACTOR) + text_heights_scaled[2]
        # La última línea (line3_text)
        idx_line3 = 2 if name_line2_str else 1
        if len(text_heights_scaled) > idx_line3 : total_text_height_scaled += (SEPARACION_FINAL * SCALE_FACTOR) + text_heights_scaled[idx_line3+ (1 if name_line2_str else 0)]


        TEXT_PADDING_HR = self.settings['text_padding_hr'] * SCALE_FACTOR
        text_area_width_scaled = max_text_width_scaled + (2 * TEXT_PADDING_HR)
        
        final_img_width_scaled = (qr_px_width * SCALE_FACTOR) + TEXT_PADDING_HR + text_area_width_scaled # QR + padding + text_area
        final_img_height_scaled = max(qr_px_height * SCALE_FACTOR, (DESFASE_VERTICAL_TEXTO * SCALE_FACTOR) + total_text_height_scaled)


        high_res_canvas = Image.new("RGB", (final_img_width_scaled, final_img_height_scaled), color="#FFFFFF")
        draw = ImageDraw.Draw(high_res_canvas)
        high_res_canvas.paste(img_qr.resize((qr_px_width * SCALE_FACTOR, qr_px_height * SCALE_FACTOR), resample=Image.NEAREST), (0, 0))

        text_x_pos_scaled = (qr_px_width * SCALE_FACTOR) + TEXT_PADDING_HR
        current_y_scaled = DESFASE_VERTICAL_TEXTO * SCALE_FACTOR

        # Linea 1
        bbox = draw.textbbox((0,0), line1_text, font=font_normal_hr)
        draw.text((text_x_pos_scaled, current_y_scaled), line1_text, fill="black", font=font_normal_hr)
        current_y_scaled += (bbox[3]-bbox[1]) + (SEPARACION_1_2 * SCALE_FACTOR)

        # Nombre Linea 1
        bbox = draw.textbbox((0,0), name_line1_str, font=font_bold_hr)
        draw.text((text_x_pos_scaled, current_y_scaled), name_line1_str, fill="black", font=font_bold_hr)
        current_y_scaled += (bbox[3]-bbox[1])
        
        if name_line2_str:
            current_y_scaled += (SEPARACION_2_3 * SCALE_FACTOR)
            bbox = draw.textbbox((0,0), name_line2_str, font=font_bold_hr)
            draw.text((text_x_pos_scaled, current_y_scaled), name_line2_str, fill="black", font=font_bold_hr)
            current_y_scaled += (bbox[3]-bbox[1])

        current_y_scaled += (SEPARACION_FINAL * SCALE_FACTOR)
        draw.text((text_x_pos_scaled, current_y_scaled), line3_text, fill="black", font=font_normal_hr)
        
        final_canvas_img = high_res_canvas.resize((final_img_width_scaled // SCALE_FACTOR, final_img_height_scaled // SCALE_FACTOR), resample=Image.LANCZOS)

        # Calculate bounding box of QR code
        qr_bbox = (0, 0, qr_px_width * SCALE_FACTOR, qr_px_height * SCALE_FACTOR)

        # Initialize text bounding box with extreme values
        text_min_x = float('inf')
        text_min_y = float('inf')
        text_max_x = float('-inf')
        text_max_y = float('-inf')

        # Draw text and update text bounding box
        text_x_pos_scaled = (qr_px_width * SCALE_FACTOR) + TEXT_PADDING_HR
        current_y_scaled_for_bbox = DESFASE_VERTICAL_TEXTO * SCALE_FACTOR # Use a separate variable for bbox calculation

        # Line 1
        bbox = draw.textbbox((text_x_pos_scaled, current_y_scaled_for_bbox), line1_text, font=font_normal_hr)
        text_min_x = min(text_min_x, bbox[0])
        text_min_y = min(text_min_y, bbox[1])
        text_max_x = max(text_max_x, bbox[2])
        text_max_y = max(text_max_y, bbox[3])
        current_y_scaled_for_bbox += (bbox[3]-bbox[1]) + (SEPARACION_1_2 * SCALE_FACTOR)

        # Nombre Linea 1
        bbox = draw.textbbox((text_x_pos_scaled, current_y_scaled_for_bbox), name_line1_str, font=font_bold_hr)
        text_min_x = min(text_min_x, bbox[0])
        text_min_y = min(text_min_y, bbox[1])
        text_max_x = max(text_max_x, bbox[2])
        text_max_y = max(text_max_y, bbox[3])
        current_y_scaled_for_bbox += (bbox[3]-bbox[1])
        
        if name_line2_str:
            current_y_scaled_for_bbox += (SEPARACION_2_3 * SCALE_FACTOR)
            bbox = draw.textbbox((text_x_pos_scaled, current_y_scaled_for_bbox), name_line2_str, font=font_bold_hr)
            text_min_x = min(text_min_x, bbox[0])
            text_min_y = min(text_min_y, bbox[1])
            text_max_x = max(text_max_x, bbox[2])
            text_max_y = max(text_max_y, bbox[3])
            current_y_scaled_for_bbox += (bbox[3]-bbox[1])

        current_y_scaled_for_bbox += (SEPARACION_FINAL * SCALE_FACTOR)
        bbox = draw.textbbox((text_x_pos_scaled, current_y_scaled_for_bbox), line3_text, font=font_normal_hr)
        text_min_x = min(text_min_x, bbox[0])
        text_min_y = min(text_min_y, bbox[1])
        text_max_x = max(text_max_x, bbox[2])
        text_max_y = max(text_max_y, bbox[3])

        text_bbox = (text_min_x, text_min_y, text_max_x, text_max_y)

        # Combine QR and Text bounding boxes
        final_bbox_min_x = min(qr_bbox[0], text_bbox[0])
        final_bbox_min_y = min(qr_bbox[1], text_bbox[1])
        final_bbox_max_x = max(qr_bbox[2], text_bbox[2])
        final_bbox_max_y = max(qr_bbox[3], text_bbox[3])

        final_combined_bbox = (final_bbox_min_x, final_bbox_min_y, final_bbox_max_x, final_bbox_max_y)

        # Crop the high_res_canvas using the final combined bounding box
        imagen_estampa_final_high_res = high_res_canvas.crop(final_combined_bbox)

        # Resize to final resolution
        imagen_estampa_final = imagen_estampa_final_high_res.resize(
            (imagen_estampa_final_high_res.width // SCALE_FACTOR,
             imagen_estampa_final_high_res.height // SCALE_FACTOR),
            resample=Image.LANCZOS
        )

        # Auto-crop para eliminar espacios blancos adicionales
        bbox_final = imagen_estampa_final.getbbox()
        if bbox_final:
            imagen_estampa_final = imagen_estampa_final.crop(bbox_final)

        return imagen_estampa_final
            

    def sign_file(self, input_pdf, output_pdf, reason, location, page_index, x_coord, y_coord, width):
        # Si están vacíos, poner un espacio para evitar null en la validación
        if not reason:
            reason = " "
        if not location:
            location = " "
        
        # Generar timestamp con compensación para sincronizar con el momento de la firma real
        # Agregamos tiempo para compensar el procesamiento (imagen, campos, firma, etc.)
        base_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone()
        # Compensación por el tiempo del proceso de firma (ajustable según rendimiento del sistema)
        time_offset_seconds = self.settings.get('timestamp_offset_seconds', 2)
        compensated_timestamp = base_timestamp + datetime.timedelta(seconds=time_offset_seconds)
        stamp_image = self.create_stamp_image(reason, location, compensated_timestamp)
        
        aspect_ratio = float(stamp_image.height) / float(stamp_image.width) if stamp_image.width > 0 else 1
        height = max(1, round(width * aspect_ratio))

        # Generar un nombre único para el campo de firma para permitir múltiples firmas
        unique_field_name = self._get_unique_field_name(input_pdf)

        # Usar el mismo timestamp para QR y firma (el timestamp se establece automáticamente durante la firma)
        metadata = PdfSignatureMetadata(
            field_name=unique_field_name, 
            reason=reason, 
            location=location
        )
        sig_field_spec = SigFieldSpec(
            sig_field_name=unique_field_name, 
            on_page=page_index, 
            box=(x_coord, y_coord, x_coord + width, y_coord + height)
        )
        
        pdf_stamp_image = PdfImage(stamp_image)
        stamp_style = TextStampStyle(background=pdf_stamp_image, stamp_text="", border_width=0, background_opacity=1.0)
        
        pdf_signer = PdfSigner(
            signature_meta=metadata,
            signer=self.signer,
            new_field_spec=sig_field_spec,
            stamp_style=stamp_style
        )
        
        try:
            with open(input_pdf, "rb") as infile, open(output_pdf, "wb") as outfile:
                # Usar strict=False para permitir firmas en PDFs que ya tienen firmas previas
                writer = IncrementalPdfFileWriter(infile, strict=False)
                
                # Control exacto del timestamp si está habilitado
                if self.settings.get('use_exact_timestamp_sync', False):
                    # Monkey patch datetime.now para usar el mismo timestamp del QR
                    original_now = datetime.datetime.now
                    def custom_now(tz=None):
                        return compensated_timestamp.astimezone(tz) if tz else compensated_timestamp
                    datetime.datetime.now = custom_now
                    try:
                        pdf_signer.sign_pdf(writer, output=outfile)
                    finally:
                        # Restaurar datetime.now original
                        datetime.datetime.now = original_now
                else:
                    # Usar timestamp automático (comportamiento normal)
                    pdf_signer.sign_pdf(writer, output=outfile)
            return True, f"¡Éxito! PDF firmado con QR guardado en:\n{output_pdf}"
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(f"Error detallado: {traceback_str}")
            # Agregar información más específica sobre errores relacionados con firmas existentes
            error_msg = str(e)
            if "signature field" in error_msg.lower() or "already exists" in error_msg.lower():
                return False, f"Error: El PDF podría tener restricciones de firma. Intente con un nombre de archivo diferente.\nDetalle: {error_msg}"
            return False, f"Error durante la firma: {type(e).__name__}: {e}"

    # NUEVO MÉTODO ASÍNCRONO
    async def async_sign_file(self, input_pdf, output_pdf, reason, location, page_index, x_coord, y_coord, width):
        if not reason: reason = " "
        if not location: location = " "
        
        stamp_image = self.create_stamp_image(reason, location)
        aspect_ratio = float(stamp_image.height) / float(stamp_image.width)
        height = round(width * aspect_ratio)
        unique_field_name = self._get_unique_field_name(input_pdf)

        pdf_signer = PdfSigner(
            signature_meta=PdfSignatureMetadata(field_name=unique_field_name, reason=reason, location=location),
            signer=self.signer,
            new_field_spec=SigFieldSpec(sig_field_name=unique_field_name, on_page=page_index, box=(x_coord, y_coord, x_coord + width, y_coord + height)),
            stamp_style=TextStampStyle(background=PdfImage(stamp_image), stamp_text="")
        )
        
        try:
            with open(input_pdf, "rb") as infile, open(output_pdf, "wb") as outfile:
                writer = IncrementalPdfFileWriter(infile, strict=False)
                # ¡LA LLAMADA CLAVE AHORA ES ASÍNCRONA!
                await pdf_signer.async_sign_pdf(writer, output=outfile)
            return True, f"¡Éxito! PDF firmado con QR guardado en:\n{output_pdf}"
        except Exception as e:
            return False, f"Error durante la firma: {e}"
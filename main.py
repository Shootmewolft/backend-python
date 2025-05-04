from flask import Flask, request, jsonify
from docx import Document
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from flask_cors import CORS
import boto3
import uuid

app = Flask(__name__)
CORS(app)  # Esto permite solicitudes desde cualquier origen

# Configuración de S3
S3_BUCKET = "amplify-d2yl9rekppsb0u-ma-amplifyd2yl9rekppsb0umaa-ufu1izf4ntdk"
S3_REGION = "us-east-1"  # ajusta según tu región
s3_client = boto3.client("s3")

# Utilidad para reemplazar texto en DOCX
def replace_text_in_docx(file_stream, replacements):
    document = Document(file_stream)
    for paragraph in document.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
    output_stream = BytesIO()
    document.save(output_stream)
    output_stream.seek(0)
    return output_stream

# Utilidad para reemplazar texto en PDF (solo texto plano, no es perfecto)
def replace_text_in_pdf(file_stream, replacements):
    reader = PdfReader(file_stream)
    writer = PdfWriter()

    for page in reader.pages:
        text = page.extract_text()
        for key, value in replacements.items():
            if key in text:
                text = text.replace(key, value)
        writer.add_page(page)  # No se puede reinsertar texto modificado directamente (requiere rediseño)

    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream

# Ruta principal
@app.route("/modify-document", methods=["POST"])
def modify_document():
    try:
        file = request.files.get("file")
        replacements = request.form.get("replacements")

        if not file or not replacements:
            return jsonify({"error": "Archivo y reemplazos son requeridos"}), 400

        replacements_dict = eval(replacements)  # ¡Usar json.loads(replacements) en producción!

        filename = file.filename
        extension = filename.rsplit(".", 1)[-1].lower()

        # Procesar documento
        if extension == "docx":
            modified_file = replace_text_in_docx(file.stream, replacements_dict)
        elif extension == "pdf":
            modified_file = replace_text_in_pdf(file.stream, replacements_dict)
        else:
            return jsonify({"error": "Tipo de archivo no soportado"}), 400

        # Subir a S3
        new_filename = f"modified_{uuid.uuid4()}.{extension}"
        s3_client.upload_fileobj(modified_file, S3_BUCKET, new_filename)

        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{new_filename}"

        return jsonify({"message": "Documento modificado y subido con éxito", "url": file_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

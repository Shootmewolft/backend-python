from flask import Flask, request, send_file, jsonify
from docx import Document
import os

app = Flask(__name__)

# Ruta para manejar el archivo y reemplazar los campos dinámicos
@app.route("/process-document", methods=["POST"])
def process_document():
    try:
        # Obtener el texto del documento procesado desde la petición
        file_text = request.json.get("file")
        replacements = request.json.get("replacements", {})

        if not file_text:
            return {"error": "No file provided"}, 400

        if not replacements:
            return {"error": "No replacement data provided"}, 400

        # Crear un nuevo documento
        doc = Document()
        doc.add_paragraph(file_text)  # Se crea un documento Word con el contenido procesado

        # Reemplazar las variables dinámicas con los valores proporcionados
        for key, value in replacements.items():
            for para in doc.paragraphs:
                para.text = para.text.replace(f"{{{{{key}}}}}", value)

        # Guardar el documento modificado
        output_path = "modified_document.docx"
        doc.save(output_path)

        # Devolver el archivo modificado
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)

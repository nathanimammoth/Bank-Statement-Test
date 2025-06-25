import io, zipfile
from flask import Flask, render_template, request, send_file
from bank_statements_processor import process_pdf

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    pdfs = request.files.getlist("pdfs")
    if not pdfs:
        return "No files", 400

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w') as zf:
        for f in pdfs:
            df = process_pdf(f.stream)
            zf.writestr(f.filename.replace('.pdf','.csv'),
                        df.to_csv(index=False))
    mem_zip.seek(0)
    return send_file(mem_zip,
                     mimetype="application/zip",
                     as_attachment=True,
                     download_name="results.zip")

if __name__ == "__main__":
    app.run(debug=True)
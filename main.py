from flask import Flask, request, jsonify, render_template
from kbbi import KBBI, TidakDitemukan

app = Flask(__name__)

with open("data/kbbi_edited.txt", "r") as f:
    data_lokal = f.read().splitlines()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cek_kata', methods=['POST'])
def cek_kata():
    kata = request.json.get('kata', '').strip()
    if not kata:
        return jsonify({"status": "error", "message": "Kata kosong"}), 400

    try:
        data = KBBI(kata)
    except TidakDitemukan as e:
        data = e
    except Exception as d:
        data = d
    
    if "ConnectionError" in str(data.__class__):
        if kata in data_lokal:
            definisi_html = f"""
            <div class='pelafalan-kata-dasar'>
                <div class='kata-dasar'>{kata}</div>
            </div>
            <div class='makna'></div>
            """

            return jsonify({"status": "valid", "definisi": definisi_html})

            return jsonify({
                "status": "valid",
                "message": f"Kata '{kata}' ditemukan secara offline (local dictionary)."
            })
        else:
            return jsonify({
                "status": "invalid",
                "message": f"Tidak ada internet dan kata '{kata}' tidak ditemukan di data lokal."
            })
        
    if "tidak ditemukan dalam KBBI." in str(data) :
        return jsonify({
            "status": "invalid",
            "message": f"Kata '{kata}' tidak ditemukan dalam KBBI."
        })

    mentah = data.serialisasi()
    entri = mentah["entri"][0]

    # Pelafalan & kata dasar
    pelafalan = entri.get("nama", kata)
    kata_dasar = entri.get("kata_dasar", [])
    kata_dasar_txt = "; ".join(kata_dasar) + " >> " if kata_dasar else ""

    # Format HTML untuk setiap makna
    makna_html = ""
    for i, makna in enumerate(entri["makna"], 1):
        kelas = " ".join(f"({item['kode']})" for item in makna.get("kelas", []))
        submakna = "; ".join(makna.get("submakna", []))
        contoh = "; ".join(makna.get("contoh", []))

        makna_html += "<div class='makna-item'>"
        if kelas:
            makna_html += f"<span class='kelas'>{kelas}</span> "
        if submakna:
            makna_html += f"<span class='submakna'>{submakna}: </span> "
        if contoh:
            makna_html += f"<span class='contoh'>— {contoh}</span>"
        makna_html += "</div>"

    definisi_html = f"""
    <div class='pelafalan-kata-dasar'>
        <div class='kata-dasar'>{kata_dasar_txt} {pelafalan}</div>
    </div>
    <div class='makna'>{makna_html}</div>
    """

    return jsonify({"status": "valid", "definisi": definisi_html})

if __name__ == '__main__':
    app.run(debug=True)

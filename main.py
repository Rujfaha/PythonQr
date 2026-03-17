from flask import Flask, request, send_file, render_template_string
import qrcode
import io
import base64

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>QR Generator</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --border: #ffffff12;
    --accent: #c8f04a;
    --accent2: #7b61ff;
    --text: #f0f0f0;
    --muted: #666680;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow-x: hidden;
  }

  /* background grid */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--border) 1px, transparent 1px),
      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
  }

  /* glow blob */
  body::after {
    content: '';
    position: fixed;
    width: 600px; height: 600px;
    background: radial-gradient(circle, #7b61ff22 0%, transparent 70%);
    top: -100px; left: 50%;
    transform: translateX(-50%);
    pointer-events: none;
    z-index: 0;
  }

  .container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 520px;
  }

  .header {
    margin-bottom: 2.5rem;
    animation: fadeUp 0.6s ease both;
  }

  .tag {
    display: inline-block;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid var(--accent);
    padding: 3px 10px;
    border-radius: 2px;
    margin-bottom: 1rem;
  }

  h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.03em;
  }

  h1 span { color: var(--accent); }

  .subtitle {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.6rem;
    letter-spacing: 0.05em;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    animation: fadeUp 0.6s 0.1s ease both;
  }

  .input-row {
    display: flex;
    gap: 0.75rem;
    align-items: stretch;
  }

  .input-wrap {
    flex: 1;
    position: relative;
  }

  .input-label {
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
    display: block;
  }

  input[type="text"] {
    width: 100%;
    background: #0a0a0f;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    padding: 0.75rem 1rem;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  input[type="text"]:focus {
    border-color: var(--accent2);
    box-shadow: 0 0 0 3px #7b61ff22;
  }

  input[type="text"]::placeholder { color: var(--muted); }

  .btn-generate {
    margin-top: 1.45rem;
    background: var(--accent);
    color: #0a0a0f;
    border: none;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    padding: 0.75rem 1.4rem;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
    white-space: nowrap;
  }

  .btn-generate:hover {
    background: #d8ff5a;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px #c8f04a44;
  }

  .btn-generate:active { transform: translateY(0); }

  /* result section */
  .result {
    margin-top: 1.5rem;
    display: none;
    animation: fadeUp 0.4s ease both;
  }

  .result.show { display: block; }

  .divider {
    border: none;
    border-top: 1px solid var(--border);
    margin-bottom: 1.5rem;
  }

  .qr-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.25rem;
  }

  .qr-frame {
    position: relative;
    padding: 1.25rem;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 0 40px #c8f04a22;
  }

  .qr-frame img {
    display: block;
    width: 220px;
    height: 220px;
    image-rendering: pixelated;
  }

  /* corner decorations */
  .qr-frame::before, .qr-frame::after {
    content: '';
    position: absolute;
    width: 18px; height: 18px;
    border-color: var(--accent);
    border-style: solid;
  }
  .qr-frame::before { top: -1px; left: -1px; border-width: 2px 0 0 2px; border-radius: 4px 0 0 0; }
  .qr-frame::after  { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; border-radius: 0 0 4px 0; }

  .qr-meta {
    text-align: center;
  }

  .qr-url {
    font-size: 0.7rem;
    color: var(--muted);
    word-break: break-all;
    max-width: 280px;
  }

  .qr-url span {
    color: var(--accent2);
  }

  .btn-download {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    padding: 0.6rem 1.2rem;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.2s, color 0.2s, transform 0.15s;
    margin-top: 0.25rem;
  }

  .btn-download:hover {
    background: var(--accent);
    color: #0a0a0f;
    transform: translateY(-1px);
  }

  /* loading spinner */
  .spinner {
    display: none;
    width: 20px; height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin: 1rem auto;
  }

  .spinner.show { display: block; }

  @keyframes spin { to { transform: rotate(360deg); } }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .footer {
    margin-top: 2rem;
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-align: center;
    animation: fadeUp 0.6s 0.2s ease both;
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="tag">// tool</div>
    <h1>QR<br/><span>GEN</span></h1>
    <p class="subtitle">paste a url. get a code. done.</p>
  </div>

  <div class="card">
    <div class="input-row">
      <div class="input-wrap">
        <label class="input-label" for="urlInput">URL or text</label>
        <input type="text" id="urlInput" placeholder="https://example.com" />
      </div>
      <button class="btn-generate" onclick="generate()">Generate</button>
    </div>

    <div class="spinner" id="spinner"></div>

    <div class="result" id="result">
      <hr class="divider"/>
      <div class="qr-wrap">
        <div class="qr-frame">
          <img id="qrImg" src="" alt="QR Code"/>
        </div>
        <div class="qr-meta">
          <div class="qr-url" id="qrUrl"></div>
        </div>
        <a class="btn-download" id="downloadBtn" download="qrcode.png">
          ↓ download png
        </a>
      </div>
    </div>
  </div>

  <div class="footer">press enter or click generate</div>
</div>

<script>
  document.getElementById('urlInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') generate();
  });

  async function generate() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return;

    const spinner = document.getElementById('spinner');
    const result  = document.getElementById('result');

    result.classList.remove('show');
    spinner.classList.add('show');

    const res  = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'url=' + encodeURIComponent(url)
    });

    const blob = await res.blob();
    const objUrl = URL.createObjectURL(blob);

    spinner.classList.remove('show');

    document.getElementById('qrImg').src = objUrl;
    document.getElementById('qrUrl').innerHTML = '<span>↗</span> ' + url;
    document.getElementById('downloadBtn').href = objUrl;

    result.classList.add('show');
  }
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/generate", methods=["POST"])
def generate():
    url = request.form["url"]
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
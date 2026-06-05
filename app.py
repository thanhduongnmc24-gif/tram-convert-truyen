import os
import tempfile
import requests
from flask import Flask, request, Response
from flask_cors import CORS
import mobi
from bs4 import BeautifulSoup
import shutil

app = Flask(__name__)
CORS(app)

@app.route('/convert', methods=['GET'])
def convert():
    file_id = request.args.get('fileId')
    api_key = request.args.get('apiKey')
    if not file_id or not api_key:
        return "Thiếu thông tin fileId hoặc apiKey", 400

    temp_path = None
    extract_dir = None
    try:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return "Không thể tải file từ Drive", 400

        fd, temp_path = tempfile.mkstemp(suffix='.mobi')
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)

        extract_dir, filepath = mobi.extract(temp_path)

        # [Suy luận] Quét toàn bộ thư mục giải nén để gom sạch file văn bản
        text_content = ""
        for root, dirs, files in os.walk(extract_dir):
            for file in sorted(files):
                if file.lower().endswith(('.html', '.htm', '.xhtml')):
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        text_content += soup.get_text(separator='\n') + "\n\n"

        if not text_content.strip():
            text_content = "Không tìm thấy nội dung chữ. File có thể là truyện tranh ảnh hoặc bị mã hóa phần cứng."

        return Response(text_content, mimetype='text/plain')

    except Exception as e:
        return f"Lỗi trạm trung chuyển: {str(e)}", 500

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

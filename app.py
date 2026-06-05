import os
import tempfile
import requests
from flask import Flask, request, Response
import mobi
from bs4 import BeautifulSoup
import shutil

app = Flask(__name__)

@app.route('/convert', methods=['GET'])
def convert():
    file_id = request.args.get('fileId')
    api_key = request.args.get('apiKey')
    if not file_id or not api_key:
        return "Thiếu thông tin fileId hoặc apiKey", 400

    temp_path = None
    extract_dir = None
    try:
        # 1. Tèo chạy đi lấy file từ Drive về
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return "Không thể tải file từ Drive", 400

        # 2. Lưu tạm vào ổ cứng máy chủ
        fd, temp_path = tempfile.mkstemp(suffix='.mobi')
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)

        # 3. Dùng búa đập vỡ lớp vỏ .mobi / .azw3
        extract_dir, filepath = mobi.extract(temp_path)

        # 4. Lọc lấy phần lõi chữ thuần túy
        text_content = ""
        if filepath.endswith('.html') or filepath.endswith('.htm'):
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                text_content = soup.get_text(separator='\n')
        else:
            text_content = "Định dạng giải nén không hỗ trợ hiển thị chữ."

        return Response(text_content, mimetype='text/plain')

    except Exception as e:
        return f"Lỗi trạm trung chuyển: {str(e)}", 500

    finally:
        # 5. Dọn dẹp rác sạch sẽ để trạm không bị đầy bộ nhớ
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# 1. Bắt đầu từ ảnh Python 3.10
FROM python:3.10-slim

# 2. CÀI ĐẶT CÁC CÔNG CỤ HỆ THỐNG
#    build-essential: Trình biên dịch C/C++ (để compile PyAudio)
#    portaudio19-dev: Thư viện cho PyAudio (cho micro)
RUN apt-get update && apt-get install -y build-essential portaudio19-dev git

# 3. Thiết lập thư mục làm việc
WORKDIR /app

# 4. Sao chép file requirements
#    (Docker sẽ cache bước này nếu file không đổi)
COPY requirements.txt .

# 5. Cài đặt thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Sao chép toàn bộ code dự án
COPY . .

# 7. Mở cổng Streamlit
EXPOSE 8501

# 8. Lệnh chạy
CMD ["streamlit", "run", "app.py"]
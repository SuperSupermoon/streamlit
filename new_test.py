from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json

# Google API 클라이언트 설정 파일 경로
gauth = GoogleAuth()

# 사용자 인증
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

# 업로드할 JSON 데이터
data = {
    "key": "value",
    "name": "John"
}

# JSON 파일로 저장
with open("sample.json", "w") as f:
    json.dump(data, f)

# Google Drive에 파일 업로드
upload_file = drive.CreateFile({'title': 'sample.json'})
upload_file.SetContentFile('sample.json')
upload_file.Upload()

print('업로드 완료, 파일 ID:', upload_file['id'])

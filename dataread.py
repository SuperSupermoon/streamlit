import streamlit as st
import pandas as pd
import io
from collections import defaultdict
import re
import json
import nltk

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# 서비스 계정 키 JSON 파일 경로
SERVICE_ACCOUNT_FILE = {
  "type": "service_account",
  "project_id": "app-open-397403",
  "private_key_id": "b73248497df422c5e6497307d7cbdd0b191f5990",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCei28+sI0hMo7c\n75H47YBhdsx2QVexSeTRq0mS7s6Ka03AqcTDz4CWw7T2r9lvGXtrrqGpLer/qtN9\nFCH1MC+PwDrV9uzFQ4oakF42vXsc/DKEAGBU6FWf9K541O4KkFgr6NaUFOhCGpCR\nsdBG2+3bDThKHiYoVwCCMFjFD7hpsgDl0ZNhIDd11zlmN99Qjmkovou8Euw0Bv21\ndHsuIHalrIxGVOEK99xAYG5A9ZxcAxICQMGVHhCq2XybE5Mht1XMHp5MIYOraseI\nX1rwAl+di4sNHspLcBrEKaBbBwPx69iKl8YFR5QQiGNJA95kRnHlr55ja9/wMwew\n4I6DMKLFAgMBAAECggEAIWWrWygLLp9ND1bK58Y16TICe3WjwJWZhR5BGxnBedCF\nOiy45WuIQZn7vIxJ7/iM8l/Ar5fb3RvxvXMYfSL3nd8nNau0cBBcXuCi7AKJlM8+\nX+aJZFFluhJrj0oBU8nYvPUpAFwQGd6pLfuoLUkGR4K3JQvJS22aTpJbHLXFScQv\nwet92GCiNVz2BgStFLiL6yG68yShrGoXkmfQPMXIi6N6gqE1SIb0XXWE04loJSIO\nkRGMPvTYLjZliNr7LZB9n7twn6Ehe/5WCskkaf6BmFZs7IKEg6LN0FNbQwF4EIV0\nLLq/XmSDbBDHC3SJGy365yeM0C/QOuw5LKJgX6hhWQKBgQDKgGtzke/7blWmI0Wc\nirLv06YEW+qBkHCoNChmKujvb5mW0EMwxsVQLGk5N82BK7VxHuCVtQ9SUJ5y/r87\n+UQTEPcloCeFpNJ0jPi7Cndssc36Iv7lScYKc7b7gilXO3hBCetve40kqk9rxGsx\nyMTLiEG62lIpZpgeumlfgkranQKBgQDIbh59YhPuPRp+Oo5mvYBDqxk9wUUCeUZi\nGwRe/a5lfuKlKkSOMVMpsQcukCCISiUNHIGwGJ02SFgER4F60j8yIV7O8LaUTSXS\nKopENtb2X3UOM5Awn+7q1JicSFKwRMTrs473ueu6SCVH3QU37msRGF5tulTfnwwO\nmrqlNHG8SQKBgGRr0t15Hb1eNfMxwq+iyKHOH6JBwsWFz5haZT5lQSab/Vqg5PEn\nYWok2/mYBr1r44q5eT5Ej9iOSkVUt5kSQAQEgcuS5IaN+h/6WM7Infi1JCRLfoRO\nVXuRbsjC/6VWxIfcV3jtmEz6eHBE87O4kH8ujwoOgngtfHqgjujiQCSxAoGAfz7i\nHooQyzSByFfWpkVy1AMhMEKuVEa4N3qdiM0XVhp7O46dHYUVHifkvlwEO2KPKUbK\n0widbqP5NSZMfrRSKLpk3Y6W64obE9WsGGiUiq/Jue1kgmpXHUFBbh7AWGYget9x\nSbcAgDBjcr9QG9VCpgTJlnIwhhQMbI0xJ8cm2fkCgYA5K/b6/sLX6qUqcF38Rr15\nDcr8Gxqz/Zx4mMJNnAG4U6cuozmV3Z+wtF82QFnSaiibPH1cNo7+7W3MH7JN5ZyR\nWKl67J5kef/Pyo0GYH0PcWP5ZJ39LeApAesePz7t7seq+oKXGlPnXn6nLTY0++En\nk5b8RL/l6uo5p6EVb5csOA==\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit@app-open-397403.iam.gserviceaccount.com",
  "client_id": "114410097368575921127",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit%40app-open-397403.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

SCOPES = ['https://www.googleapis.com/auth/drive']

# 정규표현식 미리 컴파일
QUOTE_REGEX = re.compile(r'^["\']|["\']$|^["\'],|["\'],$')

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Drive 정보 가져오기
drive_info = drive_service.about().get(fields='storageQuota').execute()


def adjust_key(k, reference_dict):
    # Attempt to find a matching key in reference_dict that starts with 'rel.'
    matching_key = next((key for key in reference_dict.keys() if key.endswith('.' + k)), None)
    
    if matching_key:
        # If a matching key is found, modify k to match the format of the key in reference_dict            
        return matching_key.replace('.', ': ').split(': ')
    return [k]


def create_folder(folder_name, parent_folder_id=None):
    query = f"name='{folder_name}'"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"
        
    results = drive_service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()

    # print("results", results)
    
    items = results.get('files', [])
    
    # print("items", items)
    
    # 폴더가 이미 존재하는 경우
    if len(items) > 0:
        return items[0]['id']
    
    # 새 폴더를 생성
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # print("folder_name", folder_name)
    
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]
        
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    
    # print("folder['id']", folder['id'])
    
    return folder['id']


def find_top_folder(service):
    results = service.files().list(
        q=f"name='{st.session_state.reviewer_name}' and mimeType='application/vnd.google-apps.folder'",
        pageSize=10,
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    
    # print("root folder path:", items)
    
    if items:
        return items[0]['id']
    else:
        return None

# Google Drive에 파일 업로드
def upload_to_drive(filename, filedata, folder_id=None):
    file_metadata = {'name': filename}
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    # Convert DataFrame to CSV string and then to BytesIO object
    csv_buffer = io.BytesIO()
    filedata.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    media = MediaIoBaseUpload(csv_buffer, mimetype='text/csv', resumable=True)
        
    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, parents'
    )
    file = request.execute()

    # 파일의 ID와 부모 폴더 정보를 출력합니다.
    print(f"Uploaded file with name {file.get('name')}, ID {file.get('id')} to parent(s) {file.get('parents')}")


def load_csv_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    csv_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(csv_buffer, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()
    
    csv_buffer.seek(0)
    df = pd.read_csv(csv_buffer)
    return df



# when Gdrive.
def load_feedback(patient_id, display_names, service, folder_id):
    if folder_id is not None:
        results = service.files().list(
            q=f"'{folder_id}' in parents and name='{patient_id}' and mimeType='application/vnd.google-apps.folder'",
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()

        items = results.get('files', [])
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                subfolder_id = item['id']
                subfolder_results = service.files().list(
                    q=f"'{subfolder_id}' in parents and name='{display_names}.csv'",
                    pageSize=10,
                    fields="files(id, name)"
                ).execute()
                
                subfolder_items = subfolder_results.get('files', [])
                if subfolder_items:
                    csv_file_id = subfolder_items[0]['id']
                    feedback_data = load_csv_from_drive(service, csv_file_id)
                    return feedback_data

    return None


def save_feedback(jsonfile, input_feedback, current_section, section_texts, display_names, feedback_data=None):
    # 기존 데이터 불러오기
    top_folder_id = find_top_folder(drive_service)
    existing_feedback = load_feedback(jsonfile['subject'], display_names, drive_service, top_folder_id)

    # 기존 데이터에 새로운 피드백 추가
    if existing_feedback is not None:
        # 현재 섹션의 기존 피드백 찾기
        existing_section_feedback = existing_feedback[existing_feedback['section'] == current_section]

        # 기존 피드백이 있는 경우, 해당 피드백 삭제
        if not existing_section_feedback.empty:
            existing_feedback = existing_feedback[existing_feedback['section'] != current_section]

        input_feedback['subject_id'] = jsonfile['subject']
        input_feedback['study_id'] = jsonfile['study']
        input_feedback['sequence'] = jsonfile['sequence']
        input_feedback['section'] = current_section    
        input_feedback['report'] = section_texts

        # 새로운 피드백 추가
        feedback_data = pd.concat([existing_feedback, input_feedback], ignore_index=True)
    else:
        feedback_data = input_feedback.copy()
        feedback_data['subject_id'] = jsonfile['subject']
        feedback_data['study_id'] = jsonfile['study']
        feedback_data['sequence'] = jsonfile['sequence']
        feedback_data['section'] = current_section    
        feedback_data['report'] = section_texts

    # print("st.session_state.reviewer_name", st.session_state.reviewer_name)
    # 폴더 생성 및 데이터 저장
    
    reviewer_folder_id = create_folder(st.session_state.reviewer_name)
    patient_folder_id = create_folder(jsonfile['subject'], reviewer_folder_id)
    upload_to_drive(f"{display_names}.csv", feedback_data, patient_folder_id)
    # return patient_folder_id, feedback_data


def del_files(service, folder_id, indent=0):
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])
    
    
    if not items:
        print('No files found.')
    else:
        for item in items:
            # Delete the folder
            print(f"Deleting folder: {item['name']} ({item['id']})")
            drive_service.files().delete(fileId=item['id']).execute()


@st.cache_data
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Failed to parse JSON file: {filepath}")
        return {}
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
        return {}


# Simplified sentence tokenizer
@st.cache_data
def custom_sent_tokenize(text):
    sentences = text.split('. ')
    sentences = [s + '.' if s != sentences[-1] else s for s in sentences]

    return sentences

# Helper function to tokenize sentences from annotations
@st.cache_data
def tokenize_annotations(annotations):
    return [sent for anno in annotations for sent in sent_tokenize(anno)]

@st.cache_data
def get_statistics(data, dfs):
    present_sections = {key: True for key, value in data.items() if value and key in ["History", "Findings", "Impression"]}
    sent_stats, cat_stats, missing_sents = {}, {}, {}
    norm_ent_stats = defaultdict(recursive_defaultdict)
    
    for sec, df in dfs.items():
        section_texts = data.get({'HIST': 'History', 'FIND': 'Findings', 'IMPR': 'Impression'}[sec], "")
        section_sents = custom_sent_tokenize(section_texts)
                    
        if 'sent' in df.columns:
            sent_counts = df['sent'].value_counts().to_dict()
            sent_stats[sec] = sent_counts
            
            sents_from_annos = set(df['sent'])
            sents_from_annos_tokenized = set(tokenize_annotations(sents_from_annos))
            missing_sents_for_section = [sent for sent in section_sents if sent not in sents_from_annos_tokenized]
            if missing_sents_for_section:
                missing_sents[sec] = missing_sents_for_section
        elif section_sents:
            missing_sents[sec] = section_sents

    return present_sections, sent_stats, cat_stats, norm_ent_stats, missing_sents


def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

def remove_quotes_with_re(text):
    return QUOTE_REGEX.sub('', text)

            
def extract_key_values(d):
    output_dict1, output_dict2 = {}, {}
    stack = [(d, '', '')]
    
    while stack:
        current_dict, parent_key1, parent_key2 = stack.pop()
        for key, value in current_dict.items():
            new_key1 = f"{parent_key1}.{key}" if parent_key1 else key
            new_key2 = f"{key}" if parent_key2 else key
            if isinstance(value, dict):
                stack.append((value, new_key1, new_key2))
            else:
                output_dict1[new_key1] = value
                output_dict2[new_key2] = value
    
    return output_dict1, output_dict2

def find_and_map_values_by_index(key_to_find, output_dict1, output_dict2):
    keys_output_dict2 = list(output_dict2.keys())
    keys_output_dict1 = list(output_dict1.keys())
    
    try:
        index_to_find = keys_output_dict2.index(key_to_find)
        return keys_output_dict1[index_to_find]
    except ValueError:
        return None


def parse_input_to_dict(input_data):
    if isinstance(input_data, str):
        clean_str = re.sub(r"[}\]\n]", "", input_data)
        return dict(re.findall(r"(\w+):\s*([^,]*)(?:,|$)", clean_str))
    elif isinstance(input_data, list) and len(input_data) == 2:
        return {input_data[0].strip(): input_data[1].strip()}
    st.warning(f"Unexpected input format: {input_data}")
    return {}
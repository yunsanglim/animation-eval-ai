import streamlit as st
import google.generativeai as genai
from notion_client import Client
from pypdf import PdfReader
import io

# 1. 보안 설정 (배포 시 Streamlit Secrets 칸에 키를 입력해야 작동합니다)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    NOTION_DB_ID = st.secrets["NOTION_DB_ID"]
except KeyError:
    st.error("보안 설정(Secrets)이 완료되지 않았습니다. 관리자 설정을 확인하세요.")
    st.stop()

# API 연결 설정
genai.configure(api_key=GOOGLE_API_KEY)
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="AI 애니메이션 과제 평가 시스템", layout="wide")

st.title("🎬 AI 루브릭 기반 애니메이션 평가 시스템")
st.markdown("---")
st.sidebar.header("📁 과제 업로드")

# 2. PDF 텍스트 추출 함수
def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text

# 3. Opal(Gemini) 분석 함수
def analyze_with_opal(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    당신은 애니메이션 전공 교수입니다. 다음 과제 내용을 분석하여 루브릭에 따라 평가하세요.
    [과제 내용]:
    {text}
    [지시사항]: 
    1. 시놉시스의 장르를 판별하세요. 
    2. 이야기 구조, 갈등 전개, 장면 구성, 형식 준수, 시간배분 타당성에 대해 100점 만점으로 정량 평가하세요.
    3. 종합적인 교수 피드백을 한 줄로 작성하세요.
    """
    response = model.generate_content(prompt)
    return response.text

# 4. 파일 업로드 및 평가 로직
uploaded_files = st.sidebar.file_uploader("학생 과제 PDF를 선택하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        with st.expander(f"👤 학생 과제: {file.name}"):
            if st.button(f"{file.name} 분석 시작", key=f"btn_{file.name}"):
                with st.spinner('Opal AI가 분석 중입니다...'):
                    raw_text = extract_text_from_pdf(file)
                    st.session_state[f"res_{file.name}"] = analyze_with_opal(raw_text)
            
            if f"res_{file.name}" in st.session_state:
                st.write("**AI 분석 제안:**")
                st.info(st.session_state[f"res_{file.name}"])
                
                # 교수님 슬라이드 평가 영역
                st.markdown("### ✍️ 교수님 최종 평가 (슬라이드 바)")
                col1, col2 = st.columns(2)
                with col1:
                    genre = st.text_input("장르 확인", key=f"g_{file.name}")
                    s1 = st.slider("시놉_주제적합성", 0, 100, 80, key=f"s1_{file.name}")
                    s2 = st.slider("시놉_인물설정", 0, 100, 80, key=f"s2_{file.name}")
                with col2:
                    v1 = st.slider("스토_완성도", 0, 100, 80, key=f"v1_{file.name}")
                    v2 = st.slider("스토_연출의도", 0, 100, 80, key=f"v2_{file.name}")
                
                feedback = st.text_area("최종 한 줄 피드백", key=f"fb_{file.name}")
                
                if st.button("🚀 노션 데이터베이스로 전송", key=f"save_{file.name}"):
                    try:
                        notion.pages.create(
                            parent={"database_id": NOTION_DB_ID},
                            properties={
                                "이름": {"title": [{"text": {"content": file.name.split('.')[0]}}]},
                                "장르": {"select": {"name": genre if genre else "미분류"}},
                                "시놉_주제적합성": {"number": s1},
                                "시놉_인물설정": {"number": s2},
                                "스토_완성도": {"number": v1},
                                "스토_연출의도": {"number": v2},
                                "종합 피드백": {"rich_text": [{"text": {"content": feedback}}]}
                            }
                        )
                        st.success("노션 전송 완료!")
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

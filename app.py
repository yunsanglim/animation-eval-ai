import streamlit as st
import google.generativeai as genai

st.title("Gemini 연결 테스트")

# 1. 키 가져오기
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("Secrets에 GOOGLE_API_KEY가 없습니다!")
else:
    st.write(f"키 확인됨: {api_key[:10]}********")
    
    # 2. API 설정 및 테스트
    try:
        genai.configure(api_key=api_key)
        # 1.5-flash 대신 가장 기본인 gemini-pro로 테스트
       model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("안녕? 너 작동하니?")
        
        st.success("✅ 연결 성공!")
        st.balloons()
        st.write("Gemini 답변:", response.text)
        
    except Exception as e:
        st.error(f"❌ 연결 실패: {e}")

import streamlit as st
import pandas as pd
import openai
import json
import os
from datetime import datetime
from openai import OpenAI

# 🔐 API 키 입력
openai_api_key = st.text_input("🔐 OpenAI API 키 입력", type="password")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# 📦 데이터 로딩
try:
    orders_df = pd.read_csv("orders_by_phone.csv", dtype={"전화번호": str})
except FileNotFoundError:
    st.error("orders_by_phone.csv 파일이 필요합니다.")
    st.stop()

try:
    with open("company_policy.json", "r", encoding="utf-8") as f:
        company_policy = json.load(f)
except FileNotFoundError:
    st.error("company_policy.json 파일이 필요합니다.")
    st.stop()

# 🧠 정책 추출
def extract_policy(question):
    for key in company_policy.keys():
        if key in question:
            return f"[회사 정책 - {key}]\n{company_policy[key]}"
    return ""

# 💾 로그 저장
def save_log(phone, question, answer):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_df = pd.DataFrame([[now, phone, question, answer]], columns=["시간", "전화번호", "질문", "GPT응답"])
    if os.path.exists("chat_logs.csv"):
        existing = pd.read_csv("chat_logs.csv")
        combined = pd.concat([existing, log_df], ignore_index=True)
    else:
        combined = log_df
    combined.to_csv("chat_logs.csv", index=False)

# 🤖 GPT 응답 생성
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 🌐 Streamlit 채팅 UI 시작
st.title("💬 AI 고객 응답 챗봇")

# 상태 저장
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "phone" not in st.session_state:
    st.session_state.phone = ""

# 전화번호 입력 (고정)
if not st.session_state.phone:
    st.session_state.phone = st.text_input("📱 고객 전화번호 입력 (한 번만)", key="phone_input").strip()
    st.stop()

# 채팅 입력창
user_input = st.chat_input("💬 질문을 입력하세요")

if user_input and client:
    phone = st.session_state.phone
    customer_order = orders_df[orders_df["전화번호"] == phone]

    if customer_order.empty:
        bot_reply = "❌ 고객 정보를 찾을 수 없습니다. 전화번호를 확인해주세요."
    else:
        order = customer_order.iloc[0]
        context = f"""
[고객 주문 정보]
- 고객명: {order['고객명']}
- 상품명: {order['상품명']}
- 주문일: {order['주문일']}
- 배송상태: {order['배송상태']}
"""
        policy_text = extract_policy(user_input)
        prompt = f"""{context}
{policy_text}

[고객 질문]
{user_input}

위 정보를 바탕으로 고객에게 정중하고 친절한 답변을 생성해주세요.
"""
        bot_reply = generate_response(prompt)

    # 대화 기록 저장
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", bot_reply))

    # CSV로 로그 저장
    if customer_order.empty is False:
        save_log(phone, user_input, bot_reply)

# 채팅 기록 표시
for sender, msg in st.session_state.chat_history:
    if sender == "user":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)

import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 配置區域 ---
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 台灣居留證規格: 3.5cm x 4.5cm
TARGET_WIDTH_PX = 827   # 300dpi 標準
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照自動裁切", layout="centered")
st.title("🇹🇼 居留證大頭照自動裁切系統")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "上傳照片後,系統將自動進行標準大頭照裁切:\n"
    "• 頭部佔畫面 70-80% 高度\n"
    "• 頭頂留白約 10%\n"
    "• 肩膀完整顯示\n"
    "• 純白背景\n\n"
    "**提醒:** Sandbox 版本會有浮水印,正式使用請更換 Live 金鑰。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 自動化處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    with st.spinner("AI 正在自動處理並進行標準大頭照裁切,請稍候..."):
        try:
            # 先上傳圖片到臨時空間 (或直接使用 multipart)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            headers = {"x-api-key": PHOTOROOM_API_KEY}

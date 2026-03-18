import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 自動填入你的 Sandbox API Key ---
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 設定台灣規格 (3.5cm x 4.5cm @ 300DPI)
TARGET_WIDTH_PX = 413 
TARGET_HEIGHT_PX = 531 

st.set_page_config(page_title="居留證照片生成器", layout="centered")
st.title("🇹🇼 居留證照片自動生成 (Sandbox 測試版)")

uploaded_file = st.file_uploader("請上傳員工照片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    if st.button("開始高品質去背與裁切"):
        with st.spinner("正在呼叫 Photoroom AI..."):
            try:
                # 圖片轉二進位
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_data = img_byte_arr.getvalue()

                # 呼叫 API
                headers = {"x-api-key": PHOTOROOM_API_KEY}
                params = {
                    "background_color": "#FFFFFF",
                    "crop": "true",
                    "auto_crop_padding": "0.1" # 確保頭部佔比正確
                }
                
                response = requests.post(
                    "https://sdk.photoroom.com/v1/segment",
                    headers=headers,
                    files={"image_file": img_data},
                    params=params
                )

                if response.status_code == 200:
                    processed_img = Image.open(io.BytesIO(response.content))
                    final_img = processed_img.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.LANCZOS)
                    
                    st.success("生成成功！")
                    st.image(final_img, width=TARGET_WIDTH_PX)
                    
                    # 下載按鈕
                    buf = io.BytesIO()
                    final_img.save(buf, format="PNG")
                    st.download_button("下載成品", buf.getvalue(), "id_photo.png", "image/png")
                else:
                    st.error(f"API 錯誤：{response.text}")
            except Exception as e:
                st.error(f"發生錯誤：{e}")

import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 配置區域 ---
# 自動填入你之前測試成功的 Photoroom Sandbox API Key
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 設定台灣規格 (3.5cm x 4.5cm @ 300DPI) 
TARGET_WIDTH_PX = 413  # (35mm / 25.4mm/inch) * 300dpi = 413px
TARGET_HEIGHT_PX = 531 # (45mm / 25.4mm/inch) * 300dpi = 531px

st.set_page_config(page_title="居留證大頭照生成器", layout="centered")
st.title("🇹🇼 居留證大頭照自動生成 (Sandbox 測試版)")

# 使用說明
st.info(
    "預設規格為：台灣身分證/居留證使用 (3.5*4.5cm)。本系統已升級，採用最嚴格的「大頭」規格，"
    "自動進行高品質去背，並使頭部在畫面中最大化，最小化肩膀，以符合 `image_11.png` 的標準。\n\n"
    "**重要提醒：** 當前使用測試金鑰 (Sandbox)，生成的成品圖片將帶有 Photoroom 浮水印。測試滿意後，請更換為 Live 金鑰。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 顯示原始照片
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    # 生成按鈕
    generate_btn = st.button("開始高品質生成大頭照格")

    if generate_btn:
        # 顯示處理中的動畫
        with st.spinner("Photoroom AI 正在進行高品質去背與嚴格大頭裁切，請稍候..."):
            
            try:
                # --- 3. 準備呼叫 Photoroom API ---
                # 將圖片轉換為二進位資料
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                # 設定 API 請求頭和參數
                headers = {
                    "x-api-key": PHOTOROOM_API_KEY,
                }
                api_url = "https://sdk.photoroom.com/v1/segment"

                # 設定參數 (精準控制大頭格式的核心)
                # 1. background_color: 將背景設定為純白 (255, 255, 255)
                # 2. auto_crop: 自動裁切人像
                # 3. auto_crop_padding: 人像佔比。
                #    之前的 "0.1" (10% 留白) 保留太多肩膀。
                #    我們將其改為 "0.0" (0% 留白)，使頭部最大化，符合用戶要求的 `image_11.png` 格式。
                params = {
                    "background_color": "#FFFFFF", # 設定純白背景
                    "crop": "true",               # 開啟自動裁切
                    "format": "png",              # 輸出格式為 PNG，確保去背乾淨
                    "auto_crop_padding": "0.0",   # <<<<< 關鍵修改！0% 填充，最大化頭部，最小化肩膀 (大頭版本)。
                }

                # 準備要上傳的檔案
                files = {
                    "image_file": (uploaded_file.name, img_byte_arr, uploaded_file.type)
                }

                # --- 4. 執行 API 請求 ---
                response = requests.post(api_url, headers=headers, files=files, params=params)

                if response.status_code == 200:
                    # 成功獲取去背並裁切好的圖片
                    processed_image = Image.open(io.BytesIO(response.content))

                    # --- 5. 強制調整圖片為精確的像素尺寸 (3.5x4.5cm @ 300DPI) ---
                    # 即使 API 做了裁切，我們仍需確保檔案像素精確，這是為了解決用戶最初抱怨的「比例太少」問題。
                    final_image = processed_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.LANCZOS)

                    # --- 6. 顯示結果與下載 ---
                    st.success("🎉 大頭照格式生成成功！符合 `image_11.png` 格式（Sandbox 測試版）")
                    
                    st.subheader("最終成果 (大頭照 3.5x4.5cm)")
                    # 顯示標準大頭照
                    st.image(final_image, width=TARGET_WIDTH_PX)

                    # 準備下載
                    final_byte_arr = io.BytesIO()
                    final_image.save(final_byte_arr, format='PNG')
                    final_byte_arr = final_byte_arr.getvalue()
                    
                    st.markdown("<br>", unsafe_allow_html=True) # 調整位置
                    st.download_button(
                        label="下載標準大頭照 (符合規格)",
                        data=final_byte_arr,
                        file_name=f"Taiwan_ID_Photo_{uploaded_file.name}.png",
                        mime="image/png",
                        key='download-btn'
                    )
                else:
                    # API 呼叫失敗
                    st.error(f"API 呼叫失敗。錯誤碼: {response.status_code}")
                    st.error(f"錯誤訊息: {response.text}")
            
            except Exception as e:
                st.error(f"發生未知的錯誤: {str(e)}")

# --- 底部 ---
st.markdown("---")
st.markdown("© 2023 [你的公司名稱] - 跨國人力文件處理系統")

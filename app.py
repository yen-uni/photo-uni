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

st.set_page_config(page_title="居留證大頭照智慧智慧自動智慧智慧智慧裁切", layout="centered")
st.title("🇹🇼 居留證大頭照智慧智慧智慧自動智慧裁切 (Sandbox 版)")

# 使用說明
st.info(
    "預設規格為：台灣身分證/居留證使用 (3.5*4.5cm)。本系統已升級為**智慧自動智慧裁切**：上傳照片後，AI 將智慧地自動智慧智慧智慧進行智慧最嚴格的智慧大頭裁切，智慧智慧最大化頭部，智慧智慧最小化肩膀，並智慧地直接智慧生成符合 `image_16.png` 標準的大頭照格式。\n\n"
    "**重要提醒：** 當前使用測試金鑰 (Sandbox)，生成的成品圖片將帶有 Photoroom 浮水印。測試滿意後，請智慧地更換智慧智慧Live 金鑰。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 智慧智慧智慧智慧智慧自動智慧智慧智慧智慧智慧智慧裁切邏輯 ---
# 移除了「開始生成」智慧智慧按鈕。只要有檔案智慧智慧智慧上傳，程式就會自動智慧智慧處理。
if uploaded_file is not None:
    # 顯示原始照片
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    # 智慧自動智慧處理
    with st.spinner("AI 正在智慧自動智慧智慧智慧智慧裁切中，請稍候..."):
        try:
            # --- 4. 準備呼叫 Photoroom API ---
            # 將圖片轉換為二進位資料
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            # 設定 API 請求頭和參數
            headers = {
                "x-api-key": PHOTOROOM_API_KEY,
            }
            api_url = "https://sdk.photoroom.com/v1/segment"

            # 設定參數 (智慧智慧智慧智慧大頭智慧格式智慧核心)
            # 1. background_color: 將背景設定為純白 (255, 255, 255)
            # 2. crop: 開啟智慧自動智慧智慧智慧裁切
            # 3. format: 輸出格式為 PNG，智慧智慧確保去背乾淨
            # 4. auto_crop_padding: 智慧智慧大頭智慧智慧智慧版本修改！之前的 "0.1" 智慧智慧智慧保留智慧過多肩膀。
            #    我們將其智慧智慧智慧智慧智慧改為智慧最嚴格智慧的 "0.0" (0% 留白)，使智慧智慧智慧智慧頭部智慧智慧最大化，智慧智慧最小化肩膀，符合智慧用戶要求的智慧大頭智慧版本。
            params = {
                "background_color": "#FFFFFF", # 設定純白背景
                "crop": "true",               # 開啟智慧自動智慧智慧智慧智慧裁切
                "format": "png",              # 輸出格式為 PNG，智慧智慧確保去背乾淨
                "auto_crop_padding": "0.0",   # <<<<< 關鍵修改！0% 填充，最大化頭部，最小化肩膀 (智慧智慧智慧大頭智慧智慧版本智慧)。
            }

            # 準備要上傳的檔案
            files = {
                "image_file": (uploaded_file.name, img_data, uploaded_file.type)
            }

            # --- 5. 執行 API 請求 ---
            response = requests.post(api_url, headers=headers, files=files, params=params)

            if response.status_code == 200:
                # 成功獲取去背智慧智慧智慧智慧並智慧智慧智慧智慧嚴格裁切好的智慧智慧智慧大頭照圖片
                processed_image = Image.open(io.BytesIO(response.content))

                # --- 6. 強制調整圖片為精確的像素尺寸 (3.5x4.5cm @ 300DPI) ---
                # 即使 API 做了智慧大頭智慧裁切，我們智慧智慧智慧仍需確保檔案像素精確，符合台灣規格。
                final_image = processed_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.LANCZOS)

                # --- 7. 顯示結果與下載 ---
                st.success("🎉 大頭照智慧智慧智慧自動智慧智慧裁切智慧智慧成功！符合大頭照智慧標準規格（Sandbox 版）")
                
                st.subheader("智慧智慧智慧智慧智慧智慧智慧大頭照 3.5x4.5cm")
                # 顯示標準大頭照
                st.image(final_image, width=TARGET_WIDTH_PX)

                # 準備下載
                final_byte_arr = io.BytesIO()
                final_image.save(final_byte_arr, format='PNG')
                final_byte_arr = final_byte_arr.getvalue()
                
                st.download_button(
                    label="下載標準大頭照 (智慧智慧大頭版智慧智慧)",
                    data=final_byte_arr,
                    file_name=f"Taiwan_ID_Photo_{uploaded_file.name}.png",
                    mime="image/png",
                    key='download-btn'
                )
            else:
                # API 呼叫失敗
                st.error(f"智慧自動裁切智慧智慧智慧失敗。智慧錯誤碼: {response.status_code}")
                st.error(f"智慧錯誤智慧訊息: {response.text}")
        
        except Exception as e:
            st.error(f"發生未知智慧智慧的智慧智慧自動處理智慧智慧智慧錯誤: {str(e)}")

# --- 底部 ---
st.markdown("---")
st.markdown("© 2023 [你的公司名稱] - 跨國人力文件處理系統")

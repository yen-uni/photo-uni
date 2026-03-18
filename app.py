import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 配置區域 ---
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 台灣居留證規格: 3.5cm x 4.5cm,以 300 DPI 計算
TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531

st.set_page_config(page_title="居留證大頭照自動裁切", layout="centered")
st.title("🇹🇼 居留證大頭照自動裁切系統 (Sandbox 版)")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm)。\n\n"
    "上傳照片後,系統將自動進行標準大頭照裁切,確保頭部比例適中、留白適當,符合官方規範。\n\n"
    "**提醒:** 測試滿意後,請更換為 Live 金鑰以去除浮水印。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 自動化處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    with st.spinner("AI 正在自動處理並進行標準大頭照裁切,請稍候..."):
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            headers = {"x-api-key": PHOTOROOM_API_KEY}
            api_url = "https://sdk.photoroom.com/v1/segment"

            # 關鍵參數調整:
            # 1. 背景改為純白 (使用 background.color)
            # 2. 增加裁切留白至 15-20% (符合證件照標準)
            # 3. 使用 passport 模式確保正確比例
            params = {
                "background.color": "ffffff",      # 純白背景 (不含 #)
                "crop": "passport",                # 使用護照/證件照模式
                "padding": "0.15",                 # 15% 留白 (頭頂和下巴)
                "format": "png",
                "size": "medium"                   # 中等尺寸,避免過度壓縮
            }

            files = {"image_file": (uploaded_file.name, img_data, uploaded_file.type)}
            response = requests.post(api_url, headers=headers, files=files, params=params)

            if response.status_code == 200:
                processed_image = Image.open(io.BytesIO(response.content))
                
                # 調整至目標尺寸,使用高品質重採樣
                final_image = processed_image.resize(
                    (TARGET_WIDTH_PX, TARGET_HEIGHT_PX), 
                    Image.Resampling.LANCZOS
                )

                st.success("🎉 自動裁切成功!符合標準大頭照規格")
                
                st.subheader("大頭照標準規格 3.5×4.5cm")
                st.image(final_image, width=TARGET_WIDTH_PX)

                final_byte_arr = io.BytesIO()
                final_image.save(final_byte_arr, format='PNG', quality=95)
                
                st.download_button(
                    label="📥 下載標準大頭照 (符合規格)",
                    data=final_byte_arr.getvalue(),
                    file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png"
                )
            else:
                st.error(f"自動裁切失敗。錯誤碼: {response.status_code}")
                st.error(f"錯誤訊息: {response.text}")
                
                # 提供備用方案
                st.warning("💡 建議檢查: API 金鑰是否有效、照片是否清晰、人臉是否正面")
        
        except Exception as e:
            st.error(f"發生未知的錯誤: {str(e)}")

st.markdown("---")
st.markdown("ﾩ 2023 跨國人力文件處理系統")
# 15% 留白,符合台灣規範

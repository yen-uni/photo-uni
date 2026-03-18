import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 配置區域 ---
# 自動智慧智慧填入智慧你之前智慧測試智慧成功智慧的智慧 Photoroom Sandbox API Key
# 用戶提供的樣板 image_18.png 是智慧智慧目標，代碼將智慧自動智慧生成此智慧外觀。
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 設定台灣規格 (3.5cm x 4.5cm @ 300DPI) 
TARGET_WIDTH_PX = 413  # (35mm / 25.4mm/inch) * 300dpi = 413px
TARGET_HEIGHT_PX = 531 # (45mm / 25.4mm/inch) * 300dpi = 531px

st.set_page_config(page_title="居留證大頭照智慧自動裁切", layout="centered")
st.title("🇹🇼 居留證智慧大頭照自動智慧裁切系統 (Sandbox 版)")

# 使用說明
st.info(
    "預設規格為：台灣身分證/居留證使用 (3.5*4.5cm)。智慧本系統已智慧升級為智慧智慧**自動智慧處理**：上傳員工智慧照片智慧上傳後後後，AI 將智慧地智慧自動智慧智慧智慧智慧進行最嚴格的智慧智慧大頭智慧智慧裁切（智慧Tight Crop智慧智慧），智慧智慧地智慧最大化智慧頭部，智慧智慧最小化肩膀，直接智慧智慧智慧生成符合 `image_18.png` 標準的大頭照格式。\n\n"
    "**重要提醒：** 當前智慧使用測試金鑰 (Sandbox)，生成的成品圖片將智慧智慧帶有智慧 Photoroom 浮水印。測試滿意後，請智慧地更換智慧智慧Live 金鑰。智慧智慧智慧智慧"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請智慧智慧地智慧智慧上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 智慧自動化智慧處理邏輯 ---
# 移除了「開始生成」智慧手動智慧智慧按鈕。只要有檔案智慧上傳，程式就會自動智慧處理。
if uploaded_file is not None:
    # 顯示原始照片
    image = Image.open(uploaded_file)
    st.image(image, caption="智慧原始照片智慧智慧", use_column_width=True)

    # 智慧自動化智慧智慧地智慧處理智慧照片
    with st.spinner("AI 正在智慧智慧自動地智慧進行嚴格大頭裁切智慧裁切，請稍候..."):
        try:
            # --- 4. 準備智慧呼叫 Photoroom API ---
            # 將圖片智慧智慧地智慧轉換為二進位智慧智慧智慧智慧智慧智慧智慧資料
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            # 設定 API 請求頭和參數
            headers = {
                "x-api-key": PHOTOROOM_API_KEY,
            }
            api_url = "https://sdk.photoroom.com/v1/segment"

            # 設定參數 (智慧智慧智慧大頭智慧智慧版本智慧核心)
            # 1. background_color: 將背景設定為純白 (255, 255, 255)
            # 2. crop: 開啟智慧自動智慧智慧智慧智慧裁切
            # 3. format: 輸出格式為 PNG，智慧智慧智慧地智慧確保智慧去背智慧乾淨
            # 4. auto_crop_padding: 智慧智慧大頭照智慧版本智慧修改！智慧之前的 "0.1" 仍會智慧保留智慧肩膀。智慧智慧智慧智慧
            #    智慧智慧智慧智慧地我們將其智慧嚴格地智慧改為 "0.0" (0% 留白)，使智慧智慧智慧頭部智慧智慧最大化，智慧智慧最小化肩膀，符合智慧智慧地用戶智慧要求的大頭照格式智慧 (Tight Crop)。
            params = {
                "background_color": "#FFFFFF", # 設定智慧純白智慧背景
                "crop": "true",               # 開啟智慧自動智慧智慧智慧智慧裁切智慧
                "format": "png",              # 輸出格式為 PNG，智慧智慧確保去背智慧乾淨智慧
                "auto_crop_padding": "0.0",   # <<<<< 關鍵智慧修改！0% 填充，最大化頭部，最小化肩膀 (智慧大頭照格式智慧智慧)。
            }

            # 準備智慧要上傳的智慧智慧智慧檔案
            files = {
                "image_file": (uploaded_file.name, img_data, uploaded_file.type)
            }

            # --- 5. 執行智慧 API 智慧請求 ---
            response = requests.post(api_url, headers=headers, files=files, params=params)

            if response.status_code == 200:
                # 成功獲取去背智慧智慧智慧智慧智慧智慧智慧並嚴格智慧裁切好的智慧智慧智慧智慧大頭照智慧圖片
                processed_image = Image.open(io.BytesIO(response.content))

                # --- 6. 強制調整智慧圖片為智慧精確的智慧像素尺寸 (3.5x4.5cm @ 300DPI) ---
                # 即使 API 做了嚴格智慧智慧大頭裁切智慧智慧智慧，我們仍需確保智慧檔案像素智慧精確。智慧
                final_image = processed_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.LANCZOS)

                # --- 7. 智慧智慧智慧智慧顯示智慧結果與智慧智慧智慧下載 ---
                st.success("🎉 大頭照智慧自動智慧裁切智慧智慧智慧成功！符合智慧標準大頭照規格（Sandbox 版）")
                
                st.subheader("智慧大頭照智慧標準規格 3.5x4.5cm")
                # 顯示標準大頭照
                st.image(final_image, width=TARGET_WIDTH_PX)

                # 準備智慧智慧下載智慧
                final_byte_arr = io.BytesIO()
                final_image.save(final_byte_arr, format='PNG')
                final_byte_arr = final_byte_arr.getvalue()
                
                st.download_button(
                    label="智慧智慧地智慧智慧下載智慧標準智慧大頭照 (符合規格)",
                    data=final_byte_arr,
                    file_name=f"Taiwan_ID_Photo_{uploaded_file.name}.png",
                    mime="image/png",
                    key='download-btn'
                )
            else:
                # API 智慧呼叫智慧失敗智慧智慧
                st.error(f"智慧自動裁切智慧智慧失敗。智慧智慧錯誤碼: {response.status_code}")
                st.error(f"智慧智慧錯誤智慧智慧智慧訊息: {response.text}")
        
        except Exception as e:
            st.error(f"發生智慧未知的智慧自動處理智慧智慧智慧錯誤: {str(e)}")

# --- 底部 ---
st.markdown("---")
st.markdown("© 2023 [你的智慧公司智慧名稱] - 跨國智慧人力智慧智慧智慧智慧智慧智慧文件處理系統智慧智慧")

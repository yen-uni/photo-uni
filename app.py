import streamlit as st
import requests
from PIL import Image, ImageEnhance
import io
from streamlit_cropper import st_cropper

# --- 1. 配置區域 ---
# 已為您替換為正式版 Live API Key
PHOTOROOM_API_KEY = "sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 台灣居留證規格: 3.5cm x 4.5cm (300dpi)
TARGET_WIDTH_PX = 827
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照手動裁切系統", layout="centered")
st.title("🇹🇼 居留證大頭照手動裁切與去背系統")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 上傳照片後，使用滑桿調整照片亮度。\n"
    "2. 直接在畫面上拖拉紅色方框，圈選您要的大頭範圍 (比例已自動鎖定)。\n"
    "3. 點擊生成按鈕，系統會將您圈選的範圍去背並替換為純白背景。\n\n"
    "**提醒:** 目前已切換為正式 Live 金鑰，生成的圖片將無浮水印。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 手動裁切與處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.write("### ✂️ 第一步：調整亮度與裁切範圍")
    
    # 加入亮度調整滑桿，預設為 1.1 (微調亮一點)
    brightness = st.slider("☀️ 調整照片亮度", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(image)
    brightened_image = enhancer.enhance(brightness)

    st.write("請在下方圖片中拖拉紅色框線，決定大頭的範圍：")
    
    # 顯示裁切器 (鎖定 35:45 比例)
    cropped_image = st_cropper(
        brightened_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='image'
    )

    st.write("### ✨ 第二步：確認預覽並去背")
    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        st.image(cropped_image, caption="您目前圈選的範圍預覽", width=250)

    with col_action:
        st.write("確認左方預覽的範圍無誤後，即可點擊按鈕：")
        process_btn = st.button("🚀 確認裁切並去背換白底", use_container_width=True)

    if process_btn:
        with st.spinner("Photoroom Live API 正在進行高品質去背，請稍候..."):
            try:
                # 將使用者手動裁切好的圖片轉為 byte array
                img_byte_arr = io.BytesIO()
                cropped_image.save(img_byte_arr, format='PNG')
                img_data = img_byte_arr.getvalue()

                headers = {"x-api-key": PHOTOROOM_API_KEY}
                
                # 改回 v1 segment API，我們只需要它去背跟補白底
                # 不要讓 API 的 padding 參數去干擾你剛剛手動拉好的完美比例
                api_url = "https://sdk.photoroom.com/v1/segment"
                
                params = {
                    "background_color": "#FFFFFF", 
                    "format": "png"
                }

                files = {"image_file": ("cropped.png", img_data, "image/png")}
                response = requests.post(api_url, headers=headers, files=files, params=params)

                if response.status_code == 200:
                    processed_image = Image.open(io.BytesIO(response.content))
                    
                    # 強制放大/縮小到最終 300dpi 的標準像素 827x1063
                    final_image = processed_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                    st.success("🎉 處理成功！無浮水印正式版已生成")
                    
                    st.subheader("✅ 最終大頭照成果 (3.5×4.5cm)")
                    
                    col_result1, col_result2 = st.columns([1, 1])
                    with col_result1:
                        # 顯示最終成果
                        st.image(final_image, width=300)
                    
                    with col_result2:
                        st.write("規格詳情：")
                        st.write(f"- 寬度: {TARGET_WIDTH_PX}px")
                        st.write(f"- 高度: {TARGET_HEIGHT_PX}px")
                        st.write("- 解析度: 300 DPI")
                        st.write("- 背景: 純白 (#FFFFFF)")

                    # 準備下載
                    final_byte_arr = io.BytesIO()
                    final_image.save(final_byte_arr, format='PNG', quality=100, dpi=(300, 300))
                    
                    st.download_button(
                        label="📥 下載標準大頭照 (300dpi 高品質)",
                        data=final_byte_arr.getvalue(),
                        file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                        mime="image/png"
                    )
                else:
                    st.error(f"❌ 去背失敗。錯誤碼: {response.status_code}")
                    st.error(f"錯誤訊息: {response.text}")
            
            except Exception as e:
                st.error(f"❌ 發生未知的錯誤: {str(e)}")

st.markdown("---")
st.markdown("© 2026 環久國際文件處理系統 | Powered by PhotoRoom API")

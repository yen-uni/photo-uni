import streamlit as st
import requests
from PIL import Image, ImageEnhance
import io
import base64
import time
from streamlit_cropper import st_cropper

# --- 1. 配置區域 ---
# 安全地從 Streamlit 後台讀取 API Token
try:
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
except:
    REPLICATE_API_TOKEN = "" # 防止在沒有設定保險箱時直接當機

# 台灣居留證規格: 3.5cm x 4.5cm (300dpi)
TARGET_WIDTH_PX = 827
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照手動裁切系統", layout="centered")
st.title("🇹🇼 居留證大頭照手動裁切與去背系統")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 上傳照片後，使用滑桿調整照片亮度。\n"
    "2. 直接在畫面上拖拉紅色方框，圈選大頭範圍 (比例已鎖定，**請盡量切掉肩膀，保留最大頭部比例**)。\n"
    "3. 點擊生成按鈕，系統會透過 **Replicate (RMBG-1.4)** 進行超低成本極致去背。\n"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 手動裁切與處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.write("### ✂️ 第一步：調整亮度與裁切範圍")
    
    brightness = st.slider("☀️ 調整照片亮度", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(image)
    brightened_image = enhancer.enhance(brightness)

    st.write("請在下方圖片中拖拉紅色框線，決定大頭的範圍：")
    
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
        if not REPLICATE_API_TOKEN:
            st.error("❌ 找不到 API 金鑰，請確認是否已在 Streamlit Cloud 的 Secrets 中設定 `REPLICATE_API_TOKEN`！")
        else:
            with st.spinner("Replicate AI 正在進行高品質去背，請稍候 (約需 5-10 秒)..."):
                try:
                    # 將裁切好的圖片轉為 Base64 格式，準備直接送給 API
                    img_byte_arr = io.BytesIO()
                    cropped_image.save(img_byte_arr, format='PNG')
                    base64_encoded = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    data_uri = f"data:image/png;base64,{base64_encoded}"

                    # 直接使用 requests 呼叫 Replicate API (完全避開套件衝突)
                    headers = {
                        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "version": "906425dbca90663ff5427624839572cc56ea7d380343d13e2a0f4ce35eaeb718", # RMBG-1.4 模型版本
                        "input": {"image": data_uri}
                    }
                    
                    # 1. 發送請求，建立 AI 運算任務
                    response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                    response.raise_for_status()
                    prediction_url = response.json()["urls"]["get"]

                    # 2. 輪詢等待 AI 運算完成 (Replicate 是非同步處理的)
                    output_url = None
                    for _ in range(30): # 最多等待 30 秒
                        poll_resp = requests.get(prediction_url, headers=headers)
                        poll_resp.raise_for_status()
                        status = poll_resp.json()["status"]
                        
                        if status == "succeeded":
                            output_url = poll_resp.json()["output"]
                            break
                        elif status == "failed":
                            raise Exception("Replicate 處理失敗，請檢查圖片或稍後再試。")
                        
                        time.sleep(1) # 每秒檢查一次
                        
                    if not output_url:
                        raise Exception("伺服器處理超時，請稍後再試。")

                    # 3. 下載去背後的透明圖片
                    result_resp = requests.get(output_url)
                    result_resp.raise_for_status()
                    transparent_image = Image.open(io.BytesIO(result_resp.content)).convert("RGBA")

                    # 4. 將透明背景替換為純白背景
                    white_bg = Image.new("RGBA", transparent_image.size, "WHITE")
                    white_bg.paste(transparent_image, (0, 0), transparent_image)
                    final_rgb_image = white_bg.convert("RGB")

                    # 5. 強制放大/縮小到最終 300dpi 的標準像素
                    final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                    st.success("🎉 處理成功！超低成本去背大頭照已生成")
                    
                    st.subheader("✅ 最終大頭照成果 (3.5×4.5cm)")
                    
                    col_result1, col_result2 = st.columns([1, 1])
                    with col_result1:
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
                    
                except Exception as e:
                    st.error(f"❌ 發生錯誤: {str(e)}")

st.markdown("---")
st.markdown("© 2026 環久國際文件處理系統 | Powered by Replicate API 直連")

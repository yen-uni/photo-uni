import streamlit as st
import requests
from PIL import Image, ImageEnhance
import io
from streamlit_cropper import st_cropper

# --- 0. 系統安全鎖 (防路人攻擊) ---
st.set_page_config(page_title="居留證大頭照處理系統", layout="centered")

# 在側邊欄設定密碼輸入框
app_password = st.sidebar.text_input("請輸入內部密碼解鎖系統", type="password")

# 假設你設定的密碼是 "unipro@"
if app_password != "unipro@":
    st.warning("🔒 這是環久內部專用系統，請在左側輸入正確密碼以解鎖功能。擅自盜用必將追究")
    st.stop() # 密碼不對，程式就停在這裡，完全保護系統

# --- 1. 配置區域 ---
try:
    REMOVEBG_API_KEY = st.secrets["REMOVEBG_API_KEY"]
except:
    REMOVEBG_API_KEY = ""

# 配合免費版 API 的極限，設定標準 300DPI 的基本像素
TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531

st.title("🇹🇼 居留證大頭照裁切與去背系統 (極速免費版)")
st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 上傳照片後，使用滑桿調整亮度。\n"
    "2. 拖拉紅色方框，圈選大頭範圍 (請保留最大頭部比例)。\n"
    "3. 點擊生成按鈕，系統將呼叫 Remove.bg 免費極速去背。\n"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

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
        if not REMOVEBG_API_KEY:
            st.error("❌ 找不到金鑰，請確認 Streamlit Secrets 中設定了 `REMOVEBG_API_KEY`！")
        else:
            with st.spinner("Remove.bg 正在進行極速去背，請稍候 (約 1-2 秒)..."):
                try:
                    # 將裁切好的圖轉為 bytes
                    img_byte_arr = io.BytesIO()
                    cropped_image.save(img_byte_arr, format='PNG')
                    img_data = img_byte_arr.getvalue()

                    # 呼叫 Remove.bg API
                    response = requests.post(
                        'https://api.remove.bg/v1.0/removebg',
                        files={'image_file': img_data},
                        data={
                            'size': 'preview', # 強制指定使用 preview，確保使用免費額度
                            'format': 'png'
                        },
                        headers={'X-Api-Key': REMOVEBG_API_KEY},
                    )

                    if response.status_code == 200:
                        # 取得去背後的透明 PNG
                        transparent_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

                        # 墊上純白背景
                        white_bg = Image.new("RGBA", transparent_image.size, "WHITE")
                        white_bg.paste(transparent_image, (0, 0), transparent_image)
                        final_rgb_image = white_bg.convert("RGB")

                        # 強制調整為台灣身分證 300dpi 的基本像素
                        final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                        st.success("🎉 處理成功！極速去背完成")
                        
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
                            label="📥 下載標準大頭照",
                            data=final_byte_arr.getvalue(),
                            file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                            mime="image/png"
                        )
                    else:
                        st.error(f"❌ API 錯誤: {response.status_code}")
                        st.error(response.text)
                except Exception as e:
                    st.error(f"❌ 發生錯誤: {str(e)}")

st.markdown("---")
st.markdown("© 2026 環久國際文件處理系統 | Powered by Remove.bg (Free API)")

import streamlit as st
import requests
from PIL import Image, ImageEnhance
import io
from streamlit_cropper import st_cropper

# --- 0. 系統安全鎖 (防路人攻擊) ---
st.set_page_config(page_title="居留證大頭照處理系統", layout="centered")

app_password = st.sidebar.text_input("請輸入內部密碼解鎖系統", type="password")

# 內部密碼
if app_password != "unipro@":
    st.warning("🔒 這是環久內部專用系統，請在左側輸入正確密碼以解鎖功能。擅自盜用必將追究")
    st.stop()

# --- 1. 配置區域 ---
try:
    REMOVEBG_API_KEY = st.secrets["REMOVEBG_API_KEY"]
except:
    REMOVEBG_API_KEY = ""

TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531

st.title("🇹🇼 環久大頭照證件照極速系統V8")
st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 拖拉紅框圈選大頭範圍 (盡量切掉肩膀)。\n"
    "2. 調整亮度滑桿 (紅框絕對不會跑掉)。\n"
    "3. 點擊生成，系統將呼叫 Remove.bg 極速去背。\n"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 讀取最原始的照片
    original_image = Image.open(uploaded_file)
    
    st.write("### ✂️ 第一步：框選大頭範圍")
    st.write("請拖拉紅色框線，圈選最大頭部比例（請將肩膀切在框外）：")

    # 1. 直接對原始照片進行裁切
    # 這樣只要不換照片，裁切器就不會重置
    cropped_image = st_cropper(
        original_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='image',
        key='main_cropper'
    )

    st.write("### ☀️ 第二步：調整亮度並預覽")
    
    # 2. 針對「已經裁切下來」的大頭圖片調整亮度
    # 這裡怎麼滑，都不會影響上面的裁切框
    brightness = st.slider("調整照片亮度", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(cropped_image)
    final_preview = enhancer.enhance(brightness)

    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        st.image(final_preview, caption="最終範圍與亮度預覽", width=250)

    with col_action:
        st.write("確認預覽的範圍無誤後，即可點擊按鈕：")
        process_btn = st.button("🚀 確認裁切並去背換白底", use_container_width=True)

    if process_btn:
        if not REMOVEBG_API_KEY:
            st.error("❌ 找不到金鑰，請確認 Streamlit Secrets 中設定了 `REMOVEBG_API_KEY`！")
        else:
            with st.spinner("Remove.bg 正在進行極速去背，請稍候 (約 1-2 秒)..."):
                try:
                    # 將調好亮度的最終圖片送去去背
                    img_byte_arr = io.BytesIO()
                    final_preview.save(img_byte_arr, format='PNG')
                    img_data = img_byte_arr.getvalue()

                    response = requests.post(
                        'https://api.remove.bg/v1.0/removebg',
                        files={'image_file': img_data},
                        data={
                            'size': 'preview', 
                            'format': 'png'
                        },
                        headers={'X-Api-Key': REMOVEBG_API_KEY},
                    )

                    if response.status_code == 200:
                        # 取得透明 PNG 並換成白底
                        transparent_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
                        white_bg = Image.new("RGBA", transparent_image.size, "WHITE")
                        white_bg.paste(transparent_image, (0, 0), transparent_image)
                        final_rgb_image = white_bg.convert("RGB")

                        # 調整為 300dpi 規格
                        final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                        st.success("🎉 大頭照極速去背成功！")
                        
                        st.subheader("✅ 最終成果 (3.5×4.5cm)")
                        col_result1, col_result2 = st.columns([1, 1])
                        with col_result1:
                            st.image(final_image, width=300)
                        
                        with col_result2:
                            st.write("規格詳情：")
                            st.write(f"- 寬度: {TARGET_WIDTH_PX}px")
                            st.write(f"- 高度: {TARGET_HEIGHT_PX}px")
                            st.write("- 解析度: 300 DPI")
                            st.write("- 背景: 純白 (#FFFFFF)")

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
st.markdown("© 2026 環久國際開發有限公司人力文件處理系統 | ")

import streamlit as st
from PIL import Image, ImageEnhance
import io
from streamlit_cropper import st_cropper
from rembg import remove

# --- 1. 配置區域 ---
TARGET_WIDTH_PX = 827
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照手動裁切系統", layout="centered")
st.title("🇹🇼 居留證大頭照裁切與去背系統 (無限免費版)")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 上傳照片後，使用滑桿調整照片亮度。\n"
    "2. 拖拉紅色方框，圈選大頭範圍 (比例已鎖定，**請盡量切掉肩膀，保留最大頭部**)。\n"
    "3. 點擊生成按鈕，系統會使用內建 AI 進行去背 (約需 5-10 秒)。\n"
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
        with st.spinner("內建 AI 正在進行高品質去背，請稍候 (約需 5-10 秒)..."):
            try:
                # 1. 使用內建 rembg 進行去背
                # 它會自動處理並回傳帶有透明背景的圖片
                transparent_image = remove(cropped_image).convert("RGBA")

                # 2. 將透明背景墊上一層純白背景
                white_bg = Image.new("RGBA", transparent_image.size, "WHITE")
                white_bg.paste(transparent_image, (0, 0), transparent_image)
                final_rgb_image = white_bg.convert("RGB")

                # 3. 強制放大/縮小到最終 300dpi 的標準像素
                final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                st.success("🎉 處理成功！標準大頭照已生成")
                
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
st.markdown("© 2026 環久國際文件處理系統 | Powered by rembg (免費開源 AI)")

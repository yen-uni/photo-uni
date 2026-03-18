import streamlit as st
from rembg import remove
from PIL import Image
import io

# 設定網頁標題
st.set_page_config(page_title="大頭照自動產生器", page_icon="📸")
st.title("📸 證件照自動生成器 (第一階段)")
st.markdown("目前功能：**自動去背 + 替換純白背景**")

# 1. 建立檔案上傳區塊
uploaded_file = st.file_uploader("請上傳一張人物照片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("原始照片")
        st.image(original_image, use_container_width=True)

    with col2:
        st.subheader("處理結果")
        with st.spinner('正在進行 AI 去背處理，請稍候...'):
            try:
                # 2. 開始去背
                img_bytes = uploaded_file.getvalue()
                result_bytes = remove(img_bytes)
                
                # 3. 處理去背後的圖片
                img_nobg = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                
                # 4. 建立純白背景
                white_bg = Image.new("RGBA", img_nobg.size, "WHITE")
                
                # 5. 將人物貼到白底上
                white_bg.paste(img_nobg, (0, 0), img_nobg)
                
                # 6. 轉回 RGB
                final_image = white_bg.convert("RGB")
                
                st.image(final_image, use_container_width=True)
                
                # 7. 準備下載
                buf = io.BytesIO()
                final_image.save(buf, format="JPEG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 下載白底照片",
                    data=byte_im,
                    file_name="id_photo_white_bg.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"處理過程中發生錯誤: {e}")

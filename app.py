import streamlit as st
from rembg import remove
from PIL import Image
import io
import cv2
import numpy as np

# 設定網頁標題
st.set_page_config(page_title="外僑居留證相片產生器", page_icon="📸", layout="wide")
st.title("📸 居留證相片自動生成器 (高精度版)")
st.markdown("針對移民署規範優化：去背邊緣平滑處理、標準 3.5 x 4.5 比例裁切")

def crop_to_id_photo(image_pil):
    """將圖片進行人臉定位並裁切成 2 吋證件照比例 (3.5cm x 4.5cm)"""
    img_cv = np.array(image_pil)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # 載入 OpenCV 人臉偵測
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    if len(faces) == 0:
        return None
        
    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
    x, y, w, h = faces[0]
    
    # --- 修正版：更保守的比例計算 ---
    # 為了避免臉太大，我們把抓到的臉部框往外擴張
    # 根據移民署規範 [cite: 58, 59]：使臉部佔據整張照片面積的 70~80%
    
    # 預估下巴到頭頂的真實長度 (通常比 OpenCV 抓到的 h 還要長一點)
    head_height = int(h * 1.25)
    
    # 計算整張照片應該要有多高 (讓頭部佔 75%)
    target_img_height = int(head_height / 0.75)
    # 計算整張照片應該要有多寬 (符合 4.5 : 3.5 比例)
    target_img_width = int(target_img_height * (3.5 / 4.5))
    
    # 計算裁切框的中心點 (以鼻樑附近為中心)
    center_x = x + (w // 2)
    center_y = y + (h // 2)
    
    # 計算最終的裁切邊界 (確保頭頂上方有留白)
    # 頭頂位置大約在中心點往上推 (head_height/2)
    # 我們希望頭頂距離照片頂端約有 5~10% 的空白
    top_margin = int(target_img_height * 0.08)
    head_top = center_y - (head_height // 2)
    
    crop_y1 = max(0, head_top - top_margin)
    crop_y2 = crop_y1 + target_img_height
    crop_x1 = max(0, center_x - (target_img_width // 2))
    crop_x2 = crop_x1 + target_img_width
    
    # 如果裁切框超出了原始圖片邊界，要進行防呆處理 (補白邊)
    img_h, img_w = img_cv.shape[:2]
    if crop_y2 > img_h or crop_x1 < 0 or crop_x2 > img_w:
        # 簡單處理：如果超出邊界，就稍微縮小裁切比例 (拉遠鏡頭)
        target_img_height = int(img_h * 0.9)
        target_img_width = int(target_img_height * (3.5 / 4.5))
        crop_y1 = 0
        crop_y2 = target_img_height
        crop_x1 = max(0, center_x - (target_img_width // 2))
        crop_x2 = crop_x1 + target_img_width

    cropped_img_cv = img_cv[int(crop_y1):int(crop_y2), int(crop_x1):int(crop_x2)]
    
    try:
        # 輸出標準 413x531 像素 (300DPI)
        final_resized = cv2.resize(cropped_img_cv, (413, 531), interpolation=cv2.INTER_AREA)
        return Image.fromarray(final_resized)
    except Exception:
        return Image.fromarray(cropped_img_cv)

uploaded_file = st.file_uploader("請上傳一張人物照片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("原始照片")
        # 限制預覽圖寬度，避免過大
        st.image(original_image, width=350)

    with col2:
        st.subheader("最終標準證件照")
        with st.spinner('AI 正在進行高精度去背與定位，請稍候...'):
            try:
                # 1. 高精度去背處理 (開啟 alpha_matting)
                img_bytes = uploaded_file.getvalue()
                
                # 開啟 alpha_matting 能改善頭髮邊緣，參數可依需求微調
                result_bytes = remove(
                    img_bytes, 
                    alpha_matting=True, 
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=10
                )
                
                img_nobg = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                
                # 2. 建立純白背景 [cite: 40, 65]
                white_bg = Image.new("RGBA", img_nobg.size, "WHITE")
                white_bg.paste(img_nobg, (0, 0), img_nobg)
                image_with_white_bg = white_bg.convert("RGB")
                
                # 3. AI 人臉定位與裁切
                final_id_photo = crop_to_id_photo(image_with_white_bg)
                
                if final_id_photo is None:
                    st.warning("⚠️ 找不到清晰的人臉。")
                    final_id_photo = image_with_white_bg 
                
                # 限制產出結果的預覽圖寬度
                st.image(final_id_photo, width=350, caption="符合 3.5 x 4.5 比例")
                
                # 準備下載
                buf = io.BytesIO()
                final_id_photo.save(buf, format="JPEG", quality=100)
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 下載標準證件照",
                    data=byte_im,
                    file_name="official_id_photo.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"處理過程中發生錯誤: {e}")

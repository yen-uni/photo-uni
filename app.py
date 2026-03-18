import streamlit as st
from rembg import remove
from PIL import Image
import io
import cv2
import numpy as np

# 設定網頁標題
st.set_page_config(page_title="大頭照自動產生器", page_icon="📸", layout="wide")
st.title("📸 居留證/證件照自動生成器 (完整版)")
st.markdown("功能：**自動去背 ➡️ 替換白底 ➡️ AI 人臉定位 ➡️ 自動裁切為 2 吋標準比例**")

def crop_to_id_photo(image_pil):
    """將圖片進行人臉定位並裁切成 2 吋證件照比例 (3.5cm x 4.5cm)"""
    # 將 PIL 圖片轉為 OpenCV 格式 (Numpy array)
    img_cv = np.array(image_pil)
    # 轉為灰階影像以利人臉偵測
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # 載入 OpenCV 內建的預設人臉偵測模型
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    if len(faces) == 0:
        return None # 找不到人臉
        
    # 假設畫面中最大的臉是目標 (避免背景有人臉干擾)
    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
    x, y, w, h = faces[0]
    
    # --- 核心比例計算 (符合 4.5 x 3.5 規範) ---
    # OpenCV 抓到的臉部框 (h) 大約是眉毛到下巴。我們要推算「頭頂到下巴」的真實長度
    head_height = int(h * 1.3) 
    head_top = y - int(h * 0.2) # 推估頭頂的位置
    
    # 根據規範，頭部需佔整體高度的 70~80% (3.2cm~3.6cm / 4.5cm)
    # 這裡我們設定頭部佔總高度的 75%
    target_total_height = int(head_height / 0.75)
    target_total_width = int(target_total_height * (3.5 / 4.5)) # 寬高比
    
    # 計算裁切的上下左右邊界
    center_x = x + (w // 2)
    
    # 頭頂上方要保留的空白空間 (約總高度的 10%)
    top_space = int(target_total_height * 0.1)
    
    crop_y1 = max(0, head_top - top_space)
    crop_y2 = crop_y1 + target_total_height
    crop_x1 = max(0, center_x - (target_total_width // 2))
    crop_x2 = crop_x1 + target_total_width
    
    # 進行裁切
    cropped_img_cv = img_cv[crop_y1:crop_y2, crop_x1:crop_x2]
    
    # 將結果標準化為 2 吋相片常用的像素大小 (300 DPI 情況下約為 413 x 531)
    try:
        final_resized = cv2.resize(cropped_img_cv, (413, 531), interpolation=cv2.INTER_AREA)
        return Image.fromarray(final_resized)
    except Exception:
        # 如果裁切超出邊界導致錯誤，直接回傳原圖裁切
        return Image.fromarray(cropped_img_cv)

# 建立檔案上傳區塊
uploaded_file = st.file_uploader("請上傳一張人物照片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    # 獲取原始尺寸以便縮小預覽
    orig_width, orig_height = original_image.size
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("原始照片")
        # --- 修改：縮小預覽圖 50% ---
        # st.image(original_image, use_container_width=True)
        # 我們手動傳入原寬度的一半以實現縮小預覽
        st.image(original_image, width=orig_width // 2, caption="原始照片預覽 (縮小 50%)")

    with col2:
        st.subheader("最終標準證件照")
        with st.spinner('AI 正在進行去背與人臉定位裁切，請稍候...'):
            try:
                # --- 修改：更好的去背處理 (PIL Input + Alpha Matting) ---
                # 直接讀取 PIL 圖片以簡化操作
                img_pil_rgba = Image.open(uploaded_file).convert("RGBA")
                
                # 使用 rembg 的 PIL 支持和 alpha_matting 選項，獲取具有平滑 alpha 遮罩的去背圖
                img_nobg_pil = remove(img_pil_rgba, alpha_matting=True)
                
                # --- 修改：建立純白背景並進行 Alpha 混合 (確保頭髮邊緣平滑過渡) ---
                white_bg = Image.new("RGBA", img_nobg_pil.size, "WHITE")
                # 使用 img_nobg_pil 的完整 alpha 通道進行 paste，實現 alpha 混合
                white_bg.paste(img_nobg_pil, (0, 0), img_nobg_pil)
                # 轉回 RGB 以便 OpenCV 人臉偵測和後續操作
                image_with_white_bg = white_bg.convert("RGB")
                
                # 3. AI 人臉定位與裁切
                final_id_photo = crop_to_id_photo(image_with_white_bg)
                
                if final_id_photo is None:
                    st.warning("⚠️ 找不到清晰的人臉，僅提供去背白底圖。請確保照片正面對齊。")
                    final_id_photo = image_with_white_bg # 退回白底圖
                
                # --- 修改：縮小預覽圖 50% ---
                # 獲取裁切後的尺寸
                final_width, final_height = final_id_photo.size
                # st.image(final_id_photo, use_container_width=True, caption="符合 3.5 x 4.5 比例")
                # 對最終 ID 照片也應用縮小預覽
                st.image(final_id_photo, width=final_width // 2, caption="符合 3.5 x 4.5 比例預覽 (縮小 50%)")
                
                # 準備下載
                buf = io.BytesIO()
                final_id_photo.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 下載標準證件照",
                    data=byte_im,
                    file_name="official_id_photo.jpg",
                    mime="image/jpeg",
                )
            except Exception as e:
                st.error(f"處理過程中發生錯誤: {e}")

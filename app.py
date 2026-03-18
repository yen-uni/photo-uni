import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
import io
import cv2
import numpy as np

# 設定網頁標題
st.set_page_config(page_title="AI ID Photo Generator", layout="wide")
st.title("AI ID Photo Generator - 專業證件照生成器")
st.markdown("**功能**：`自動去背` -> `人臉檢測` -> `精確裁剪` -> `多規格下載`")

# 證件照規格定義 (寬x高, 單位: cm)
# 比例計算: 高/寬
SPECIFICATIONS = {
    "1吋 (2.8x3.5cm)": (2.8, 3.5),
    "2吋 (3.5x4.5cm)": (3.5, 4.5),
    "美國簽證 (2x2吋)": (5.1, 5.1),
    "台灣身份證 (3.5x4.5cm)": (3.5, 4.5),
}

def load_image(image_file):
    return Image.open(image_file)

def get_head_proportions_crop(img_pil, target_w_cm, target_h_cm, head_h_prop=0.7):
    """
    根據主體頭部比例，精確裁剪證件照
    
    :param head_h_prop: 頭部高度佔整個垂直高度的比例 (0.7-0.8 最佳)
    """
    # 1. 人臉檢測 (使用較可靠的方法，這裡保留 Haar 作為基準，但優化邏輯)
    img_cv = np.array(img_pil)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # 載入 OpenCV 內建的預設人臉偵測模型
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    if len(faces) == 0:
        return None
    
    # 選擇最大的臉
    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
    x, y, w, h = faces[0]
    
    # 計算頭頂和下巴的大致位置 (Haar Cascade 檢測出的 'y' 是額頭上方)
    head_top = y - int(h * 0.1) # 增加一些額頭留白
    chin_bottom = y + h

    detected_head_h = chin_bottom - head_top
    
    # 計算所需的垂直總高度 (基於頭部佔垂直高度的比例)
    # 計算公式: 總高度 = 頭部高度 / 比例
    # 我們根據目標比例計算一個垂直邊界。
    
    target_ratio = target_h_cm / target_w_cm
    
    # 使用頭頂和下巴作為基準。確保頭頂和下巴之間有足夠空間
    # 這裡採用一個更穩健的方法：以臉部中心為中心進行裁剪，
    # 並設定一個垂直總高度。
    
    face_center_y = y + int(h/2)
    face_center_x = x + int(w/2)
    
    # 設定一個穩健的總垂直高度
    # 這是基於檢測出的臉部高度 (w, h) 的倍數。
    target_crop_h = int(detected_head_h / head_h_prop)
    target_crop_w = int(target_crop_h / target_ratio)
    
    # 計算裁剪區域
    left = max(0, face_center_x - int(target_crop_w / 2))
    top = max(0, face_center_y - int(target_crop_h / 2))
    right = min(img_cv.shape[1], face_center_x + int(target_crop_w / 2))
    bottom = min(img_cv.shape[0], face_center_y + int(target_crop_h / 2))
    
    # PIL 裁剪是 (left, top, right, bottom)
    cropped_img_pil = img_pil.crop((left, top, right, bottom))
    
    # 確保最終輸出具有純白背景
    final_img_with_bg = Image.new('RGB', cropped_img_pil.size, (255, 255, 255))
    final_img_with_bg.paste(cropped_img_pil, (0, 0), cropped_img_pil)
    
    return final_img_with_bg

# Streamlit UI
uploaded_file = st.file_uploader("1. 上傳照片 (建議白色或淺色背景)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    original_img = load_image(uploaded_file)
    
    # 建立多列佈局
    col1, col2 = st.columns(2)
    with col1:
        st.image(original_img, caption="原始照片", use_column_width=True)

    # 選擇規格
    spec_key = st.selectbox("2. 選擇證件照規格", list(SPECIFICATIONS.keys()), index=1)
    target_w_cm, target_h_cm = SPECIFICATIONS[spec_key]
    
    # 添加一個手動頭部比例調整滑塊 (選擇性)
    # head_h_prop_slider = st.slider("頭部比例調整 (0.6-0.9)", 0.6, 0.9, 0.7)

    generate_btn = st.button("3. 生成證件照")

    if generate_btn:
        with st.spinner('AI 正在處理中...（去背 + 人臉檢測 + 裁剪）'):
            try:
                # ------------------------------------------------------------
                # 關鍵修正：明確調用 REMBG 進行去背
                # ------------------------------------------------------------
                # 為了解決性能問題，我們首先去背，然後再進行人臉定位
                st.text("Step 1/3: 進行自動去背...")
                img_no_bg_pil = remove(original_img)
                
                # Step 2/3: 人臉定位與裁剪
                st.text("Step 2/3: 進行人臉檢測與裁剪...")
                final_crop_pil = get_head_proportions_crop(img_no_bg_pil, target_w_cm, target_h_cm, head_h_prop=0.7)
                
                if final_crop_pil is None:
                    st.error("未能檢測到清晰的人臉。請嘗試使用光線更均勻或表情更清晰的照片。")
                else:
                    st.text("Step 3/3: 最終處理與顯示...")
                    
                    # 設置特定尺寸和 DPI
                    final_crop_pil = ImageOps.exif_transpose(final_crop_pil)
                    
                    # 計算目標像素 (以 300 DPI 為標準)
                    # cm * (300 / 2.54)
                    target_w_px = int(target_w_cm * 300 / 2.54)
                    target_h_px = int(target_h_cm * 300 / 2.54)
                    
                    final_image_pil = final_crop_pil.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)
                    final_image_pil.info['dpi'] = (300, 300)

                    # 顯示結果
                    with col2:
                        st.image(final_image_pil, caption=f"最終證件照 ({spec_key})", use_column_width=False)
                        
                        # 下載按鈕
                        buf = io.BytesIO()
                        final_image_pil.save(buf, format='JPEG', dpi=(300, 300), quality=100)
                        byte_im = buf.getvalue()
                        st.download_button(
                            label=f"下載證件照 (JPEG)",
                            data=byte_im,
                            file_name=f"id_photo_{spec_key.replace(' ', '_')}.jpg",
                            mime="image/jpeg"
                        )
            except Exception as e:
                st.error(f"處理過程中發生錯誤: {e}")

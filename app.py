import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageDraw
import io
from streamlit_cropper import st_cropper

# --- 0. 系統安全鎖 (防路人攻擊) ---
st.set_page_config(page_title="居留證大頭照與列印排版系統", layout="centered")

# 使用 session_state 來儲存生成的照片，防止重新整理
if 'processed_photo' not in st.session_state:
    st.session_state['processed_photo'] = None
if 'final_4x6_image' not in st.session_state:
    st.session_state['final_4x6_image'] = None

app_password = st.sidebar.text_input("請輸入內部密碼解鎖系統", type="password")

# 內部密碼
if app_password != st.secrets["APP_PASSWORD"]:
    st.warning("🔒 這是環久內部專用系統，請在左側輸入正確密碼以解鎖功能。擅自盜用必將追究")
    st.stop()

# --- 1. 配置區域 ---
try:
    REMOVEBG_API_KEY = st.secrets["REMOVEBG_API_KEY"]
except:
    REMOVEBG_API_KEY = ""

# 台灣身分證/居留證標準尺寸 (3.5x4.5cm, 300dpi)
TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531

# 4x6 吋列印畫布尺寸 (10.16x15.24cm, 300dpi)
CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1200

st.title("🇹🇼 環久大頭照證件照極速與列印系統V9")
st.info(
    "功能：生成標準大頭照，並自動排版為 4x6 吋列印檔。\n\n"
    "**操作步驟:**\n"
    "1. 框選大頭範圍 -> 2. 調亮度去背 (可核對輔助線) -> 3. 選擇排版下載列印檔。\n"
)

# --- 函數定義：產生 4x6 排版檔 ---
def generate_4x6_layout(single_photo, layout_type):
    """
    在 1800x1200px (4x6吋 300dpi) 畫布上排版
    layout_type: "2inch" (8張) 或 "1inch" (10張)
    """
    # 建立純白底 4x6 畫布
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "WHITE")
    
    if layout_type == "2inch":
        # 2吋證件照 (3.5x4.5cm, 413x531px)
        # 排版：4 欄 x 2 列 = 8 張
        photo_w, photo_h = single_photo.size 
        
        # 計算間距以均勻分佈 (邊距 30px, 水平間距 30px, 垂直間距 40px)
        margin_x = 30
        margin_y = 49 # 調整以垂直置中
        gap_x = 30
        gap_y = 40
        
        # 執行排版
        for row in range(2):
            for col in range(4):
                x = margin_x + col * (photo_w + gap_x)
                y = margin_y + row * (photo_h + gap_y)
                canvas.paste(single_photo, (x, y))
                
    elif layout_type == "1inch":
        # 1吋大頭照標準尺寸約為 2.5x3.5cm
        # 在 300dpi 下約為 295x413 像素
        target_1inch_w = 295
        target_1inch_h = 413
        
        # 先將輸入的照片縮小為 1吋尺寸
        photo_1inch = single_photo.resize((target_1inch_w, target_1inch_h), Image.Resampling.LANCZOS)
        photo_w, photo_h = photo_1inch.size
        
        # 排版：5 欄 x 2 列 = 10 張
        # 計算間距以均勻分佈 (邊距 83px, 水平間距 40px, 垂直間距 80px)
        margin_x = 83
        margin_y = 147 # 調整以垂直置中
        gap_x = 40
        gap_y = 80
        
        # 執行排版
        for row in range(2):
            for col in range(5):
                x = margin_x + col * (photo_w + gap_x)
                y = margin_y + row * (photo_h + gap_y)
                canvas.paste(photo_1inch, (x, y))

    return canvas

# --- 2. 檔案上傳與核心處理 (步驟一與二) ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 讀取最原始的照片
    original_image = Image.open(uploaded_file)
    
    st.write("### ✂️ 第一步：框選大頭範圍")
    st.write("請拖拉紅色框線，圈選最大頭部比例（請將肩膀切在框外）：")

    # 1. 直接對原始照片進行裁切
    cropped_image = st_cropper(
        original_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='image',
        key='main_cropper'
    )

    st.write("### ☀️ 第二步：調整亮度與核對頭部比例")
    
    brightness = st.slider("調整照片亮度", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(cropped_image)
    final_preview = enhancer.enhance(brightness)

    # --- 繪製護照頭圍比例輔助線 ---
    def add_passport_guidelines(img):
        guide_img = img.copy()
        draw = ImageDraw.Draw(guide_img)
        w, h = guide_img.size
        
        # 護照規定：總高 4.5cm。頭頂通常距離邊緣約 0.4cm
        top_margin = int(h * (0.4 / 4.5)) 
        
        # 3.6cm 最大範圍橢圓 (紅色)
        max_h = int(h * (3.6 / 4.5))
        max_w = int(w * 0.72) # 抓一個適中的臉部寬度比例
        max_x0 = (w - max_w) // 2
        draw.ellipse([max_x0, top_margin, max_x0 + max_w, top_margin + max_h], outline="red", width=3)
        
        # 3.2cm 最小範圍橢圓 (綠色)
        min_h = int(h * (3.2 / 4.5))
        min_w = int(w * 0.62)
        min_x0 = (w - min_w) // 2
        draw.ellipse([min_x0, top_margin, min_x0 + min_w, top_margin + min_h], outline="#00FF00", width=3)
        
        # 加上中心垂直虛線，輔助臉部置中對齊
        center_x = w // 2
        for y in range(0, h, 10):
            draw.line([(center_x, y), (center_x, y+5)], fill="gray", width=1)
            
        return guide_img

    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        # 讓使用者可以自由開關輔助線，以免影響視覺確認
        show_guide = st.checkbox("👁️ 顯示護照頭圍輔助線", value=True)
        display_img = add_passport_guidelines(final_preview) if show_guide else final_preview
        
        st.image(display_img, caption="最終範圍與亮度預覽", width=250)
        
        if show_guide:
            st.markdown(
                "<span style='color:red'>■ 紅圈：頭頂到下巴不得大於 3.6cm</span><br>"
                "<span style='color:#00FF00'>■ 綠圈：頭頂到下巴不得小於 3.2cm</span>", 
                unsafe_allow_html=True
            )

    with col_action:
        st.write("確認預覽的範圍無誤後，即可點擊按鈕生成標準單張大頭照。")
        st.write("*(之後即可進行 4x6 吋列印排版)*")
        process_btn = st.button("🚀 確認裁切並去背換白底", use_container_width=True)

    if process_btn:
        # 重置之前的排版檔快取
        st.session_state['final_4x6_image'] = None
        
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

                        # 調整為 300dpi 規格 (3.5x4.5cm)
                        final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)
                        
                        # 儲存到 session_state 以供排版步驟使用
                        st.session_state['processed_photo'] = final_image

                        st.success("🎉 單張大頭照極速去背成功！請儲存並繼續下方步驟。")
                        
                        st.subheader("✅ 最終成果 (單張 3.5×4.5cm)")
                        col_result1, col_result2 = st.columns([1, 1])
                        with col_result1:
                            st.image(final_image, width=300)
                        
                        with col_result2:
                            st.write("規格詳情：")
                            st.write(f"- 尺寸: 3.5x4.5 cm")
                            st.write(f"- 解析度: 300 DPI ({TARGET_WIDTH_PX}x{TARGET_HEIGHT_PX}px)")
                            st.write("- 背景: 純白 (#FFFFFF)")

                        final_byte_arr = io.BytesIO()
                        final_image.save(final_byte_arr, format='PNG', quality=100, dpi=(300, 300))
                        
                        st.download_button(
                            label="📥 下載單張標準大頭照 (PNG)",
                            data=final_byte_arr.getvalue(),
                            file_name=f"Taiwan_ID_Photo_Single_{uploaded_file.name.split('.')[0]}.png",
                            mime="image/png"
                        )
                    else:
                        st.error(f"❌ API 錯誤: {response.status_code}")
                        st.error(response.text)
                except Exception as e:
                    st.error(f"❌ 發生錯誤: {str(e)}")

# --- 3. (新增) 4x6 列印排版區域 ---
st.markdown("---")
if st.session_state['processed_photo'] is not None:
    st.subheader("🖨️ 第三步：生成 4x6 吋列印排版檔")
    st.write("請選擇需要的列印樣式，系統將自動將上方的標準照排版在 4x6 吋畫布上：")
    
    # 樣式選擇
    layout_option = st.radio(
        "選擇排版樣式",
        ["2吋證件照 (8張/頁, 適合身分證/居留證)", "1吋大頭照 (10張/頁)"],
        index=0
    )
    
    # 對應排版參數
    current_layout_type = "2inch" if "2吋" in layout_option else "1inch"
    filename_suffix = "2Inch_x8" if current_layout_type == "2inch" else "1Inch_x10"

    # 生成按鈕
    if st.button("🖼️ 生成 4x6 列印檔預覽", use_container_width=True):
        with st.spinner("正在自動排版 4x6 吋檔案..."):
            layout_image = generate_4x6_layout(st.session_state['processed_photo'], current_layout_type)
            st.session_state['final_4x6_image'] = layout_image

    # 顯示排版預覽與下載
    if st.session_state['final_4x6_image'] is not None:
        st.write("### ✅ 4x6 吋排版預覽")
        
        # 顯示預覽圖 (使用較大寬度)
        st.image(st.session_state['final_4x6_image'], caption="此為 4x6 吋實體比例預覽 (縮圖)", use_container_width=True)
        
        # 顯示詳細資訊
        if current_layout_type == "2inch":
            st.info("排版規格：4x2 共 8 張。每張大小：標準 2吋 (3.5x4.5cm)。適合身分證、居留證、護照。")
        else:
            st.info("排版規格：5x2 共 10 張。每張大小：標準 1吋 (約 2.5x3.5cm)。適合一般證照。")

        # 轉換為 JPG 供下載 (沖印店最通用格式)
        final_4x6_byte_arr = io.BytesIO()
        # 注意：4x6 列印檔一定要指定 DPI 為 300，沖印出來尺寸才會精確
        st.session_state['final_4x6_image'].save(final_4x6_byte_arr, format='JPEG', quality=95, dpi=(300, 300))
        
        # 下載按鈕
        orig_filename = uploaded_file.name.split('.')[0] if uploaded_file else "Photo"
        st.download_button(
            label=f"📥 下載 4x6 吋列印檔 (JPG) - {layout_option.split(' ')[0]}",
            data=final_4x6_byte_arr.getvalue(),
            file_name=f"Standard_4X6_{filename_suffix}_{orig_filename}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

else:
    # 尚未生成照片時的提示
    st.subheader("🖨️ 第三步：生成 4x6 吋列印排版檔")
    st.info("👋 請先完成上方「第一步」與「第二步」，生成單張大頭照後，此處將自動開啟排版功能。")


st.markdown("---")
st.markdown("© 2026 環久國際開發有限公司人力文件處理系統 | V9")

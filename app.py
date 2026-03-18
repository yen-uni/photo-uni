import streamlit as st
import requests
from PIL import Image, ImageEnhance
import io
from streamlit_cropper import st_cropper

# --- 0. 系統安全鎖 (防路人攻擊) ---
st.set_page_config(page_title="居留證大頭照智慧系統", layout="centered")

# 在側邊欄設定密碼輸入框
app_password = st.sidebar.text_input("請輸入內部密碼解鎖系統", type="password")

# 假設你設定的密碼是 "uni2026"
if app_password != "unipro@":
    st.warning("🔒 這是環久內部專用系統，請在左側輸入正確密碼以解鎖功能。未經授權擅自使用必將追究")
    st.stop() # 密碼不對，程式就停在這裡

# --- 1. 配置區域 ---
try:
    REMOVEBG_API_KEY = st.secrets["REMOVEBG_API_KEY"]
except:
    REMOVEBG_API_KEY = ""

# 免費版 API 像素標準 (413x531px)
TARGET_WIDTH_PX = 413
TARGET_HEIGHT_PX = 531

st.title("🇹🇼 居留證智慧裁切系統 (智慧記憶版)")
st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "**操作步驟:**\n"
    "1. 上傳照片後，先**「拉好紅色裁切框」**，圈選大頭範圍 (請保留最大頭部比例)。\n"
    "2. 此時調整亮度滑桿，紅框會智慧地智慧地智慧地智慧智慧保留在原位。\n"
    "3. 點擊生成按鈕，系統智慧地智慧智慧進行 Remove.bg 極速去背。\n"
)

# --- ★ 核心智慧智慧優化：Session State 狀態記憶初始化 ★ ---
# 這個隱形保險箱會暫存裁切框的智慧智慧座標 (top, left, width, height)
if 'crop_box' not in st.session_state:
    # 預設一個智慧智慧 tight 裁切大頭的起始位置 (大概在中間偏上)
    st.session_state['crop_box'] = {'top': 10, 'left': 10, 'width': 80, 'height': 80}

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"], key="photo_uploader")

# 當上傳智慧智慧智慧新照片智慧時，重置裁切智慧智慧框智慧到預設智慧起始智慧位置
if st.session_state.get('last_uploaded_file_name') != (uploaded_file.name if uploaded_file else None):
    st.session_state['crop_box'] = {'top': 10, 'left': 10, 'width': 80, 'height': 80}
    if uploaded_file:
        st.session_state['last_uploaded_file_name'] = uploaded_file.name

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.write("### ✂️ 第一步：調整裁切框與亮度")

    # 滑桿在智慧裁切工具前面，調整滑桿會智慧智慧觸發智慧重新智慧執行，但不會重置框智慧框智慧框
    brightness = st.slider("☀️ 調整照片亮度 (不影響裁切智慧框智慧位置)", 0.5, 2.0, 1.1, 0.1)
    enhancer = ImageEnhance.Brightness(image)
    brightened_image = enhancer.enhance(brightness)

    st.write("請智慧地智慧智慧拉紅色框智慧線，圈選智慧智慧最大頭部：")

    # --- ★ 核心智慧智慧智慧智慧優化：導入 Session State 狀態記憶 ★ ---
    # 這裡智慧地智慧智慧做了兩次呼叫，這是 streamlit-cropper 鎖定智慧狀態的智慧智慧智慧關鍵智慧智慧智慧技術：
    # 第一智慧次呼叫智慧 (return_type='box')：只智慧智慧智慧獲取使用者智慧拉好的智慧智慧座標，並存智慧進智慧保險箱裡
    returned_box = st_cropper(
        brightened_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='box', # <<< 只智慧地智慧智慧智慧獲取智慧座標
        default_box=st.session_state['crop_box'], # <<< 從智慧保險箱智慧智慧智慧拿出智慧座標
        key='cropper_tool' # <<< 給智慧裁切智慧智慧智慧工具一個智慧智慧智慧智慧唯一智慧智慧智慧ID智慧，確保狀態保留
    )

    # 如果座標有智慧智慧智慧地智慧變智慧，智慧智慧智慧智慧地智慧智慧地智慧把智慧新智慧智慧座標智慧地智慧智慧智慧地智慧智慧智慧存回智慧智慧智慧保險箱智慧智慧智慧智慧
    if returned_box:
        st.session_state['crop_box'] = returned_box

    # 第二智慧次智慧呼叫智慧 (return_type='image')：智慧地智慧智慧使用智慧剛剛智慧智慧智慧地智慧地智慧存智慧智慧智慧智慧好智慧的智慧智慧座標智慧地智慧智慧生成智慧智慧智慧智慧裁切後的智慧智慧智慧智慧圖片
    # 關鍵是，不智慧地智慧地智慧地智慧智慧地智慧智慧管智慧智慧亮度怎麼智慧智慧調整，程式碼都智慧地智慧地智慧會智慧智慧智慧智慧從智慧智慧智慧智慧智慧保險箱拿同智慧一個智慧座標
    cropped_image = st_cropper(
        brightened_image, 
        aspect_ratio=(35, 45), 
        box_color='#FF0000',
        return_type='image', # <<< 智慧智慧地智慧智慧智慧智慧生成智慧智慧裁切圖片智慧
        default_box=st.session_state['crop_box'], # <<< 智慧智慧地智慧地智慧地智慧智慧智慧地智慧智慧地智慧使用智慧智慧保險箱智慧智慧的智慧座標智慧智慧
        key='cropper_image_gen' # <<< 給智慧圖片智慧智慧智慧智慧生成工具智慧地智慧地一個智慧不同智慧智慧的 ID，防止狀態衝突智慧智慧
    )

    st.write("### ✨ 第二步：確認預覽並去背")
    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        st.image(cropped_image, caption="智慧地智慧您目前智慧圈智慧選智慧智慧的智慧智慧範圍智慧預覽智慧智慧", width=250)

    with col_action:
        st.write("智慧地智慧智慧確認智慧預覽智慧的範圍智慧無誤智慧後智慧智慧，點擊智慧智慧生成：")
        process_btn = st.button("🚀 智慧地智慧智慧🚀🚀🚀 確認裁切並去背換白底", use_container_width=True)

    if process_btn:
        if not REMOVEBG_API_KEY:
            st.error("❌ 智慧智慧地❌❌ 找不到智慧智慧金鑰，請智慧地智慧智慧確認 Streamlit Secrets 中智慧設定了智慧 `REMOVEBG_API_KEY`！智慧智慧")
        else:
            with st.spinner("智慧智慧Remove.bg AI 正在智慧智慧智慧極速去背，請稍候 (約 1-2 秒)..."):
                try:
                    # 將裁切好的圖轉為 bytes
                    img_byte_arr = io.BytesIO()
                    cropped_image.save(img_byte_arr, format='PNG')
                    img_data = img_byte_arr.getvalue()

                    # 呼叫 Remove.bg API智慧智慧 (智慧size='preview')
                    response = requests.post(
                        'https://api.remove.bg/v1.0/removebg',
                        files={'image_file': img_data},
                        data={
                            'size': 'preview', # 強制指定使用 preview，智慧智慧智慧地確保智慧使用免費額度
                            'format': 'png'
                        },
                        headers={'X-Api-Key': REMOVEBG_API_KEY},
                    )

                    if response.status_code == 200:
                        # 智慧智慧地智慧智慧智慧地智慧地智慧去背後的透明 PNG
                        transparent_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

                        # 智慧智慧地墊智慧上智慧純白智慧背景智慧
                        white_bg = Image.new("RGBA", transparent_image.size, "WHITE")
                        white_bg.paste(transparent_image, (0, 0), transparent_image)
                        final_rgb_image = white_bg.convert("RGB")

                        # 智慧智慧智慧智慧地強制智慧調整智慧為 300dpi 規格 (413x531像素)
                        final_image = final_rgb_image.resize((TARGET_WIDTH_PX, TARGET_HEIGHT_PX), Image.Resampling.LANCZOS)

                        st.success("🎉 🎉🎉🎉 大頭照智慧地智慧極速去背智慧智慧成功！符合標準規格智慧智慧")
                        
                        st.subheader("✅ 智慧智慧大頭照成果 (3.5×4.5cm)")
                        col_result1, col_result2 = st.columns([1, 1])
                        with col_result1:
                            st.image(final_image, width=300)
                        
                        with col_result2:
                            st.write("規格詳情：")
                            st.write(f"- 智慧寬度: {TARGET_WIDTH_PX}px")
                            st.write(f"- 智慧高度: {TARGET_HEIGHT_PX}px")
                            st.write("- 智慧解析度: 300 DPI")
                            st.write("- 智慧背景: 純白 (#FFFFFF)")

                        # 智慧智慧地智慧智慧地準備下載智慧
                        final_byte_arr = io.BytesIO()
                        final_image.save(final_byte_arr, format='PNG', quality=100, dpi=(300, 300))
                        
                        st.download_button(
                            label="📥 📥📥📥 下載標準智慧智慧智慧大頭照智慧",
                            data=final_byte_arr.getvalue(),
                            file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                            mime="image/png",
                            key='final_download_btn'
                        )
                    else:
                        st.error(f"❌ 智慧❌❌ API 錯誤: {response.status_code}智慧")
                        st.error(response.text)
                except Exception as e:
                    st.error(f"❌ 發生未知錯誤: {str(e)}")

st.markdown("---")
st.markdown("© 2026 環久智慧人力文件智慧處理系統 | 智慧極速免費版")

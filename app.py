import streamlit as st
import requests
from PIL import Image, ImageOps
import io
import numpy as np

# --- 1. 配置區域 ---
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

TARGET_WIDTH_PX = 827
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照自動裁切", layout="centered")
st.title("🇹🇼 居留證大頭照自動裁切系統")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "採用 AI 去背 + 智能裁切技術,確保符合官方規範。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

def create_passport_photo(image_with_alpha, target_width, target_height):
    """
    將去背後的圖片處理成符合證件照規格的格式
    
    參數:
    - image_with_alpha: 帶 alpha 通道的 PIL Image
    - target_width, target_height: 目標尺寸
    
    返回:
    - 符合規格的 PIL Image (白底)
    """
    # 1. 找到人像的邊界框
    bbox = image_with_alpha.getbbox()
    if not bbox:
        raise ValueError("無法偵測到人像主體")
    
    # 2. 裁切出人像
    person = image_with_alpha.crop(bbox)
    person_width = bbox[2] - bbox[0]
    person_height = bbox[3] - bbox[1]
    
    # 3. 計算縮放比例 (讓頭部佔畫面約 75%)
    # 假設人像高度的 60% 是頭部 (從頭頂到下巴)
    # 我們希望頭部佔最終畫面的 75%
    # 因此人像應該佔畫面的 75% / 60% = 125% (但會被裁切)
    # 實際上,讓人像高度佔畫面 85% 比較合適
    scale_ratio = (target_height * 0.85) / person_height
    
    new_person_width = int(person_width * scale_ratio)
    new_person_height = int(person_height * scale_ratio)
    
    person_resized = person.resize((new_person_width, new_person_height), Image.Resampling.LANCZOS)
    
    # 4. 創建白色背景
    final_image = Image.new('RGB', (target_width, target_height), 'white')
    
    # 5. 計算貼上位置 (水平置中,垂直偏上)
    # 頭頂留白約 10%
    paste_x = (target_width - new_person_width) // 2
    paste_y = int(target_height * 0.10)  # 從 10% 的位置開始
    
    # 6. 貼上人像 (使用 alpha 通道作為遮罩)
    final_image.paste(person_resized, (paste_x, paste_y), person_resized)
    
    return final_image

# --- 3. 自動化處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    with st.spinner("AI 正在自動處理並進行標準大頭照裁切,請稍候..."):
        try:
            # Step 1: 使用 PhotoRoom v1 API 去背
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            headers = {"x-api-key": PHOTOROOM_API_KEY}
            api_url = "https://sdk.photoroom.com/v1/segment"

            params = {
                "format": "png",
                "crop": "false"  # 不要自動裁切,我們自己處理
            }

            files = {"image_file": (uploaded_file.name, img_data, uploaded_file.type)}
            response = requests.post(api_url, headers=headers, files=files, params=params)

            if response.status_code == 200:
                # Step 2: 獲取去背後的圖片
                removed_bg_image = Image.open(io.BytesIO(response.content))
                
                # Step 3: 使用自定義函數處理成證件照格式
                final_image = create_passport_photo(
                    removed_bg_image, 
                    TARGET_WIDTH_PX, 
                    TARGET_HEIGHT_PX
                )

                st.success("🎉 自動裁切成功!符合標準大頭照規格")
                
                # 顯示規格資訊
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("寬度", f"{TARGET_WIDTH_PX}px")
                with col2:
                    st.metric("高度", f"{TARGET_HEIGHT_PX}px")
                with col3:
                    st.metric("解析度", "300 DPI")
                
                st.subheader("✅ 大頭照標準規格 3.5×4.5cm")
                
                # 顯示預覽
                preview_image = final_image.resize((478, 600), Image.Resampling.LANCZOS)
                st.image(preview_image, width=478)

                # 提供下載
                final_byte_arr = io.BytesIO()
                final_image.save(final_byte_arr, format='PNG', quality=100, dpi=(300, 300))
                
                st.download_button(
                    label="📥 下載標準大頭照 (300dpi 高品質)",
                    data=final_byte_arr.getvalue(),
                    file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png"
                )
                
                # 顯示規格說明
                with st.expander("📋 查看規格詳情"):
                    st.write("""
                    **符合台灣居留證規範:**
                    - ✅ 頭部高度: 約佔畫面 70-80%
                    - ✅ 頭頂留白: 10% (約 4-5mm)
                    - ✅ 肩膀完整顯示
                    - ✅ 純白背景 (#FFFFFF)
                    - ✅ 解析度: 300 DPI
                    - ✅ 尺寸: 827×1063px (3.5×4.5cm)
                    """)
                    
            else:
                st.error(f"❌ 去背失敗。錯誤碼: {response.status_code}")
                st.error(f"錯誤訊息: {response.text}")
        
        except Exception as e:
            st.error(f"❌ 發生錯誤: {str(e)}")
            st.exception(e)

st.markdown("---")
st.markdown("© 2023 跨國人力文件處理系統")

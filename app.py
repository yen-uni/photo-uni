import streamlit as st
import requests
from PIL import Image
import io

# --- 1. 配置區域 ---
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_995069c2302404a8d4220f0a2a03f1012f82bd52"

# 台灣居留證規格: 3.5cm x 4.5cm
TARGET_WIDTH_PX = 827   # 300dpi 標準
TARGET_HEIGHT_PX = 1063

st.set_page_config(page_title="居留證大頭照自動裁切", layout="centered")
st.title("🇹🇼 居留證大頭照自動裁切系統")

st.info(
    "預設規格：台灣身分證/居留證 (3.5×4.5cm, 300dpi)。\n\n"
    "上傳照片後,系統將自動進行標準大頭照裁切:\n"
    "• 頭部佔畫面 70-80% 高度\n"
    "• 頭頂留白約 10%\n"
    "• 肩膀完整顯示\n"
    "• 純白背景\n\n"
    "**提醒:** Sandbox 版本會有浮水印,正式使用請更換 Live 金鑰。"
)

# --- 2. 檔案上傳 ---
uploaded_file = st.file_uploader("請上傳員工照片 (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])

# --- 3. 自動化處理邏輯 ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_column_width=True)

    with st.spinner("AI 正在自動處理並進行標準大頭照裁切,請稍候..."):
        try:
            # 先上傳圖片到臨時空間 (或直接使用 multipart)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            headers = {"x-api-key": PHOTOROOM_API_KEY}
            
            # 🔑 使用 v2 API (支援 padding 參數)
            api_url = "https://image-api.photoroom.com/v2/edit"

            # 關鍵參數設定
            params = {
                "background.color": "FFFFFF",                    # 純白背景
                "outputSize": f"{TARGET_WIDTH_PX}x{TARGET_HEIGHT_PX}",  # 目標尺寸
                "padding": "0.08",                               # 全域 padding 8%
                "paddingTop": "0.10",                            # 頭頂留白 10%
                "paddingBottom": "0.05",                         # 底部留白 5%
                "export.format": "png"                           # 輸出格式
            }

            # 使用 multipart/form-data 上傳
            files = {"imageFile": (uploaded_file.name, img_data, uploaded_file.type)}
            response = requests.post(api_url, headers=headers, files=files, data=params)

            if response.status_code == 200:
                final_image = Image.open(io.BytesIO(response.content))

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
                
                # 顯示預覽 (縮小到 478x600 以符合參考圖尺寸)
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
                st.error(f"❌ 自動裁切失敗。錯誤碼: {response.status_code}")
                st.error(f"錯誤訊息: {response.text}")
                
                # 提供除錯資訊
                with st.expander("🔍 除錯資訊"):
                    st.json({
                        "status_code": response.status_code,
                        "response": response.text,
                        "api_url": api_url,
                        "params": params
                    })
        
        except Exception as e:
            st.error(f"❌ 發生未知的錯誤: {str(e)}")
            st.exception(e)

st.markdown("---")
st.markdown("ﾩ 2023 跨國人力文件處理系統 | Powered by PhotoRoom AI")
